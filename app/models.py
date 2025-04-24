import pandas as pd
import numpy as np
import networkx as nx
import time
import random
from datetime import datetime
import math
from collections import defaultdict

class PetriNetSimulator:
    """
    Implementation of Safe Petri Net Simulator for Bitcoin Transaction Network.
    In the Petri Net model:
    - Places represent Bitcoin addresses
    - Transitions represent Bitcoin transactions
    - Tokens represent Bitcoins
    """
    
    def __init__(self):
        self.places = {}  # Bitcoin addresses
        self.transitions = {}  # Bitcoin transactions
        self.arcs = []  # Connections between addresses and transactions
        self.tokens = {}  # Bitcoin balances for each address
    
    def add_place(self, place_id, initial_tokens=0):
        """Add a Bitcoin address (place) to the Petri net."""
        self.places[place_id] = {'id': place_id}
        self.tokens[place_id] = initial_tokens
    
    def add_transition(self, transition_id, metadata=None):
        """Add a Bitcoin transaction (transition) to the Petri net."""
        self.transitions[transition_id] = {
            'id': transition_id,
            'metadata': metadata or {}
        }
    
    def add_arc(self, source, target, weight=1):
        """Add a connection between address and transaction."""
        arc = {'source': source, 'target': target, 'weight': weight}
        self.arcs.append(arc)
    
    def is_transition_enabled(self, transition_id):
        """Check if a transaction can be executed based on input addresses having sufficient tokens."""
        # Find all input places to this transition
        input_arcs = [arc for arc in self.arcs if arc['target'] == transition_id]
        
        # Check if all input places have enough tokens
        for arc in input_arcs:
            place_id = arc['source']
            required_tokens = arc['weight']
            
            if place_id not in self.tokens or self.tokens[place_id] < required_tokens:
                return False
        
        return True
    
    def fire_transition(self, transition_id):
        """Execute a transaction by moving tokens from input addresses to output addresses."""
        if not self.is_transition_enabled(transition_id):
            return False
        
        # Find all input and output arcs to this transition
        input_arcs = [arc for arc in self.arcs if arc['target'] == transition_id]
        output_arcs = [arc for arc in self.arcs if arc['source'] == transition_id]
        
        # Remove tokens from input places
        for arc in input_arcs:
            place_id = arc['source']
            tokens_to_remove = arc['weight']
            self.tokens[place_id] -= tokens_to_remove
        
        # Add tokens to output places
        for arc in output_arcs:
            place_id = arc['target']
            tokens_to_add = arc['weight']
            if place_id not in self.tokens:
                self.tokens[place_id] = 0
            self.tokens[place_id] += tokens_to_add
        
        return True
    
    def get_marking(self):
        """Get the current state of the Petri net (token distribution)."""
        return self.tokens.copy()
    
    def get_transaction_trace(self, transition_id):
        """Get the input and output places of a transition."""
        input_places = [arc['source'] for arc in self.arcs if arc['target'] == transition_id]
        output_places = [arc['target'] for arc in self.arcs if arc['source'] == transition_id]
        
        return {
            'transaction_id': transition_id,
            'input_addresses': input_places,
            'output_addresses': output_places
        }


class BTN_Network:
    """
    Bitcoin Transaction Network analyzer based on Petri Net.
    This class processes Bitcoin transactions and builds a Petri Net model.
    """
    
    def __init__(self, transaction_data):
        """
        Initialize the BTN with transaction data.
        
        Args:
            transaction_data: DataFrame with Bitcoin transaction data
        """
        self.transaction_data = transaction_data
        self.petri_net = PetriNetSimulator()
        self.transactions = []
        self.addresses = set()
        self.suspected_addresses = []
        # Feature values for pattern matching
        self.address_features = {}
        # Graph representation for visualization
        self.graph = nx.DiGraph()
        
        # Address clusters - group addresses likely owned by same entity
        self.address_clusters = defaultdict(set)
        self.cluster_id_counter = 0
        
        # Transaction timeline for time-based analysis
        self.transaction_timeline = {}
        
        # Performance metrics
        self.processing_times = {
            'parsing': 0,
            'petri_net_build': 0,
            'pattern_matching': 0,
            'extension_rules': 0
        }
    
    def parse_transactions(self):
        """
        Parse Bitcoin transactions and build the Petri Net model.
        
        Returns:
            List of parsed transaction details
        """
        start_time = time.time()
        
        # Process each transaction
        for idx, tx in self.transaction_data.iterrows():
            transaction_id = str(tx.get('hash', f'tx_{idx}'))
            timestamp = tx.get('timestamp', datetime.now().timestamp())
            
            # Extract input addresses
            input_addresses = self._extract_addresses(tx, 'input')
            
            # Extract output addresses
            output_addresses = self._extract_addresses(tx, 'output')
            
            # Add transaction to Petri Net
            self._add_transaction_to_petri_net(transaction_id, input_addresses, output_addresses, timestamp)
            
            # Add transaction to our list
            tx_info = {
                'transaction_id': transaction_id,
                'timestamp': timestamp,
                'input_addresses': input_addresses,
                'output_addresses': output_addresses
            }
            self.transactions.append(tx_info)
            
            # Record in timeline
            self.transaction_timeline[transaction_id] = {
                'timestamp': timestamp,
                'info': tx_info
            }
            
            # Apply multi-input heuristic for address clustering
            if len(input_addresses) > 1:
                cluster_id = self._get_or_create_cluster(list(input_addresses.keys())[0])
                for addr in input_addresses.keys():
                    self._add_to_cluster(addr, cluster_id)
        
        self.processing_times['parsing'] = time.time() - start_time
        
        # Calculate features for each address
        self._calculate_address_features()
        
        return self.transactions
    
    def _get_or_create_cluster(self, address):
        """Get cluster ID for an address or create a new cluster."""
        for cluster_id, addresses in self.address_clusters.items():
            if address in addresses:
                return cluster_id
        
        # Create new cluster
        self.cluster_id_counter += 1
        return self.cluster_id_counter
    
    def _add_to_cluster(self, address, cluster_id):
        """Add an address to a cluster."""
        # If address is already in another cluster, merge the clusters
        for existing_id, addresses in list(self.address_clusters.items()):
            if address in addresses and existing_id != cluster_id:
                # Merge clusters
                self.address_clusters[cluster_id].update(addresses)
                del self.address_clusters[existing_id]
                return
        
        # Add address to specified cluster
        self.address_clusters[cluster_id].add(address)
    
    def _extract_addresses(self, tx, direction):
        """
        Extract addresses from transaction data.
        
        Args:
            tx: Transaction row
            direction: 'input' or 'output'
            
        Returns:
            Dict of addresses and their values
        """
        addresses = {}
        
        # Handle based on available columns in the dataset
        if f'{direction}_address' in tx and f'{direction}_value' in tx:
            # Single address format
            address = str(tx[f'{direction}_address'])
            value = float(tx[f'{direction}_value'])
            if address and address != 'nan':
                addresses[address] = value
                self.addresses.add(address)
        elif f'{direction}_addresses' in tx:
            # Multiple addresses in a list or string format
            addr_list = tx[f'{direction}_addresses']
            if isinstance(addr_list, str):
                # Parse string representation of addresses
                try:
                    addr_list = eval(addr_list) if '[' in addr_list else addr_list.split(',')
                except:
                    addr_list = [addr_list]
            
            # If we have values, use them, otherwise assign default value 1.0
            if f'{direction}_values' in tx:
                values = tx[f'{direction}_values']
                if isinstance(values, str):
                    try:
                        values = eval(values) if '[' in values else list(map(float, values.split(',')))
                    except:
                        values = [1.0] * len(addr_list)
                
                for i, addr in enumerate(addr_list):
                    addr = str(addr).strip()
                    if addr and addr != 'nan':
                        value = values[i] if i < len(values) else 1.0
                        addresses[addr] = float(value)
                        self.addresses.add(addr)
            else:
                # Default value if no values column
                for addr in addr_list:
                    addr = str(addr).strip()
                    if addr and addr != 'nan':
                        addresses[addr] = 1.0
                        self.addresses.add(addr)
        
        return addresses
    
    def _add_transaction_to_petri_net(self, transaction_id, input_addresses, output_addresses, timestamp):
        """
        Add a transaction to the Petri Net model.
        
        Args:
            transaction_id: Unique ID for the transaction
            input_addresses: Dict of input addresses and values
            output_addresses: Dict of output addresses and values
            timestamp: Transaction timestamp
        """
        start_time = time.time()
        
        # Add transaction to Petri Net
        self.petri_net.add_transition(transaction_id, {'timestamp': timestamp})
        
        # Add addresses (places) and connections (arcs)
        for addr, value in input_addresses.items():
            if addr not in self.petri_net.places:
                self.petri_net.add_place(addr, initial_tokens=value)
            
            # Add arc from address to transaction
            self.petri_net.add_arc(addr, transaction_id, weight=value)
            
            # Add to graph for visualization
            self.graph.add_node(addr, type='address')
            self.graph.add_node(transaction_id, type='transaction')
            self.graph.add_edge(addr, transaction_id, weight=value)
        
        for addr, value in output_addresses.items():
            if addr not in self.petri_net.places:
                self.petri_net.add_place(addr)
            
            # Add arc from transaction to address
            self.petri_net.add_arc(transaction_id, addr, weight=value)
            
            # Add to graph for visualization
            self.graph.add_node(addr, type='address')
            self.graph.add_edge(transaction_id, addr, weight=value)
        
        self.processing_times['petri_net_build'] += time.time() - start_time
    
    def _calculate_address_features(self):
        """Calculate features for each Bitcoin address for pattern matching."""
        for addr in self.addresses:
            # Initialize features
            received = 0
            balance = 0
            in_txs = []
            out_txs = []
            
            # Calculate received and balance
            for arc in self.petri_net.arcs:
                if arc['target'] == addr:  # Address receives Bitcoin
                    received += arc['weight']
                    balance += arc['weight']
                    # Find the transaction id (should be the source of the arc)
                    if arc['source'] in self.petri_net.transitions:
                        in_txs.append(arc['source'])
                elif arc['source'] == addr:  # Address sends Bitcoin
                    balance -= arc['weight']
                    if arc['target'] in self.petri_net.transitions:
                        out_txs.append(arc['target'])
            
            # Calculate transaction timestamps for time-based features
            timestamps = []
            for tx_id in in_txs + out_txs:
                if tx_id in self.petri_net.transitions and 'timestamp' in self.petri_net.transitions[tx_id].get('metadata', {}):
                    timestamps.append(self.petri_net.transitions[tx_id]['metadata']['timestamp'])
            
            # Calculate time-based features
            lifespan = 0
            avg_time_between_txs = 0
            
            if timestamps:
                timestamps.sort()
                lifespan = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
                
                # Calculate average time between transactions
                if len(timestamps) > 1:
                    time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                    avg_time_between_txs = sum(time_diffs) / len(time_diffs)
            
            # Find cluster this address belongs to
            cluster_id = None
            for cid, addrs in self.address_clusters.items():
                if addr in addrs:
                    cluster_id = cid
                    break
            
            # Store features
            self.address_features[addr] = {
                'received': received,
                'balance': balance,
                'in_degree': self.graph.in_degree(addr) if addr in self.graph else 0,
                'out_degree': self.graph.out_degree(addr) if addr in self.graph else 0,
                'in_txs': in_txs,
                'out_txs': out_txs,
                'tx_count': len(in_txs) + len(out_txs),
                'lifespan': lifespan,
                'avg_time_between_txs': avg_time_between_txs,
                'cluster_id': cluster_id,
                'betweenness_centrality': 0,  # Will be calculated later if needed
            }
    
    def _calculate_graph_metrics(self):
        """Calculate advanced graph metrics for addresses in the network."""
        # Only calculate for subgraphs with high-risk addresses to save computation
        risk_nodes = [addr for addr, features in self.address_features.items() 
                     if features['tx_count'] > 5]
        
        if len(risk_nodes) > 0:
            # Create a subgraph with these nodes
            subgraph = self.graph.subgraph(risk_nodes + 
                                          [n for n in self.graph.nodes() if self.graph.nodes[n].get('type') == 'transaction'])
            
            # Calculate betweenness centrality for the subgraph
            bc = nx.betweenness_centrality(subgraph, k=min(len(subgraph), 100))
            
            # Update address features
            for addr in risk_nodes:
                if addr in bc:
                    self.address_features[addr]['betweenness_centrality'] = bc[addr]
    
    def run_pattern_matching(self):
        """
        Run pattern matching algorithm to identify suspected addresses.
        
        Returns:
            List of suspected addresses with details
        """
        start_time = time.time()
        self.suspected_addresses = []
        self.detected_patterns = []  # Store all detected patterns for reporting
        
        # Calculate graph metrics for advanced detection
        self._calculate_graph_metrics()
        
        # Store transaction amounts for pattern detection
        tx_values = []
        for tx in self.transactions:
            input_sum = sum(tx['input_addresses'].values())
            tx_values.append(input_sum)
        
        # Find median transaction value
        median_tx_value = np.median(tx_values) if tx_values else 0
        
        # Calculate withdrawal statistics for anomaly detection
        withdrawal_values = [sum(tx['input_addresses'].values()) for tx in self.transactions]
        withdrawal_mean = np.mean(withdrawal_values) if withdrawal_values else 0
        withdrawal_std = np.std(withdrawal_values) if withdrawal_values else 0
        
        # Calculate deposit statistics for anomaly detection
        deposit_values = [sum(tx['output_addresses'].values()) for tx in self.transactions]
        deposit_mean = np.mean(deposit_values) if deposit_values else 0
        deposit_std = np.std(deposit_values) if deposit_values else 0
        
        # Patterns to identify suspicious behavior
        for addr, features in self.address_features.items():
            is_suspected = False
            reasons = []
            risk_score = 0
            pattern_details = []  # Store detailed pattern information
            
            # 1. Pattern: Negative balance (impossible in real Bitcoin)
            if features['balance'] < 0:
                is_suspected = True
                reasons.append("Negative balance")
                risk_score += 80
                pattern_details.append({
                    'pattern': "Negative balance",
                    'risk_score': 80,
                    'details': f"Address has negative balance of {features['balance']:.8f} BTC"
                })
            
            # 2. Pattern: No deposits over a specific time window (e.g. 7 or 30 days)
            if features['in_txs']:
                # Get timestamps of all transactions
                timestamps = []
                for tx_id in features['in_txs'] + features['out_txs']:
                    if tx_id in self.petri_net.transitions and 'timestamp' in self.petri_net.transitions[tx_id].get('metadata', {}):
                        timestamps.append(self.petri_net.transitions[tx_id]['metadata']['timestamp'])
                
                if timestamps:
                    timestamps.sort()
                    # Check for 7-day inactivity
                    for i in range(len(timestamps) - 1):
                        time_diff = timestamps[i+1] - timestamps[i]
                        if time_diff > 7 * 24 * 60 * 60:  # 7 days in seconds
                            is_suspected = True
                            reasons.append("Inactive period detected")
                            risk_score += 40
                            pattern_details.append({
                                'pattern': "Inactive period",
                                'risk_score': 40,
                                'details': f"Inactive period of {time_diff / (24 * 60 * 60):.1f} days detected",
                                'start_time': timestamps[i],
                                'end_time': timestamps[i+1]
                            })
                            break
            
            # 3. Pattern: Unusually high withdrawals
            for tx_id in features['out_txs']:
                tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                if tx_info:
                    withdrawal_amount = sum(tx_info['input_addresses'].values())
                    # Check if withdrawal is more than 2 standard deviations above mean
                    if withdrawal_amount > withdrawal_mean + 2 * withdrawal_std and withdrawal_amount > 0:
                        is_suspected = True
                        reasons.append("Unusually high withdrawal")
                        risk_score += 60
                        pattern_details.append({
                            'pattern': "Unusually high withdrawal",
                            'risk_score': 60,
                            'details': f"Withdrawal of {withdrawal_amount:.8f} BTC (mean: {withdrawal_mean:.8f}, std: {withdrawal_std:.8f})",
                            'transaction_id': tx_id,
                            'timestamp': tx_info.get('timestamp', 0)
                        })
                        break
            
            # 4. Pattern: Sudden spikes in activity
            if features['tx_count'] > 5:
                # Get timestamps of all transactions
                timestamps = []
                for tx_id in features['in_txs'] + features['out_txs']:
                    if tx_id in self.petri_net.transitions and 'timestamp' in self.petri_net.transitions[tx_id].get('metadata', {}):
                        timestamps.append(self.petri_net.transitions[tx_id]['metadata']['timestamp'])
                
                if timestamps:
                    timestamps.sort()
                    # Check for sudden spikes in activity (multiple transactions in short time)
                    for i in range(len(timestamps) - 2):
                        time_diff = timestamps[i+2] - timestamps[i]
                        if time_diff < 3600:  # 3 transactions within 1 hour
                            is_suspected = True
                            reasons.append("Sudden spike in activity")
                            risk_score += 50
                            pattern_details.append({
                                'pattern': "Sudden spike in activity",
                                'risk_score': 50,
                                'details': f"3 transactions within {time_diff/60:.1f} minutes",
                                'start_time': timestamps[i],
                                'end_time': timestamps[i+2]
                            })
                            break
            
            # 5. Pattern: Repeated failed or small-value transactions
            small_tx_count = 0
            for tx_id in features['out_txs']:
                tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                if tx_info:
                    for val in tx_info['output_addresses'].values():
                        if val < 0.0001:  # Extremely small amount
                            small_tx_count += 1
            
            if small_tx_count > 5:
                is_suspected = True
                reasons.append("Repeated small-value transactions")
                risk_score += 55
                pattern_details.append({
                    'pattern': "Repeated small-value transactions",
                    'risk_score': 55,
                    'details': f"{small_tx_count} transactions with values < 0.0001 BTC"
                })
            
            # 6. Pattern: Hoarding behavior (receives but never sends)
            if features['received'] > median_tx_value * 5 and features['out_degree'] == 0:
                is_suspected = True
                reasons.append("Hoarding address with significant funds")
                risk_score += 50
                pattern_details.append({
                    'pattern': "Hoarding behavior",
                    'risk_score': 50,
                    'details': f"Received {features['received']:.8f} BTC but never sent funds"
                })
            
            # 7. Pattern: Unusually high transaction volume
            if features['in_degree'] > 20 or features['out_degree'] > 20:
                is_suspected = True
                reasons.append("Unusually high transaction volume")
                risk_score += min((features['in_degree'] + features['out_degree']) / 10, 60)
                pattern_details.append({
                    'pattern': "High transaction volume",
                    'risk_score': min((features['in_degree'] + features['out_degree']) / 10, 60),
                    'details': f"In-degree: {features['in_degree']}, Out-degree: {features['out_degree']}"
                })
            
            # 8. Pattern: Short-lived address with high activity (possible mixer)
            if features['tx_count'] > 10 and features['lifespan'] < 86400:  # 24 hours in seconds
                is_suspected = True
                reasons.append("High-volume short-lived address")
                risk_score += 70
                pattern_details.append({
                    'pattern': "Short-lived high activity",
                    'risk_score': 70,
                    'details': f"{features['tx_count']} transactions in {features['lifespan']/3600:.1f} hours"
                })
            
            # 9. Pattern: High centrality in transaction network
            if features['betweenness_centrality'] > 0.1:
                is_suspected = True
                reasons.append("High centrality node (possible money mule)")
                risk_score += 40 + features['betweenness_centrality'] * 100
                pattern_details.append({
                    'pattern': "High centrality node",
                    'risk_score': 40 + features['betweenness_centrality'] * 100,
                    'details': f"Betweenness centrality: {features['betweenness_centrality']:.4f}"
                })
            
            # 10. Pattern: Periodic transactions (automated behavior)
            if features['tx_count'] > 5 and features['avg_time_between_txs'] > 0:
                time_diffs = []
                for i in range(len(features['in_txs']) - 1):
                    tx1 = features['in_txs'][i]
                    tx2 = features['in_txs'][i+1]
                    if tx1 in self.petri_net.transitions and tx2 in self.petri_net.transitions:
                        t1 = self.petri_net.transitions[tx1]['metadata'].get('timestamp', 0)
                        t2 = self.petri_net.transitions[tx2]['metadata'].get('timestamp', 0)
                        if t1 and t2:
                            time_diffs.append(abs(t2 - t1))
                
                if time_diffs:
                    # Check for periodicity using coefficient of variation
                    mean_diff = np.mean(time_diffs)
                    std_diff = np.std(time_diffs)
                    if mean_diff > 0 and std_diff / mean_diff < 0.1:  # Low variation = periodic
                        is_suspected = True
                        reasons.append("Periodic transaction pattern")
                        risk_score += 30
                        pattern_details.append({
                            'pattern': "Periodic transactions",
                            'risk_score': 30,
                            'details': f"Mean time between transactions: {mean_diff/3600:.1f} hours, CV: {std_diff/mean_diff:.4f}"
                        })
            
            # 11. Pattern: CoinJoin transaction (privacy-enhancing technique often used in money laundering)
            for tx_id in features['in_txs']:
                tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                if tx_info and len(tx_info['input_addresses']) >= 3:
                    # Check if outputs have equal values
                    output_values = list(tx_info['output_addresses'].values())
                    if len(output_values) >= 2 and len(set(output_values)) == 1:
                        is_suspected = True
                        reasons.append("Participated in CoinJoin transaction")
                        risk_score += 60
                        pattern_details.append({
                            'pattern': "CoinJoin transaction",
                            'risk_score': 60,
                            'details': f"Transaction with {len(tx_info['input_addresses'])} inputs and equal outputs",
                            'transaction_id': tx_id,
                            'timestamp': tx_info.get('timestamp', 0)
                        })
                        break
            
            # 12. Pattern: Peel chain (a series of transactions moving funds with change addresses)
            if features['in_degree'] == 1 and features['out_degree'] == 2:
                # This might be a change address in a peel chain
                out_txs = features['out_txs']
                if len(out_txs) >= 1:
                    # Check if one output is much larger than the other (change pattern)
                    for tx_id in out_txs:
                        tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                        if tx_info and len(tx_info['output_addresses']) == 2:
                            values = list(tx_info['output_addresses'].values())
                            ratio = max(values) / (min(values) + 0.00001)
                            if ratio > 5:  # Significant difference in output values
                                is_suspected = True
                                reasons.append("Part of peel chain")
                                risk_score += 45
                                pattern_details.append({
                                    'pattern': "Peel chain",
                                    'risk_score': 45,
                                    'details': f"Output ratio: {ratio:.2f}",
                                    'transaction_id': tx_id,
                                    'timestamp': tx_info.get('timestamp', 0)
                                })
                                break
            
            # 13. Pattern: Epsilon transactions (outputs differing by very small amounts)
            for tx_id in features['out_txs']:
                tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                if tx_info and len(tx_info['output_addresses']) >= 2:
                    values = list(tx_info['output_addresses'].values())
                    for i in range(len(values)):
                        for j in range(i+1, len(values)):
                            if 0 < abs(values[i] - values[j]) < 0.001:
                                is_suspected = True
                                reasons.append("Epsilon transaction pattern")
                                risk_score += 35
                                pattern_details.append({
                                    'pattern': "Epsilon transaction",
                                    'risk_score': 35,
                                    'details': f"Outputs differ by {abs(values[i] - values[j]):.8f} BTC",
                                    'transaction_id': tx_id,
                                    'timestamp': tx_info.get('timestamp', 0)
                                })
                                break
            
            if is_suspected:
                # Calculate final risk score (cap at 100)
                final_risk_score = min(risk_score, 100)
                
                # Add to suspected addresses
                self.suspected_addresses.append({
                    'address': addr,
                    'reasons': reasons,
                    'risk_score': final_risk_score,
                    'features': features,
                    'cluster_id': features['cluster_id'],
                    'pattern_details': pattern_details
                })
                
                # Add patterns to global list for reporting
                for pattern in pattern_details:
                    pattern['address'] = addr
                    self.detected_patterns.append(pattern)
        
        # Sort by risk score (descending)
        self.suspected_addresses.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Sort patterns by risk score (descending)
        self.detected_patterns.sort(key=lambda x: x['risk_score'], reverse=True)
        
        self.processing_times['pattern_matching'] = time.time() - start_time
        
        return self.suspected_addresses
    
    def run_extension_rules(self):
        """
        Run extension rules matching from cache.
        
        Returns:
            Results of extension rules application
        """
        start_time = time.time()
        
        # Group suspected addresses by cluster to find related addresses
        suspected_clusters = set()
        for addr_info in self.suspected_addresses:
            if addr_info['cluster_id']:
                suspected_clusters.add(addr_info['cluster_id'])
        
        # Find related addresses in the same clusters
        related_addresses = []
        for cluster_id in suspected_clusters:
            for addr in self.address_clusters[cluster_id]:
                if addr not in [a['address'] for a in self.suspected_addresses]:
                    features = self.address_features.get(addr, {})
                    related_addresses.append({
                        'address': addr,
                        'reasons': ["Related to suspicious address in same cluster"],
                        'risk_score': 30,  # Lower risk score for related addresses
                        'features': features,
                        'cluster_id': cluster_id
                    })
        
        # Add related addresses to suspected addresses
        self.suspected_addresses.extend(related_addresses)
        
        # Resort by risk score
        self.suspected_addresses.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Apply clustering to identify connected components in the graph
        subgraph = self.graph.subgraph([a['address'] for a in self.suspected_addresses] + 
                                     [n for n in self.graph.nodes() if self.graph.nodes[n].get('type') == 'transaction'])
        
        # Get connected components
        connected_components = list(nx.weakly_connected_components(subgraph))
        
        self.processing_times['extension_rules'] = time.time() - start_time
        
        return {
            'processing_time': self.processing_times['extension_rules'],
            'rules_applied': len(self.suspected_addresses),
            'connected_components': len(connected_components),
            'suspected_clusters': len(suspected_clusters)
        }
    
    def get_withdraw_graph_data(self):
        """
        Generate data for withdrawal transaction graph with pattern annotations.
        
        Returns:
            Data for withdrawal graph visualization
        """
        # Group withdrawals by amount
        withdraw_amounts = {}
        pattern_annotations = []
        
        for tx in self.transactions:
            # Sum of input values represents withdrawals
            total_input = sum(tx['input_addresses'].values())
            
            # Round to nearest whole number for grouping
            amount_group = round(total_input)
            
            if amount_group not in withdraw_amounts:
                withdraw_amounts[amount_group] = 0
            withdraw_amounts[amount_group] += 1
            
            # Check if this transaction is part of a pattern
            tx_id = tx['transaction_id']
            for pattern in self.detected_patterns:
                if 'transaction_id' in pattern and pattern['transaction_id'] == tx_id:
                    # Add annotation for this pattern
                    pattern_annotations.append({
                        'x': amount_group,
                        'y': withdraw_amounts[amount_group],
                        'text': f"{pattern['pattern']}<br>Risk: {pattern['risk_score']}",
                        'showarrow': True,
                        'arrowhead': 2,
                        'arrowsize': 1,
                        'arrowwidth': 2,
                        'arrowcolor': 'red',
                        'ax': 0,
                        'ay': -40
                    })
        
        # Convert to format for chart
        x_data = list(withdraw_amounts.keys())
        y_data = list(withdraw_amounts.values())
        
        # Sort by amount
        sorted_data = sorted(zip(x_data, y_data))
        x_data = [x for x, y in sorted_data]
        y_data = [y for x, y in sorted_data]
        
        return {
            'x': x_data,
            'y': y_data,
            'type': 'bar',
            'title': 'Withdrawal Transactions Distribution',
            'annotations': pattern_annotations
        }
    
    def get_deposit_graph_data(self):
        """
        Generate data for deposit transaction graph with pattern annotations.
        
        Returns:
            Data for deposit graph visualization
        """
        # Get top addresses by received amount
        top_addresses = sorted(
            self.address_features.items(),
            key=lambda x: x[1]['received'],
            reverse=True
        )[:20]  # Top 20
        
        x_data = [addr[:10] + '...' for addr, _ in top_addresses]  # Truncate address for display
        y_data = [features['received'] for _, features in top_addresses]
        
        # Add pattern annotations
        pattern_annotations = []
        for i, (addr, _) in enumerate(top_addresses):
            # Check if this address is part of a pattern
            for pattern in self.detected_patterns:
                if pattern['address'] == addr:
                    # Add annotation for this pattern
                    pattern_annotations.append({
                        'x': i,
                        'y': y_data[i],
                        'text': f"{pattern['pattern']}<br>Risk: {pattern['risk_score']}",
                        'showarrow': True,
                        'arrowhead': 2,
                        'arrowsize': 1,
                        'arrowwidth': 2,
                        'arrowcolor': 'red',
                        'ax': 0,
                        'ay': -40
                    })
                    break
        
        return {
            'x': x_data,
            'y': y_data,
            'type': 'bar',
            'title': 'Top Addresses by Deposit Amount',
            'annotations': pattern_annotations
        }
    
    def get_propose_vs_extension_data(self):
        """
        Generate comparison data between proposed and extension methods.
        
        Returns:
            Data for method comparison visualization
        """
        x_data = ['Parsing Time', 'Pattern Matching', 'Extension Rules', 'Total Time']
        
        base_times = [
            self.processing_times['parsing'],
            self.processing_times['pattern_matching'],
            self.processing_times['extension_rules'],
            sum(self.processing_times.values())
        ]
        
        # Normalize to percentages
        total = sum(base_times)
        y_data = [100 * t / total for t in base_times]
        
        return {
            'x': x_data,
            'y': y_data,
            'type': 'bar',
            'title': 'Processing Time Distribution (%)'
        }
    
    def get_suspected_transaction_details(self):
        """
        Generate detailed information about suspicious transactions.
        
        Returns:
            Dictionary with transaction details for each suspected address
        """
        transaction_details = {}
        
        for addr_info in self.suspected_addresses:
            addr = addr_info['address']
            features = addr_info['features']
            
            # Get all transactions involving this address
            tx_ids = features.get('in_txs', []) + features.get('out_txs', [])
            tx_details = []
            
            for tx_id in tx_ids:
                tx_info = next((t for t in self.transactions if t['transaction_id'] == tx_id), None)
                if tx_info:
                    # Determine if address is input or output in this transaction
                    is_input = addr in tx_info['input_addresses']
                    is_output = addr in tx_info['output_addresses']
                    
                    # Calculate amount involved
                    amount = 0
                    if is_input:
                        amount = tx_info['input_addresses'].get(addr, 0)
                    elif is_output:
                        amount = tx_info['output_addresses'].get(addr, 0)
                    
                    tx_details.append({
                        'transaction_id': tx_id,
                        'timestamp': tx_info.get('timestamp', 0),
                        'is_input': is_input,
                        'is_output': is_output,
                        'amount': amount,
                        'total_input': sum(tx_info['input_addresses'].values()),
                        'total_output': sum(tx_info['output_addresses'].values()),
                        'input_count': len(tx_info['input_addresses']),
                        'output_count': len(tx_info['output_addresses'])
                    })
            
            # Sort by timestamp
            tx_details.sort(key=lambda x: x['timestamp'])
            
            transaction_details[addr] = {
                'transactions': tx_details,
                'risk_score': addr_info['risk_score'],
                'reasons': addr_info['reasons'],
                'cluster_id': addr_info['cluster_id']
            }
        
        return transaction_details
    
    def get_pattern_summary_report(self):
        """
        Generate a summary report of all detected patterns.
        
        Returns:
            Dictionary with pattern summary information
        """
        # Group patterns by type
        pattern_types = {}
        for pattern in self.detected_patterns:
            pattern_type = pattern['pattern']
            if pattern_type not in pattern_types:
                pattern_types[pattern_type] = []
            pattern_types[pattern_type].append(pattern)
        
        # Calculate statistics for each pattern type
        pattern_stats = {}
        for pattern_type, patterns in pattern_types.items():
            risk_scores = [p['risk_score'] for p in patterns]
            pattern_stats[pattern_type] = {
                'count': len(patterns),
                'avg_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
                'max_risk_score': max(risk_scores) if risk_scores else 0,
                'addresses': list(set(p['address'] for p in patterns))
            }
        
        # Sort pattern types by count (descending)
        sorted_pattern_types = sorted(
            pattern_stats.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return {
            'total_patterns': len(self.detected_patterns),
            'pattern_types': dict(sorted_pattern_types),
            'patterns': self.detected_patterns
        }