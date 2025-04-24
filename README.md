# Bitcoin Transaction Network (BTN) Analyzer

A forensic investigation tool for analyzing Bitcoin transactions using an extended Safe Petri Net model.

## Overview

This application implements the methodology described in the paper "A Bitcoin Transaction Network Analytic Method for Future Blockchain Forensic Investigation". It uses a Safe Petri Net simulation to model Bitcoin transactions and applies pattern matching rules to identify suspected addresses.

Key features:
- Bitcoin transaction data parsing and preprocessing
- Construction of a Bitcoin Transaction Network (BTN) using Safe Petri Net models
- Pattern matching rules for identifying suspicious transactions
- Data visualization for transaction analysis
- Support for Bitcoin Gene tracking 

## Installation

### Prerequisites

- Python 3.7 or higher
- NodeJS 12.3.1 or higher (optional, for front-end development)

### Setup

1. Clone this repository:
```
git clone https://github.com/your-username/bitcoin-transaction-network.git
cd bitcoin-transaction-network
```

2. Create a virtual environment (optional but recommended):
```
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix or MacOS
```

3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

1. Start the application:
```
python run.py
```
or double-click on `run.bat` on Windows.

2. Open your web browser and navigate to `http://127.0.0.1:5000/`

3. Upload a Bitcoin transaction dataset in CSV format. The application expects a specific format with columns for transaction hashes, input addresses, output addresses, and values.

4. Follow the interface to:
   - Parse and build the BTN Petri Net simulation
   - Run the pattern matching rules algorithm
   - View visualization graphs for withdraw/deposit transactions
   - Analyze suspected addresses

## Dataset Format

The application expects a CSV file with Bitcoin transaction data. The minimum required columns are:
- `hash`: Transaction hash identifier
- `input_address` or `input_addresses`: Source address(es)
- `output_address` or `output_addresses`: Destination address(es)
- `input_value` or `input_values`: Amount sent from each source
- `output_value` or `output_values`: Amount received at each destination
- `timestamp`: Transaction time (optional, but recommended)

## Implementation Details

This application implements:
1. A **Safe Petri Net Simulator** where:
   - Places represent Bitcoin addresses
   - Transitions represent Bitcoin transactions
   - Tokens represent Bitcoins

2. **Pattern Matching Rules** to identify suspected addresses based on:
   - Negative balance (impossible in real Bitcoin)
   - Hoarding behavior (receiving but never sending)
   - Unusually high transaction volume
   - Short-lived addresses

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project is based on research in Bitcoin transaction network analysis and blockchain forensics. "# Bitcoin-Transaction-Network-Analyze" 
"# Bitcoin-Transaction-Network-Analyze" 
