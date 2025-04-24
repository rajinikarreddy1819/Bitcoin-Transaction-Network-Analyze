import pandas as pd
import numpy as np
import hashlib
import random
import time
import os

def generate_address():
    """Generate a random Bitcoin-like address."""
    return hashlib.sha256(str(random.random()).encode()).hexdigest()[:34]

def generate_transaction_hash():
    """Generate a random transaction hash."""
    return hashlib.sha256(str(random.random()).encode()).hexdigest()

def generate_timestamp(start_date="2022-01-01", end_date="2023-01-01"):
    """Generate a random timestamp between start and end date."""
    start_ts = time.mktime(time.strptime(start_date, "%Y-%m-%d"))
    end_ts = time.mktime(time.strptime(end_date, "%Y-%m-%d"))
    return int(start_ts + random.random() * (end_ts - start_ts))

def generate_sample_transactions(num_transactions=100, num_addresses=50):
    """
    Generate sample Bitcoin transaction data.
    
    Args:
        num_transactions: Number of transactions to generate
        num_addresses: Number of unique addresses to use
        
    Returns:
        DataFrame with transaction data
    """
    # Generate pool of addresses
    addresses = [generate_address() for _ in range(num_addresses)]
    
    # Initialize transactions list
    transactions = []
    
    # Generate random transactions
    for i in range(num_transactions):
        # Get random number of inputs (1-3)
        num_inputs = random.randint(1, 3)
        # Get random number of outputs (1-5)
        num_outputs = random.randint(1, 5)
        
        # Select input addresses and values
        input_addresses = random.sample(addresses, num_inputs)
        input_values = [round(random.uniform(0.1, 10.0), 8) for _ in range(num_inputs)]
        
        # Total input amount
        total_input = sum(input_values)
        
        # Select output addresses
        output_addresses = random.sample(addresses, num_outputs)
        
        # Distribute input amount to outputs with some fee
        fee = round(total_input * random.uniform(0.001, 0.01), 8)
        remaining = total_input - fee
        
        # Distribute remaining amount to outputs
        output_values = []
        for j in range(num_outputs - 1):
            val = round(remaining * random.uniform(0.1, 0.5), 8)
            output_values.append(val)
            remaining -= val
        
        # Add remaining to last output
        output_values.append(round(remaining, 8))
        
        # Generate timestamp
        timestamp = generate_timestamp()
        
        # Create transaction
        tx = {
            'hash': generate_transaction_hash(),
            'timestamp': timestamp,
            'input_addresses': str(input_addresses),
            'input_values': str(input_values),
            'output_addresses': str(output_addresses),
            'output_values': str(output_values),
            'fee': fee
        }
        
        transactions.append(tx)
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    
    # Add some known suspicious patterns
    
    # 1. Add a hoarding address (receives but never sends)
    hoarding_addr = generate_address()
    hoard_tx = {
        'hash': generate_transaction_hash(),
        'timestamp': generate_timestamp(),
        'input_addresses': str([random.choice(addresses)]),
        'input_values': str([round(random.uniform(50.0, 100.0), 8)]),
        'output_addresses': str([hoarding_addr]),
        'output_values': str([round(random.uniform(49.0, 99.0), 8)]),
        'fee': round(random.uniform(0.1, 1.0), 8)
    }
    transactions.append(hoard_tx)
    
    # 2. Add high volume address
    high_volume_addr = generate_address()
    
    # Add multiple transactions for this address
    for _ in range(20):
        # As input
        hv_tx_in = {
            'hash': generate_transaction_hash(),
            'timestamp': generate_timestamp(),
            'input_addresses': str([high_volume_addr]),
            'input_values': str([round(random.uniform(1.0, 5.0), 8)]),
            'output_addresses': str(random.sample(addresses, 3)),
            'output_values': str([round(random.uniform(0.3, 1.5), 8) for _ in range(3)]),
            'fee': round(random.uniform(0.01, 0.1), 8)
        }
        transactions.append(hv_tx_in)
        
        # As output
        hv_tx_out = {
            'hash': generate_transaction_hash(),
            'timestamp': generate_timestamp(),
            'input_addresses': str(random.sample(addresses, 2)),
            'input_values': str([round(random.uniform(1.0, 5.0), 8) for _ in range(2)]),
            'output_addresses': str([high_volume_addr]),
            'output_values': str([round(random.uniform(1.9, 9.9), 8)]),
            'fee': round(random.uniform(0.01, 0.1), 8)
        }
        transactions.append(hv_tx_out)
    
    # 3. Add address with negative balance (impossible in real Bitcoin)
    neg_balance_addr = generate_address()
    
    # First receive some funds
    neg_tx1 = {
        'hash': generate_transaction_hash(),
        'timestamp': generate_timestamp(),
        'input_addresses': str([random.choice(addresses)]),
        'input_values': str([round(random.uniform(1.0, 2.0), 8)]),
        'output_addresses': str([neg_balance_addr]),
        'output_values': str([round(random.uniform(0.9, 1.9), 8)]),
        'fee': round(random.uniform(0.01, 0.1), 8)
    }
    transactions.append(neg_tx1)
    
    # Then spend more than received (to create negative balance in our model)
    neg_tx2 = {
        'hash': generate_transaction_hash(),
        'timestamp': generate_timestamp("2023-01-02", "2023-01-03"),  # Later timestamp
        'input_addresses': str([neg_balance_addr]),
        'input_values': str([round(random.uniform(2.0, 3.0), 8)]),  # More than received
        'output_addresses': str([random.choice(addresses)]),
        'output_values': str([round(random.uniform(1.9, 2.9), 8)]),
        'fee': round(random.uniform(0.01, 0.1), 8)
    }
    transactions.append(neg_tx2)
    
    # Create final DataFrame
    df = pd.DataFrame(transactions)
    
    return df

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Generate sample data
    transactions_df = generate_sample_transactions(num_transactions=200, num_addresses=50)
    
    # Save to CSV
    file_path = os.path.join('data', 'sample_transactions.csv')
    transactions_df.to_csv(file_path, index=False)
    
    print(f"Generated {len(transactions_df)} sample transactions and saved to {file_path}")
    print(f"Dataset contains {transactions_df['hash'].nunique()} unique transactions")
    
    # Display a few sample records
    print("\nSample records:")
    print(transactions_df.head(3)) 