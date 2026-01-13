def handler(event):
    """
    Example function - similar to AWS Lambda handler
    """
    name = event.get('name', 'World')
    return {
        'message': f'Hello {name}!',
        'event': event
    }