from gym_trading_env.downloader import download
import datetime
from datetime import timezone, UTC
import pandas as pd
import numpy as np
from bellman_ford_arbitrage import BellmanFordArbitrage
from typing import List, Dict, Tuple
from gym_trading_env.environments import TradingEnv
import time
import asyncio
import ccxt.async_support as ccxt
import os
import nest_asyncio
import warnings

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Suppress DeprecationWarning for utcfromtimestamp
warnings.filterwarnings('ignore', category=DeprecationWarning, 
                       message='datetime.datetime.utcfromtimestamp.*')

class CryptoArbitrageTrader:
    def __init__(self, symbols: List[str], timeframe: str = "1h", 
                 since: datetime.datetime = datetime.datetime(2020, 1, 1, tzinfo=UTC),
                 trading_fee: float = 0.001):  # 0.1% trading fee by default
        self.symbols = symbols
        self.timeframe = timeframe
        self.since = since
        self.trading_fee = trading_fee
        self.bf_arbitrage = BellmanFordArbitrage(trading_fee=trading_fee)
        self.data = {}
        self.current_rates = {}
        self.exchange = None
        
    async def initialize_exchange(self):
        """Initialize exchange connection"""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        await self.exchange.load_markets()
        
    async def close_exchange(self):
        """Close exchange connection properly"""
        if self.exchange:
            await self.exchange.close()
            
    async def download_data_async(self, exchange: str = "binance", dir: str = "data"):
        """Download historical data for all symbol pairs asynchronously"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(dir, exist_ok=True)
            
            await self.initialize_exchange()
            
            for symbol in self.symbols:
                filename = f"{dir}/{exchange}-{symbol.replace('/', '')}-{self.timeframe}.pkl"
                
                # Skip if file already exists
                if os.path.exists(filename):
                    print(f"Loading existing data for {symbol}")
                    self.data[symbol] = pd.read_pickle(filename)
                    continue
                
                print(f"Downloading data for {symbol}")
                since_ts = int(self.since.timestamp() * 1000)
                
                # Get all candles
                all_ohlcv = []
                while True:
                    ohlcv = await self.exchange.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=self.timeframe,
                        since=since_ts,
                        limit=1000  # Maximum number of candles per request
                    )
                    
                    if not ohlcv:
                        break
                        
                    all_ohlcv.extend(ohlcv)
                    
                    # Update since_ts for next iteration
                    since_ts = ohlcv[-1][0] + 1
                    
                    # Add delay to avoid rate limits
                    await asyncio.sleep(1)
                
                if all_ohlcv:
                    # Convert to DataFrame
                    df = pd.DataFrame(
                        all_ohlcv,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    # Convert timestamp to timezone-aware datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                    df.set_index('timestamp', inplace=True)
                    
                    # Save to file
                    df.to_pickle(filename)
                    self.data[symbol] = df
                    print(f"Downloaded {len(df)} candles for {symbol}")
                else:
                    print(f"No data available for {symbol}")
                
        finally:
            await self.close_exchange()
            
    def download_data(self, exchange: str = "binance", dir: str = "data"):
        """Synchronous wrapper for download_data_async"""
        asyncio.run(self.download_data_async(exchange, dir))
            
    def update_exchange_rates(self, timestamp: pd.Timestamp) -> Dict[Tuple[str, str], float]:
        """Update current exchange rates based on timestamp"""
        self.current_rates = {}
        
        for symbol in self.symbols:
            base, quote = symbol.split('/')
            
            # Get current price
            current_data = self.data[symbol].loc[self.data[symbol].index == timestamp]
            if not current_data.empty:
                price = current_data['close'].iloc[0]
                print(f"Debug: {symbol} price at {timestamp}: {price}")
                
                # Add direct rate
                self.current_rates[(quote, base)] = 1.0 / price  # Buy base with quote
                self.current_rates[(base, quote)] = price        # Sell base for quote
                
                print(f"Debug: Rate {quote}->{base}: {self.current_rates[(quote, base)]}")
                print(f"Debug: Rate {base}->{quote}: {self.current_rates[(base, quote)]}")
    
        return self.current_rates
    
    def find_arbitrage_opportunity(self, start_currency: str = "USDT") -> Tuple[bool, List[str], float]:
        """Find arbitrage opportunity in current rates"""
        self.bf_arbitrage.create_graph(self.current_rates)
        return self.bf_arbitrage.find_arbitrage(start_currency)
    
    def analyze_triangle(self, timestamp):
        """Analyze triangular arbitrage opportunity for specific timestamp"""
        rates = self.update_exchange_rates(timestamp)
        
        # Get exchange rates from price data directly
        btc_usdt_price = float(self.data["BTC/USDT"].loc[timestamp, "close"])
        eth_usdt_price = float(self.data["ETH/USDT"].loc[timestamp, "close"])
        eth_btc_price = float(self.data["ETH/BTC"].loc[timestamp, "close"])
        
        print("\nExchange rates:")
        print(f"BTC/USDT: {btc_usdt_price}")
        print(f"ETH/USDT: {eth_usdt_price}")
        print(f"ETH/BTC: {eth_btc_price}")
        
        # Calculate rates with fees
        fee = 1 - self.trading_fee
        
        # Path 1: USDT -> BTC -> ETH -> USDT
        path1_amount = 1000  # Start with 1000 USDT
        path1_step1 = (path1_amount / btc_usdt_price) * fee  # USDT -> BTC
        path1_step2 = (path1_step1 * eth_btc_price) * fee    # BTC -> ETH
        path1_step3 = (path1_step2 * eth_usdt_price) * fee   # ETH -> USDT
        path1_profit = path1_step3 - path1_amount
        
        # Path 2: USDT -> ETH -> BTC -> USDT
        path2_amount = 1000  # Start with 1000 USDT
        path2_step1 = (path2_amount / eth_usdt_price) * fee  # USDT -> ETH
        path2_step2 = (path2_step1 * eth_btc_price) * fee    # ETH -> BTC
        path2_step3 = (path2_step2 * btc_usdt_price) * fee   # BTC -> USDT
        path2_profit = path2_step3 - path2_amount
        
        print(f"\nAnalyzing timestamp: {timestamp}")
        print("\nPath 1: USDT -> BTC -> ETH -> USDT")
        print(f"Step 1: {path1_amount:.4f} USDT -> {path1_step1:.8f} BTC (Rate: {1/btc_usdt_price:.8f})")
        print(f"Step 2: {path1_step1:.8f} BTC -> {path1_step2:.8f} ETH (Rate: {eth_btc_price:.8f})")
        print(f"Step 3: {path1_step2:.8f} ETH -> {path1_step3:.4f} USDT (Rate: {eth_usdt_price:.8f})")
        print(f"Profit: {path1_profit:.4f} USDT ({(path1_profit/path1_amount)*100:.4f}%)")
        
        print("\nPath 2: USDT -> ETH -> BTC -> USDT")
        print(f"Step 1: {path2_amount:.4f} USDT -> {path2_step1:.8f} ETH (Rate: {1/eth_usdt_price:.8f})")
        print(f"Step 2: {path2_step1:.8f} ETH -> {path2_step2:.8f} BTC (Rate: {eth_btc_price:.8f})")
        print(f"Step 3: {path2_step2:.8f} BTC -> {path2_step3:.4f} USDT (Rate: {btc_usdt_price:.8f})")
        print(f"Profit: {path2_profit:.4f} USDT ({(path2_profit/path2_amount)*100:.4f}%)")

    def analyze_timerange(self, start_time: pd.Timestamp, end_time: pd.Timestamp, interval: str = '1h'):
        """Analyze triangular arbitrage opportunities over a time range
        
        Args:
            start_time (pd.Timestamp): Start time for analysis
            end_time (pd.Timestamp): End time for analysis
            interval (str): Time interval between analyses, e.g. '1h', '30min'
        """
        current_time = start_time
        opportunities = []
        
        print(f"\nAnalyzing time range from {start_time} to {end_time}")
        print("Looking for profitable opportunities...\n")
        
        while current_time <= end_time:
            try:
                # Update rates for current timestamp
                self.update_exchange_rates(current_time)
                
                # Get exchange rates from price data
                btc_usdt_price = float(self.data["BTC/USDT"].loc[current_time, "close"])
                eth_usdt_price = float(self.data["ETH/USDT"].loc[current_time, "close"])
                eth_btc_price = float(self.data["ETH/BTC"].loc[current_time, "close"])
                
                # Calculate rates with fees
                fee = 1 - self.trading_fee
                
                # Path 1: USDT -> BTC -> ETH -> USDT
                path1_amount = 1000
                path1_step1 = (path1_amount / btc_usdt_price) * fee
                path1_step2 = (path1_step1 * eth_btc_price) * fee
                path1_step3 = (path1_step2 * eth_usdt_price) * fee
                path1_profit = path1_step3 - path1_amount
                path1_profit_pct = (path1_profit/path1_amount)*100
                
                # Path 2: USDT -> ETH -> BTC -> USDT
                path2_amount = 1000
                path2_step1 = (path2_amount / eth_usdt_price) * fee
                path2_step2 = (path2_step1 * eth_btc_price) * fee
                path2_step3 = (path2_step2 * btc_usdt_price) * fee
                path2_profit = path2_step3 - path2_amount
                path2_profit_pct = (path2_profit/path2_amount)*100
                
                # Store opportunity if profitable
                if path1_profit > 0 or path2_profit > 0:
                    opportunity = {
                        'timestamp': current_time,
                        'path1_profit': path1_profit,
                        'path1_profit_pct': path1_profit_pct,
                        'path2_profit': path2_profit,
                        'path2_profit_pct': path2_profit_pct,
                        'btc_usdt': btc_usdt_price,
                        'eth_usdt': eth_usdt_price,
                        'eth_btc': eth_btc_price
                    }
                    opportunities.append(opportunity)
                    print(f"Found opportunity at {current_time}:")
                    if path1_profit > 0:
                        print(f"  Path 1 (USDT->BTC->ETH->USDT): {path1_profit:.4f} USDT ({path1_profit_pct:.4f}%)")
                    if path2_profit > 0:
                        print(f"  Path 2 (USDT->ETH->BTC->USDT): {path2_profit:.4f} USDT ({path2_profit_pct:.4f}%)")
                
            except KeyError:
                pass  # Skip timestamps where we don't have data
                
            # Move to next interval
            current_time += pd.Timedelta(interval)
        
        # Print summary
        print(f"\nAnalysis complete. Found {len(opportunities)} profitable opportunities.")
        if opportunities:
            # Find best opportunity for each path
            best_path1 = max(opportunities, key=lambda x: x['path1_profit'])
            best_path2 = max(opportunities, key=lambda x: x['path2_profit'])
            
            print("\nBest opportunities:")
            if best_path1['path1_profit'] > 0:
                print(f"Path 1 (USDT->BTC->ETH->USDT):")
                print(f"  Time: {best_path1['timestamp']}")
                print(f"  Profit: {best_path1['path1_profit']:.4f} USDT ({best_path1['path1_profit_pct']:.4f}%)")
                print(f"  Rates: BTC/USDT={best_path1['btc_usdt']:.2f}, ETH/BTC={best_path1['eth_btc']:.6f}, ETH/USDT={best_path1['eth_usdt']:.2f}")
            
            if best_path2['path2_profit'] > 0:
                print(f"\nPath 2 (USDT->ETH->BTC->USDT):")
                print(f"  Time: {best_path2['timestamp']}")
                print(f"  Profit: {best_path2['path2_profit']:.4f} USDT ({best_path2['path2_profit_pct']:.4f}%)")
                print(f"  Rates: BTC/USDT={best_path2['btc_usdt']:.2f}, ETH/BTC={best_path2['eth_btc']:.6f}, ETH/USDT={best_path2['eth_usdt']:.2f}")
        
        return opportunities

def main():
    # Initialize with the trading pairs you want to monitor
    symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "ETH/BTC"
    ]
    
    try:
        # Create trader instance with 0.1% trading fee
        trader = CryptoArbitrageTrader(symbols, trading_fee=0.001)
        
        # Download historical data
        print("Downloading historical data...")
        trader.download_data()
        
        # Analyze specific timestamp
        timestamp = pd.Timestamp("2022-11-19 21:00:00+00:00")
        trader.analyze_triangle(timestamp)
        
        # Analyze time range with 15-minute intervals
        start_time = pd.Timestamp("2022-11-18 00:00:00+00:00")  # Start from 18th
        end_time = pd.Timestamp("2022-11-20 00:00:00+00:00")    # End at 20th
        trader.analyze_timerange(start_time, end_time, interval='15min')
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
