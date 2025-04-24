from app import app

if __name__ == '__main__':
    app.secret_key = 'bitcoin_transaction_network_analyzer'
    app.run(debug=True) 