# Vajra Serverless Platform CLI Documentation

## Overview

The Vajra CLI is a command-line interface for managing serverless functions on the Vajra Serverless Platform. It provides comprehensive functionality for deploying, managing, and monitoring serverless functions across multiple runtimes.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd vajra-serverless

# Install dependencies
pip install requests

# Make CLI executable
chmod +x vajra-cli.py
```

## Authentication

Before using any commands, you must authenticate with the Vajra platform:

```bash
python3 vajra-cli.py init
```

This will prompt you to enter your email address and establish authentication with the platform.

## Commands Reference

### Authentication Commands

#### `init`
Initialize and authenticate with the Vajra platform.

```bash
python3 vajra-cli.py init
```

**Example:**
```bash
$ python3 vajra-cli.py init
Enter your email address: user@example.com
Successfully authenticated as user@example.com
```

#### `whoami`
Display current authenticated user information.

```bash
python3 vajra-cli.py whoami
```

**Output:**
- Email address
- User ID
- Authentication status
- Authentication timestamp

### Function Management Commands

#### `deploy`
Deploy a function to the Vajra platform.

```bash
python3 vajra-cli.py deploy <function-name> <source-path> [options]
```

**Arguments:**
- `function-name`: Unique name for your function
- `source-path`: Path to directory containing function code

**Options:**
- `--runtime <runtime>`: Specify runtime (default: auto-detect)
- `--handler <handler>`: Entry point function (default: main)
- `--memory <mb>`: Memory allocation in MB (default: 512)
- `--timeout <seconds>`: Timeout in seconds (default: 30)
- `--description <text>`: Function description

**Supported Runtimes:**
- `python3.8`, `python3.9`, `python3.10`, `python3.11`, `python3.12`
- `nodejs16`, `nodejs18`, `nodejs20`
- `go1.19`, `go1.20`, `go1.21`
- `java11`, `java17`, `java21`
- `rust1.70`
- `dotnet6`, `dotnet8`

**Examples:**
```bash
# Deploy with auto-detected runtime
python3 vajra-cli.py deploy my-function ./src

# Deploy Python function with specific configuration
python3 vajra-cli.py deploy api-handler ./api --runtime python3.11 --memory 1024 --timeout 60

# Deploy Node.js function with description
python3 vajra-cli.py deploy webhook ./webhook --runtime nodejs18 --description "GitHub webhook handler"
```

#### `list`
List all deployed functions for the authenticated user.

```bash
python3 vajra-cli.py list
```

**Output includes:**
- Function name
- Runtime
- Status (deploying, deployed, failed)
- Version
- Invocation count
- Creation timestamp
- Description

#### `details`
Get detailed information about a specific function.

```bash
python3 vajra-cli.py details <function-name>
```

**Output includes:**
- Function metadata
- Runtime configuration
- Performance metrics
- Recent execution logs

**Example:**
```bash
python3 vajra-cli.py details my-api-function
```

#### `invoke`
Execute a function with optional payload.

```bash
python3 vajra-cli.py invoke <function-name> [options]
```

**Options:**
- `--payload <json>`: JSON payload to send to function
- `--test`: Enable test mode for debugging

**Examples:**
```bash
# Simple invocation
python3 vajra-cli.py invoke hello-world

# Invocation with payload
python3 vajra-cli.py invoke user-service --payload '{"user_id": 123, "action": "get_profile"}'

# Test mode invocation
python3 vajra-cli.py invoke data-processor --payload '{"data": [1,2,3]}' --test
```

#### `delete`
Delete a function and all associated resources.

```bash
python3 vajra-cli.py delete <function-name> [options]
```

**Options:**
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation
python3 vajra-cli.py delete old-function

# Force delete without confirmation
python3 vajra-cli.py delete temp-function --force
```

## Function Development Guide

### Directory Structure

Your function directory should contain:

```
my-function/
├── main.py          # Entry point (Python)
├── requirements.txt # Dependencies (Python)
└── README.md       # Documentation
```

### Function Handler

#### Python Example
```python
def main(event, context):
    """
    Function entry point
    
    Args:
        event: Input payload
        context: Execution context
    
    Returns:
        dict: Response data
    """
    name = event.get('name', 'World')
    return {
        'message': f'Hello {name}!',
        'timestamp': context.get('timestamp')
    }
```

#### Node.js Example
```javascript
exports.main = (event, context) => {
    const name = event.name || 'World';
    return {
        message: `Hello ${name}!`,
        timestamp: context.timestamp
    };
};
```

### Environment Variables

Set environment variables during deployment:

```bash
python3 vajra-cli.py deploy my-function ./src --env '{"API_KEY": "secret", "DEBUG": "true"}'
```

## Configuration

### Configuration Files

The CLI stores configuration in `~/.vajra/`:

```
~/.vajra/
├── config.json    # User configuration
└── token          # Authentication token
```

### Configuration Options

Edit `~/.vajra/config.json`:

```json
{
  "user_email": "user@example.com",
  "user_id": "user123",
  "authenticated_at": "2026-01-11T10:00:00",
  "default_runtime": "python3.11",
  "default_memory": 512,
  "default_timeout": 30
}
```

## Error Handling

### Common Errors

#### Authentication Errors
```
Error: Not authenticated. Please run 'vajra init' first.
```
**Solution:** Run `python3 vajra-cli.py init`

#### Deployment Errors
```
Error: Unsupported runtime: python3.13
```
**Solution:** Use a supported runtime version

#### Function Not Found
```
Error: Function 'my-function' not found
```
**Solution:** Verify function name with `python3 vajra-cli.py list`

### Debug Mode

Enable verbose output by setting environment variable:

```bash
export VAJRA_DEBUG=1
python3 vajra-cli.py deploy my-function ./src
```

## Best Practices

### Function Development
1. Keep functions small and focused
2. Use appropriate memory allocation
3. Set reasonable timeouts
4. Include error handling
5. Add comprehensive logging

### Deployment
1. Test functions locally before deployment
2. Use descriptive function names
3. Include meaningful descriptions
4. Version your function code
5. Monitor function performance

### Security
1. Never include secrets in function code
2. Use environment variables for configuration
3. Implement proper input validation
4. Follow principle of least privilege

## API Integration

The CLI communicates with the Vajra API at:
```
https://vajra-api-gateway-635998496384.us-central1.run.app
```

### Direct API Usage

You can also interact directly with the API:

```bash
# List functions
curl -H "Authorization: Bearer user:your-email@example.com" \
     https://vajra-api-gateway-635998496384.us-central1.run.app/functions

# Invoke function
curl -X POST \
     -H "Authorization: Bearer user:your-email@example.com" \
     -H "Content-Type: application/json" \
     -d '{"payload": {"name": "World"}, "test_mode": true}' \
     https://vajra-api-gateway-635998496384.us-central1.run.app/functions/my-function/invoke
```

## Troubleshooting

### Connection Issues
- Verify internet connectivity
- Check API endpoint availability
- Ensure authentication token is valid

### Deployment Issues
- Verify source code directory exists
- Check file permissions
- Ensure all dependencies are listed
- Validate function handler exists

### Runtime Issues
- Check function logs for errors
- Verify payload format
- Test with smaller payloads
- Monitor memory usage

## Support

For additional support:
1. Check function logs: `python3 vajra-cli.py details <function-name>`
2. Review API documentation
3. Verify authentication status: `python3 vajra-cli.py whoami`
4. Test with simple functions first

## Version Information

- CLI Version: 3.0.0
- API Version: v3
- Supported Platforms: macOS, Linux, Windows
- Python Requirements: 3.8+