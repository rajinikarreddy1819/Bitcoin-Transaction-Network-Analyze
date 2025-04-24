from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}
app.secret_key = 'bitcoin_transaction_network_analyzer'

# Import routes after app initialization to avoid circular imports
from app import routes 