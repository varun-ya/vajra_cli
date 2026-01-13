import os
import sys
import json
import importlib.util
from flask import Flask, request, jsonify
from google.cloud import storage

app = Flask(__name__)

def load_user_function():
    """Download and load user function from Cloud Storage"""
    bucket_name = os.environ.get('FUNCTION_BUCKET')
    function_path = os.environ.get('FUNCTION_PATH')
    
    if not bucket_name or not function_path:
        raise ValueError("Missing function configuration")
    
    # Download function code
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(function_path)
    
    # Extract and load function
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, 'function.zip')
        blob.download_to_filename(zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Load main.py
        spec = importlib.util.spec_from_file_location("user_function", 
                                                     os.path.join(temp_dir, "main.py"))
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        
        return user_module.handler

# Load function at startup
user_handler = load_user_function()

@app.route('/', methods=['POST'])
def execute_function():
    try:
        # Get request data
        data = request.get_json() or {}
        
        # Execute user function
        result = user_handler(data)
        
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))