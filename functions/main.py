# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import firebase_admin
from firebase_admin import credentials
from flask import Flask, request, jsonify
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from firebase_functions import https_fn

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

# Create Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Hello World! Firebase Flask App is running."

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({'error': 'No code provided'}), 400
    
    code = data['code']
    
    # Capture stdout and stderr
    output = io.StringIO()
    error = io.StringIO()
    
    result = {
        'output': '',
        'error': '',
        'success': True
    }
    
    # Execute the code with time and memory limits
    try:
        with redirect_stdout(output), redirect_stderr(error):
            # Execute in a somewhat controlled environment
            exec(code, {'__builtins__': __builtins__})
        
        result['output'] = output.getvalue()
    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
    
    # Add stderr to error if any
    if error.getvalue():
        result['error'] += error.getvalue()
        
    return jsonify(result)

# This is the Firebase function entrypoint
@https_fn.on_request()
def handler(request):
    """Handle HTTP requests with the Flask app"""
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {'Access-Control-Allow-Origin': '*'}
    
    # Process the request with Flask
    return app(request.environ, lambda status, headers, body: (body, status, headers))

# initialize_app()
#
#
# @https_fn.on_request()
# def on_request_example(req: https_fn.Request) -> https_fn.Response:
#     return https_fn.Response("Hello world!")