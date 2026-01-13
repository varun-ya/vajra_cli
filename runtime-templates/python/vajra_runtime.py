import os
import sys
import json
import importlib.util
import traceback
from flask import Flask, request, jsonify
from google.cloud import logging as cloud_logging

app = Flask(__name__)

# Initialize logging
logging_client = cloud_logging.Client()
logger = logging_client.logger("vajra-function")

def load_user_function():
    """Load user function dynamically"""
    handler = os.environ.get('FUNCTION_TARGET', 'main')
    
    try:
        # Import main module
        if os.path.exists('main.py'):
            spec = importlib.util.spec_from_file_location("main", "main.py")
            main_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_module)
            
            # Get handler function
            if hasattr(main_module, handler):
                return getattr(main_module, handler)
            else:
                raise AttributeError(f"Handler '{handler}' not found in main.py")
        else:
            raise FileNotFoundError("main.py not found")
            
    except Exception as e:
        logger.log_struct({
            "message": f"Failed to load function: {str(e)}",
            "level": "ERROR",
            "traceback": traceback.format_exc()
        })
        raise

# Load function at startup
try:
    user_function = load_user_function()
    logger.log_struct({"message": "Function loaded successfully", "level": "INFO"})
except Exception as e:
    logger.log_struct({"message": f"Startup failed: {str(e)}", "level": "ERROR"})
    user_function = None

@app.route('/', methods=['POST', 'GET'])
def execute_function():
    if not user_function:
        return jsonify({"error": "Function not loaded"}), 500
    
    start_time = time.time()
    
    try:
        # Get request data
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = dict(request.args)
        
        # Log invocation
        logger.log_struct({
            "message": "Function invoked",
            "method": request.method,
            "payload_size": len(json.dumps(data))
        })
        
        # Execute user function
        result = user_function(data)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log success
        logger.log_struct({
            "message": "Function executed successfully",
            "execution_time_ms": execution_time,
            "level": "INFO"
        })
        
        return jsonify({
            "result": result,
            "execution_time": f"{execution_time:.2f}ms"
        })
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        # Log error
        logger.log_struct({
            "message": f"Function execution failed: {error_msg}",
            "execution_time_ms": execution_time,
            "level": "ERROR",
            "traceback": traceback.format_exc()
        })
        
        return jsonify({
            "error": error_msg,
            "execution_time": f"{execution_time:.2f}ms"
        }), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "function_loaded": user_function is not None})

if __name__ == '__main__':
    import time
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)