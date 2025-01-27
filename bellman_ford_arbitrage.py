import numpy as np
from typing import List, Tuple, Dict
import networkx as nx

class BellmanFordArbitrage:
    def __init__(self, trading_fee: float = 0.001):  # 0.1% trading fee by default
        self.graph = nx.DiGraph()
        self.trading_fee = trading_fee
        
    def create_graph(self, exchange_rates: Dict[Tuple[str, str], float]):
        """
        Create a graph from exchange rates.
        exchange_rates: Dictionary with (from_currency, to_currency) as key and rate as value
        """
        # Clear existing graph
        self.graph.clear()
        
        # Add edges with weights as -log(rate)
        for (from_curr, to_curr), rate in exchange_rates.items():
            # Apply trading fee to the rate
            effective_rate = rate * (1 - self.trading_fee)
            # Use negative log of exchange rate as edge weight
            if effective_rate > 0:  # Avoid log(0) or log(negative)
                weight = -np.log(effective_rate)
                self.graph.add_edge(from_curr, to_curr, weight=weight)
    
    def find_arbitrage(self, start_currency: str) -> Tuple[bool, List[str], float]:
        """
        Find arbitrage opportunity using Bellman-Ford algorithm.
        Returns: (has_arbitrage, path, profit_ratio)
        """
        if not self.graph.has_node(start_currency):
            return False, [], 1.0
            
        # Initialize distances
        distances = {node: float('inf') for node in self.graph.nodes()}
        distances[start_currency] = 0
        predecessors = {node: None for node in self.graph.nodes()}
        
        # Relax edges |V| - 1 times
        for _ in range(len(self.graph.nodes()) - 1):
            for u, v, weight in self.graph.edges(data='weight'):
                if distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    predecessors[v] = u
        
        # Check for negative cycle
        for u, v, weight in self.graph.edges(data='weight'):
            if distances[u] + weight < distances[v]:
                # Negative cycle exists, extract the cycle
                visited = set()
                cycle = []
                current = u
                
                while current not in visited:
                    visited.add(current)
                    cycle.append(current)
                    current = predecessors[current]
                
                # Find start of cycle
                start_idx = cycle.index(current)
                arbitrage_path = cycle[start_idx:][::-1]
                
                # Calculate profit ratio
                profit_ratio = 1.0
                initial_amount = 1.0
                current_amount = initial_amount
                
                # Add the start node to complete the cycle
                arbitrage_path.append(arbitrage_path[0])
                
                # Calculate the actual profit ratio considering fees
                for i in range(len(arbitrage_path)-1):
                    # Get the raw exchange rate
                    rate = np.exp(-self.graph[arbitrage_path[i]][arbitrage_path[i+1]]['weight'])
                    # Apply the fee
                    current_amount = current_amount * rate
                
                profit_ratio = current_amount / initial_amount
                
                return True, arbitrage_path, profit_ratio
        
        return False, [], 1.0

    def get_exchange_rate(self, from_curr: str, to_curr: str) -> float:
        """Get exchange rate between two currencies"""
        if self.graph.has_edge(from_curr, to_curr):
            return np.exp(-self.graph[from_curr][to_curr]['weight'])
        return 0.0
