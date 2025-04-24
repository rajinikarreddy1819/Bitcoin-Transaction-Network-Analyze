import os
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import app
from app.models import BTN_Network, PetriNetSimulator
import pandas as pd
import numpy as np
import json

# Global variable to store the BTN network instance
btn_network = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global btn_network
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Store file path in session
        session['uploaded_file'] = file_path
        
        return jsonify({'success': True, 'message': 'File uploaded successfully', 'file_path': file_path})
    
    return jsonify({'error': 'File type not allowed'})

@app.route('/build_btn', methods=['POST'])
def build_btn():
    global btn_network
    
    try:
        file_path = session.get('uploaded_file')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'No file uploaded or file not found'})
        
        # Read the transactions data
        df = pd.read_csv(file_path)
        
        # Create BTN network
        btn_network = BTN_Network(df)
        
        # Parse transactions and build Petri net
        transactions = btn_network.parse_transactions()
        
        return jsonify({
            'success': True, 
            'message': 'BTN network built successfully',
            'transactions_count': len(transactions),
            'addresses_count': len(btn_network.addresses),
            'transactions': transactions[:10]  # Return first 10 for preview
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/run_pattern_matching', methods=['POST'])
def run_pattern_matching():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Run pattern matching algorithm
        suspected_addresses = btn_network.run_pattern_matching()
        
        # Store results in session
        session['suspected_addresses'] = [addr['address'] for addr in suspected_addresses[:50]]  # Store first 50 for session
        
        return jsonify({
            'success': True,
            'message': 'Pattern matching completed',
            'suspected_count': len(suspected_addresses),
            'suspected_addresses': suspected_addresses[:20]  # Return first 20 for preview
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/withdraw_graph', methods=['GET'])
def withdraw_graph():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Generate withdrawal transaction data for graph
        withdraw_data = btn_network.get_withdraw_graph_data()
        
        return jsonify({
            'success': True,
            'data': withdraw_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/deposit_graph', methods=['GET'])
def deposit_graph():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Generate deposit transaction data for graph
        deposit_data = btn_network.get_deposit_graph_data()
        
        return jsonify({
            'success': True,
            'data': deposit_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/extension_rules', methods=['POST'])
def extension_rules():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Run extension rules matching from cache
        results = btn_network.run_extension_rules()
        
        return jsonify({
            'success': True,
            'message': 'Extension rules applied successfully',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/propose_vs_extension', methods=['GET'])
def propose_vs_extension():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Get comparison data between proposed and extension method
        comparison_data = btn_network.get_propose_vs_extension_data()
        
        return jsonify({
            'success': True,
            'data': comparison_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/transaction_details', methods=['GET'])
def transaction_details():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Get detailed transaction information for suspected addresses
        details = btn_network.get_suspected_transaction_details()
        
        # Get top suspected addresses (by risk score)
        top_suspected = sorted(
            details.items(), 
            key=lambda x: x[1]['risk_score'], 
            reverse=True
        )[:20]  # Top 20
        
        # Format for response
        formatted_details = {}
        for addr, info in top_suspected:
            formatted_details[addr] = {
                'risk_score': info['risk_score'],
                'reasons': info['reasons'],
                'cluster_id': info['cluster_id'],
                'transactions': info['transactions'][:10]  # Limit to 10 transactions per address
            }
        
        return jsonify({
            'success': True,
            'transaction_details': formatted_details
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/suspected_address_detail/<address>', methods=['GET'])
def suspected_address_detail(address):
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Get detailed information for a specific address
        all_details = btn_network.get_suspected_transaction_details()
        
        if address not in all_details:
            return jsonify({'error': 'Address not found or not suspected'})
        
        # Get address details
        address_details = all_details[address]
        
        # Get cluster information
        cluster_id = address_details['cluster_id']
        cluster_addresses = list(btn_network.address_clusters.get(cluster_id, []))
        
        # Format for response
        formatted_details = {
            'address': address,
            'risk_score': address_details['risk_score'],
            'reasons': address_details['reasons'],
            'cluster_id': cluster_id,
            'cluster_size': len(cluster_addresses),
            'related_addresses': cluster_addresses[:10],  # First 10 related addresses
            'transactions': address_details['transactions'],
            'features': btn_network.address_features.get(address, {})
        }
        
        return jsonify({
            'success': True,
            'address_details': formatted_details
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/pattern_summary', methods=['GET'])
def pattern_summary():
    global btn_network
    
    if not btn_network:
        return jsonify({'error': 'BTN network not built yet'})
    
    try:
        # Get pattern summary report
        pattern_report = btn_network.get_pattern_summary_report()
        
        return jsonify({
            'success': True,
            'pattern_report': pattern_report
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}) 