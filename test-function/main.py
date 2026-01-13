def main(event, context):
    """Simple hello world function"""
    name = event.get('name', 'World')
    return {
        'message': f'Hello {name}!',
        'timestamp': '2026-01-11T11:05:00Z',
        'function': 'hello-world-test'
    }

if __name__ == "__main__":
    # Test locally
    result = main({'name': 'Vajra'}, {})
    print(result)