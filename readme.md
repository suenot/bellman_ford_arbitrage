# tldr
pip install -r requirements.txt
python crypto_arbitrage.py

# result
```
Debug: Rate ETH->BTC: 0.072638

Exchange rates:
BTC/USDT: 16679.49
ETH/USDT: 1211.68
ETH/BTC: 0.072638

Analyzing timestamp: 2022-11-19 21:00:00+00:00

Path 1: USDT -> BTC -> ETH -> USDT
Step 1: 1000.0000 USDT -> 0.05989392 BTC (Rate: 0.00005995)
Step 2: 0.05989392 BTC -> 0.00434622 ETH (Rate: 0.07263800)
Step 3: 0.00434622 ETH -> 5.2610 USDT (Rate: 1211.68000000)
Profit: -994.7390 USDT (-99.4739%)

Path 2: USDT -> ETH -> BTC -> USDT
Step 1: 1000.0000 USDT -> 0.82447511 ETH (Rate: 0.00082530)
Step 2: 0.82447511 ETH -> 0.05982833 BTC (Rate: 0.07263800)
Step 3: 0.05982833 BTC -> 996.9082 USDT (Rate: 16679.49000000)
Profit: -3.0918 USDT (-0.3092%)
```