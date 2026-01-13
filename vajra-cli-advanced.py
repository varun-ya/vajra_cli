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
    
    def deploy_function(self, name, path, runtime="python3.11", handler="main", 
                       memory=512, timeout=30, description="", env_vars=None):
        """Deploy function with advanced configuration"""
        print(f"🚀 Deploying function '{name}' with {runtime} runtime...")
        
        # Detect runtime if not specified
        if runtime == "auto":
            runtime = self.detect_runtime(path)
            print(f"📦 Detected runtime: {runtime}")
        
        # Create zip file with all files
        zip_path = f"{name}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, path)
                    zf.write(file_path, arc_path)
        
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
            print(f"✅ Function deployed successfully!")
            print(f"   Function ID: {result['function_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Version: {result['version']}")
            return result
        else:
            print(f"❌ Deployment failed: {response.text}")
            return None
    
    def invoke_function(self, name, payload=None, test_mode=False):
        """Invoke function with payload"""
        print(f"⚡ Invoking function '{name}'...")
        
        data = {
            "payload": payload or {},
            "test_mode": test_mode
        }
        
        start_time = time.time()
        response = requests.post(f"{self.api_base}/functions/{name}/invoke", 
                               json=data)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Function executed successfully!")
            print(f"   Result: {json.dumps(result['result'], indent=2)}")
            print(f"   Execution Time: {result.get('execution_time', 'N/A')}")
            print(f"   Memory Used: {result.get('memory_used', 'N/A')}")
            print(f"   Total Time: {(end_time - start_time)*1000:.2f}ms")
            return result
        else:
            print(f"❌ Invocation failed: {response.text}")
            return None
    
    def test_function(self, name, payload=None):
        """Test function in debug mode"""
        print(f"🧪 Testing function '{name}' in debug mode...")
        
        data = {
            "payload": payload or {},
            "test_mode": True
        }
        
        response = requests.post(f"{self.api_base}/functions/{name}/test", 
                               json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test completed successfully!")
            print(f"   Result: {json.dumps(result['result'], indent=2)}")
            print(f"   Debug Info: {json.dumps(result['debug'], indent=2)}")
            return result
        else:
            print(f"❌ Test failed: {response.text}")
            return None
    
    def list_functions(self):
        """List all functions"""
        response = requests.get(f"{self.api_base}/functions")
        
        if response.status_code == 200:
            result = response.json()
            functions = result['functions']
            
            print(f"📋 Found {len(functions)} functions:")
            print()
            
            for func in functions:
                print(f"  🔧 {func['name']}")
                print(f"     Runtime: {func['runtime']}")
                print(f"     Status: {func['status']}")
                print(f"     Invocations: {func['invocation_count']}")
                print(f"     Created: {func['created_at']}")
                if func['description']:
                    print(f"     Description: {func['description']}")
                print()
            
            return functions
        else:
            print(f"❌ Failed to list functions: {response.text}")
            return None
    
    def get_function_details(self, name):
        """Get detailed function information"""
        response = requests.get(f"{self.api_base}/functions/{name}")
        
        if response.status_code == 200:
            result = response.json()
            func = result['function']
            logs = result['logs']
            metrics = result['metrics']
            
            print(f"📊 Function Details: {name}")
            print("=" * 50)
            print(f"ID: {func['id']}")
            print(f"Runtime: {func['runtime']}")
            print(f"Handler: {func['handler']}")
            print(f"Memory: {func['memory']}MB")
            print(f"Timeout: {func['timeout']}s")
            print(f"Status: {func['status']}")
            print(f"Version: {func['version']}")
            print(f"Description: {func.get('description', 'N/A')}")
            print(f"Created: {func['created_at']}")
            print(f"Updated: {func['updated_at']}")
            print()
            
            print("📈 Metrics (24h):")
            print(f"  Invocations: {metrics['invocations_24h']}")
            print(f"  Errors: {metrics['errors_24h']}")
            print(f"  Success Rate: {metrics['success_rate']}")
            print(f"  Avg Duration: {metrics['avg_duration']}")
            print(f"  Avg Memory: {metrics['avg_memory']}")
            print()
            
            print("📝 Recent Logs:")
            for log in logs[:5]:
                print(f"  [{log['timestamp']}] {log['level']}: {log['message']}")
            print()
            
            return result
        else:
            print(f"❌ Failed to get function details: {response.text}")
            return None
    
    def get_logs(self, name, limit=50):
        """Get function logs"""
        response = requests.get(f"{self.api_base}/functions/{name}/logs?limit={limit}")
        
        if response.status_code == 200:
            result = response.json()
            logs = result['logs']
            
            print(f"📝 Logs for function '{name}' (last {len(logs)} entries):")
            print()
            
            for log in logs:
                print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
                if 'execution_time' in log:
                    print(f"    Execution Time: {log['execution_time']}")
                if 'memory_used' in log:
                    print(f"    Memory Used: {log['memory_used']}")
                print()
            
            return logs
        else:
            print(f"❌ Failed to get logs: {response.text}")
            return None
    
    def detect_runtime(self, path):
        """Auto-detect runtime based on files"""
        if os.path.exists(os.path.join(path, "package.json")):
            return "nodejs18"
        elif os.path.exists(os.path.join(path, "go.mod")):
            return "go1.21"
        elif os.path.exists(os.path.join(path, "pom.xml")):
            return "java17"
        elif os.path.exists(os.path.join(path, "main.py")):
            return "python3.11"
        else:
            return "python3.11"  # default

def main():
    parser = argparse.ArgumentParser(description='Vajra Serverless CLI')
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
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test a function')
    test_parser.add_argument('name', help='Function name')
    test_parser.add_argument('--payload', help='JSON payload')
    
    # List command
    subparsers.add_parser('list', help='List all functions')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get function details')
    info_parser.add_argument('name', help='Function name')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Get function logs')
    logs_parser.add_argument('name', help='Function name')
    logs_parser.add_argument('--limit', type=int, default=50, help='Number of log entries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = VajraCLI()
    
    if args.command == 'deploy':
        env_vars = {}
        cli.deploy_function(args.name, args.path, args.runtime, args.handler,
                          args.memory, args.timeout, args.description, env_vars)
    
    elif args.command == 'invoke':
        payload = json.loads(args.payload) if args.payload else {}
        cli.invoke_function(args.name, payload)
    
    elif args.command == 'test':
        payload = json.loads(args.payload) if args.payload else {}
        cli.test_function(args.name, payload)
    
    elif args.command == 'list':
        cli.list_functions()
    
    elif args.command == 'info':
        cli.get_function_details(args.name)
    
    elif args.command == 'logs':
        cli.get_logs(args.name, args.limit)

if __name__ == "__main__":
    main()