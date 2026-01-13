# Vajra CLI Quick Reference

## Quick Start
```bash
# 1. Authenticate
python3 vajra-cli.py init

# 2. Deploy a function
python3 vajra-cli.py deploy my-function ./src

# 3. List functions
python3 vajra-cli.py list

# 4. Invoke function
python3 vajra-cli.py invoke my-function --payload '{"key": "value"}'
```

## Command Summary

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Authenticate with platform | `python3 vajra-cli.py init` |
| `whoami` | Show current user | `python3 vajra-cli.py whoami` |
| `deploy <name> <path>` | Deploy function | `python3 vajra-cli.py deploy api ./src` |
| `list` | List all functions | `python3 vajra-cli.py list` |
| `details <name>` | Get function details | `python3 vajra-cli.py details api` |
| `invoke <name>` | Execute function | `python3 vajra-cli.py invoke api --payload '{}'` |
| `delete <name>` | Delete function | `python3 vajra-cli.py delete api` |

## Deploy Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--runtime` | Specify runtime | auto | `--runtime python3.11` |
| `--handler` | Entry point function | main | `--handler handler` |
| `--memory` | Memory in MB | 512 | `--memory 1024` |
| `--timeout` | Timeout in seconds | 30 | `--timeout 60` |
| `--description` | Function description | "" | `--description "API handler"` |

## Supported Runtimes

### Python
- `python3.8`, `python3.9`, `python3.10`, `python3.11`, `python3.12`

### Node.js
- `nodejs16`, `nodejs18`, `nodejs20`

### Go
- `go1.19`, `go1.20`, `go1.21`

### Java
- `java11`, `java17`, `java21`

### Others
- `rust1.70`
- `dotnet6`, `dotnet8`

## Common Workflows

### Deploy Python Function
```bash
# Create function directory
mkdir my-api && cd my-api

# Create main.py
cat > main.py << 'EOF'
def main(event, context):
    return {"message": "Hello World", "event": event}
EOF

# Create requirements.txt
echo "requests==2.31.0" > requirements.txt

# Deploy
python3 vajra-cli.py deploy my-api . --runtime python3.11
```

### Deploy Node.js Function
```bash
# Create function directory
mkdir my-service && cd my-service

# Create index.js
cat > index.js << 'EOF'
exports.main = (event, context) => {
    return {message: "Hello from Node.js", event: event};
};
EOF

# Create package.json
cat > package.json << 'EOF'
{
  "name": "my-service",
  "version": "1.0.0",
  "main": "index.js"
}
EOF

# Deploy
python3 vajra-cli.py deploy my-service . --runtime nodejs18
```

### Test Function
```bash
# Simple test
python3 vajra-cli.py invoke my-function

# Test with payload
python3 vajra-cli.py invoke my-function --payload '{"name": "John", "age": 30}'

# Test mode (with debugging)
python3 vajra-cli.py invoke my-function --payload '{"test": true}' --test
```

## Configuration Files

### Location
```
~/.vajra/
├── config.json    # User configuration
└── token          # Authentication token
```

### Sample config.json
```json
{
  "user_email": "user@example.com",
  "user_id": "user123",
  "authenticated_at": "2026-01-11T10:00:00"
}
```

## Troubleshooting

### Authentication Issues
```bash
# Re-authenticate
python3 vajra-cli.py init

# Check current user
python3 vajra-cli.py whoami
```

### Function Issues
```bash
# Check function status
python3 vajra-cli.py details my-function

# List all functions
python3 vajra-cli.py list
```

### Common Errors

| Error | Solution |
|-------|----------|
| "Not authenticated" | Run `python3 vajra-cli.py init` |
| "Function not found" | Check name with `python3 vajra-cli.py list` |
| "Unsupported runtime" | Use supported runtime version |
| "Deployment failed" | Check source directory and permissions |

## API Endpoint
```
https://vajra-api-gateway-635998496384.us-central1.run.app
```

## Support
- Check function details: `python3 vajra-cli.py details <name>`
- Verify authentication: `python3 vajra-cli.py whoami`
- Review documentation: `CLI_DOCUMENTATION.md`