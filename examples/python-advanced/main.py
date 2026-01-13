import json
import os
from datetime import datetime

def main(event):
    """
    Advanced Python function with logging and error handling
    """
    try:
        # Get environment variables
        env = os.environ.get('ENVIRONMENT', 'production')
        
        # Process event data
        name = event.get('name', 'World')
        operation = event.get('operation', 'greet')
        
        if operation == 'greet':
            result = {
                'message': f'Hello {name}!',
                'timestamp': datetime.utcnow().isoformat(),
                'environment': env,
                'runtime': 'python3.11'
            }
        elif operation == 'calculate':
            a = event.get('a', 0)
            b = event.get('b', 0)
            result = {
                'operation': 'add',
                'result': a + b,
                'inputs': {'a': a, 'b': b}
            }
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'type': type(e).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }