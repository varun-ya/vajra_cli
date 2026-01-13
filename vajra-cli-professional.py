#!/usr/bin/env python3

import requests
import zipfile
import os
import sys
import json
import time
from datetime import datetime
import argparse

API_BASE = "https://vajra-api-gateway-635998496384.us-central1.run.app"

class VajraCLI:
    def __init__(self):
        self.api_base = API_BASE
    
    def print_banner(self):
        """Print Vajra CLI banner"""
        banner = """
╭─────────────────────────────────────────────────────────────────╮
│                                                                 │
│  ██╗   ██╗ █████╗      ██╗██████╗  █████╗     ██████╗██╗     ██╗│
│  ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗   ██╔════╝██║     ██║│
│  ██║   ██║███████║     ██║██████╔╝███████║   ██║     ██║     ██║│
│  ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║   ██║     ██║     ██║│
│   ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║   ╚██████╗███████╗██║│
│    ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝╚══════╝╚═╝│
│                                                                 │
│                 Vajra Serverless Platform CLI                  │
│                     Enterprise Edition v3.0                    │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
        """
        print(banner)
    
    def print_section(self, title):
        """Print section header"""
        print(f"\n┌─ {title} " + "─" * (60 - len(title)) + "┐")
    
    def print_end_section(self):
        """Print section footer"""
        print("└" + "─" * 62 + "┘")
    
    def print_status(self, status, message):
        """Print status message"""
        symbols = {
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ',
            'progress': '→'
        }
        symbol = symbols.get(status, '•')
        print(f"  {symbol} {message}")
    
    def deploy_function(self, name, path, runtime="python3.11", handler="main", 
                       memory=512, timeout=30, description="", env_vars=None):
        """Deploy function with advanced configuration"""
        self.print_section("FUNCTION DEPLOYMENT")
        
        print(f"  Function Name    : {name}")
        print(f"  Runtime          : {runtime}")
        print(f"  Handler          : {handler}")
        print(f"  Memory           : {memory}MB")
        print(f"  Timeout          : {timeout}s")
        print(f"  Source Path      : {path}")
        
        # Detect runtime if not specified
        if runtime == "auto":
            runtime = self.detect_runtime(path)
            self.print_status('info', f"Auto-detected runtime: {runtime}")
        
        self.print_status('progress', "Creating deployment package...")
        
        # Create zip file with all files
        zip_path = f"{name}.zip"
        file_count = 0
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, path)
                    zf.write(file_path, arc_path)
                    file_count += 1
        
        self.print_status('info', f"Packaged {file_count} files")
        self.print_status('progress', "Uploading to Vajra platform...")
        
        # Prepare form data
        with open(zip_path, 'rb') as f:
            files = {'code': (zip_path, f, 'application/zip')}
            data = {
                'name': name,
                'runtime': runtime,
                'handler': handler,
                'memory': memory,
                'timeout': timeout,
                'description': description,
                'environment': json.dumps(env_vars or {})
            }
            
            response = requests.post(f"{self.api_base}/functions", 
                                   files=files, data=data)
        
        os.remove(zip_path)
        
        if response.status_code == 200:
            result = response.json()
            self.print_status('success', "Function deployed successfully")
            print(f"  Function ID      : {result['function_id']}")
            print(f"  Status           : {result['status']}")
            print(f"  Version          : {result['version']}")
            self.print_end_section()
            return result
        else:
            self.print_status('error', f"Deployment failed: {response.text}")
            self.print_end_section()
            return None
    
    def invoke_function(self, name, payload=None, test_mode=False):
        """Invoke function with payload"""
        self.print_section("FUNCTION INVOCATION")
        
        print(f"  Function Name    : {name}")
        print(f"  Test Mode        : {'Yes' if test_mode else 'No'}")
        print(f"  Payload Size     : {len(json.dumps(payload or {}))} bytes")
        
        data = {
            "payload": payload or {},
            "test_mode": test_mode
        }
        
        self.print_status('progress', "Invoking function...")
        start_time = time.time()
        response = requests.post(f"{self.api_base}/functions/{name}/invoke", 
                               json=data)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            self.print_status('success', "Function executed successfully")
            print(f"  Execution Time   : {result.get('execution_time', 'N/A')}")
            print(f"  Memory Used      : {result.get('memory_used', 'N/A')}")
            print(f"  Total Latency    : {(end_time - start_time)*1000:.2f}ms")
            print(f"  Result           :")
            print(f"    {json.dumps(result['result'], indent=4)}")
            self.print_end_section()
            return result
        else:
            self.print_status('error', f"Invocation failed: {response.text}")
            self.print_end_section()
            return None
    
    def list_functions(self):
        """List all functions"""
        self.print_section("FUNCTION INVENTORY")
        
        response = requests.get(f"{self.api_base}/functions")
        
        if response.status_code == 200:
            result = response.json()
            functions = result['functions']
            
            if not functions:
                self.print_status('info', "No functions found")
                self.print_end_section()
                return []
            
            print(f"  Total Functions  : {len(functions)}")
            print(f"  Storage Source   : {result.get('source', 'unknown')}")
            print()
            # Table header
            print("  ┌─" + "─" * 20 + "┬─" + "─" * 12 + "┬─" + "─" * 10 + "┬─" + "─" * 8 + "┬─" + "─" * 12 + "┐")
            print("  │ Function Name    │ Runtime      │ Status     │ Version  │ Invocations  │")
            print("  ├─" + "─" * 20 + "┼─" + "─" * 12 + "┼─" + "─" * 10 + "┼─" + "─" * 8 + "┼─" + "─" * 12 + "┤")
            
            for func in functions:
                name = func['name'][:18] + '..' if len(func['name']) > 20 else func['name']
                runtime = func['runtime'][:10] + '..' if len(func['runtime']) > 12 else func['runtime']
                status = func['status'][:8] + '..' if len(func['status']) > 10 else func['status']
                version = str(func['version'])
                invocations = str(func['invocation_count'])
                
                print(f"  │ {name:<20} │ {runtime:<12} │ {status:<10} │ {version:<8} │ {invocations:<12} │")
            
            print("  └─" + "─" * 20 + "┴─" + "─" * 12 + "┴─" + "─" * 10 + "┴─" + "─" * 8 + "┴─" + "─" * 12 + "┘")
            
            self.print_end_section()
            return functions
        else:
            self.print_status('error', f"Failed to list functions: {response.text}")
            self.print_end_section()
            return None
    
    def get_function_details(self, name):
        """Get detailed function information"""
        response = requests.get(f"{self.api_base}/functions/{name}")
        
        if response.status_code == 200:
            result = response.json()
            func = result['function']
            logs = result['logs']
            metrics = result['metrics']
            
            self.print_section(f"FUNCTION DETAILS: {name.upper()}")
            
            # Function Configuration
            print("  Configuration:")
            print(f"    Function ID      : {func['id']}")
            print(f"    Runtime          : {func['runtime']}")
            print(f"    Handler          : {func['handler']}")
            print(f"    Memory           : {func['memory']}MB")
            print(f"    Timeout          : {func['timeout']}s")
            print(f"    Status           : {func['status']}")
            print(f"    Version          : {func['version']}")
            print(f"    Description      : {func.get('description', 'N/A')}")
            print(f"    Created          : {func['created_at']}")
            print(f"    Updated          : {func['updated_at']}")
            
            # Metrics
            print("\n  Performance Metrics (24h):")
            print(f"    Invocations      : {metrics['invocations_24h']}")
            print(f"    Errors           : {metrics['errors_24h']}")
            print(f"    Success Rate     : {metrics['success_rate']}")
            print(f"    Avg Duration     : {metrics['avg_duration']}")
            print(f"    Avg Memory       : {metrics['avg_memory']}")
            
            # Recent Logs
            print("\n  Recent Logs:")
            for log in logs[:5]:
                timestamp = log['timestamp'][:19].replace('T', ' ')
                print(f"    [{timestamp}] {log['level']}: {log['message']}")
            
            self.print_end_section()
            return result
        else:
            self.print_status('error', f"Failed to get function details: {response.text}")
            return None
    
    def delete_function(self, name, force=False):
        """Delete a function"""
        self.print_section(f"FUNCTION DELETION: {name.upper()}")
        
        if not force:
            confirm = input(f"  Are you sure you want to delete function '{name}'? (y/N): ")
            if confirm.lower() != 'y':
                self.print_status('info', "Deletion cancelled")
                self.print_end_section()
                return None
        
        self.print_status('progress', "Deleting function...")
        
        params = {'force': 'true'} if force else {}
        response = requests.delete(f"{self.api_base}/functions/{name}", params=params)
        
        if response.status_code == 200:
            result = response.json()
            self.print_status('success', "Function deleted successfully")
            print(f"  Deleted At       : {result['deleted_at']}")
            print(f"  Resources Cleaned:")
            for resource in result['resources_cleaned']:
                print(f"    - {resource}")
            self.print_end_section()
            return result
        else:
            self.print_status('error', f"Deletion failed: {response.text}")
            self.print_end_section()
            return None
    
    def detect_runtime(self, path):
        """Auto-detect runtime based on files"""
        if os.path.exists(os.path.join(path, "package.json")):
            return "nodejs18"
        elif os.path.exists(os.path.join(path, "go.mod")):
            return "go1.21"
        elif os.path.exists(os.path.join(path, "pom.xml")):
            return "java17"
        elif os.path.exists(os.path.join(path, "Cargo.toml")):
            return "rust1.70"
        elif os.path.exists(os.path.join(path, "main.py")):
            return "python3.11"
        else:
            return "python3.11"  # default

def main():
    cli = VajraCLI()
    
    parser = argparse.ArgumentParser(
        description='Vajra Serverless Platform CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vajra deploy my-function ./src --runtime python3.11 --memory 512
  vajra invoke my-function --payload '{"name": "world"}'
  vajra list
  vajra info my-function
  vajra delete my-function
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a function')
    deploy_parser.add_argument('name', help='Function name')
    deploy_parser.add_argument('path', help='Function code path')
    deploy_parser.add_argument('--runtime', default='auto', help='Runtime (auto, python3.11, nodejs18, etc.)')
    deploy_parser.add_argument('--handler', default='main', help='Handler function name')
    deploy_parser.add_argument('--memory', type=int, default=512, help='Memory in MB')
    deploy_parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    deploy_parser.add_argument('--description', default='', help='Function description')
    
    # Invoke command
    invoke_parser = subparsers.add_parser('invoke', help='Invoke a function')
    invoke_parser.add_argument('name', help='Function name')
    invoke_parser.add_argument('--payload', help='JSON payload')
    invoke_parser.add_argument('--test', action='store_true', help='Enable test mode')
    
    # List command
    subparsers.add_parser('list', help='List all functions')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get function details')
    info_parser.add_argument('name', help='Function name')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a function')
    delete_parser.add_argument('name', help='Function name')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if not args.command:
        cli.print_banner()
        parser.print_help()
        return
    
    if args.command == 'version':
        cli.print_banner()
        return
    
    if args.command == 'deploy':
        env_vars = {}
        cli.deploy_function(args.name, args.path, args.runtime, args.handler,
                          args.memory, args.timeout, args.description, env_vars)
    
    elif args.command == 'invoke':
        payload = json.loads(args.payload) if args.payload else {}
        cli.invoke_function(args.name, payload, args.test)
    
    elif args.command == 'list':
        cli.list_functions()
    
    elif args.command == 'info':
        cli.get_function_details(args.name)
    
    elif args.command == 'delete':
        cli.delete_function(args.name, args.force)

if __name__ == "__main__":
    main()