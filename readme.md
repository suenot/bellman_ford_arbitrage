# Crypto Arbitrage Detection

This project implements the Bellman-Ford algorithm to detect arbitrage opportunities in cryptocurrency markets. The implementation includes handling of trading fees and supports multiple trading pairs.

## Quick Start

```bash
pip install -r requirements.txt
python crypto_arbitrage.py
```

## Project Structure

- `bellman_ford_arbitrage.py` - Core implementation of the Bellman-Ford algorithm for arbitrage detection
- `crypto_arbitrage.py` - Example usage with cryptocurrency market data
- `requirements.txt` - Project dependencies

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd arbi_strage
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

The simplest way to use the arbitrage detector is to run the example script:

```bash
python crypto_arbitrage.py
```

### Using the BellmanFordArbitrage Class

```python
from bellman_ford_arbitrage import BellmanFordArbitrage

# Initialize with custom trading fee (default is 0.1%)
arbitrage_finder = BellmanFordArbitrage(trading_fee=0.001)

# Define exchange rates
exchange_rates = {
    ('BTC', 'USDT'): 16679.49,
    ('ETH', 'USDT'): 1211.68,
    ('ETH', 'BTC'): 0.072638
}

# Create the graph
arbitrage_finder.create_graph(exchange_rates)

# Find arbitrage opportunities starting from USDT
has_arbitrage, path, profit = arbitrage_finder.find_arbitrage('USDT')

if has_arbitrage:
    print(f"Arbitrage found! Path: {' -> '.join(path)}")
    print(f"Profit ratio: {profit:.4f}")
else:
    print("No arbitrage opportunities found")
```

## Understanding the Output

The program outputs detailed information about potential arbitrage paths:

```
Path: USDT -> BTC -> ETH -> USDT
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

Each path shows:
- The sequence of currency conversions
- Amount of currency at each step
- Exchange rate used
- Final profit/loss in both absolute and percentage terms

## Technical Details

### Algorithm Implementation

The implementation uses the Bellman-Ford algorithm to detect negative cycles in a weighted directed graph where:
- Vertices represent currencies
- Edges represent exchange rates
- Edge weights are -log(exchange_rate)
- Trading fees are incorporated into the exchange rates

### Features

- Handles trading fees
- Supports multiple currency pairs
- Detects multiple arbitrage paths
- Calculates actual profit considering fees
- Provides detailed path analysis

### Performance Considerations

- Time Complexity: O(V * E) where V is the number of vertices (currencies) and E is the number of edges (trading pairs)
- Space Complexity: O(V) for storing distances and predecessors

## Example Results

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]