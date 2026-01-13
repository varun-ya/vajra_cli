#!/usr/bin/env python3

import requests
import zipfile
import os
import sys
import json
import time
import argparse
import webbrowser
import threading
import http.server
import socketserver
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

API_BASE = "https://vajra-api-gateway-635998496384.us-central1.run.app"
CONFIG_DIR = Path.home() / ".vajra"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "token"

class VajraCLI:
    def __init__(self):
        self.api_base = API_BASE
        self.config = self.load_config()
        self.token = self.load_token()
    
    def load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config):
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def load_token(self):
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                return f.read().strip()
        return None
    
    def save_token(self, token):
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        os.chmod(TOKEN_FILE, 0o600)
        self.token = token
    
    def get_auth_headers(self):
        if not self.token:
            raise Exception("Not authenticated. Run 'vajra init' first.")
        return {"Authorization": f"Bearer {self.token}"}
    
    def print_banner(self):
        banner = """
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ██╗   ██╗ █████╗      ██╗██████╗  █████╗     ██████╗██╗     ██╗│
│  ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗   ██╔════╝██║     ██║│
│  ██║   ██║███████║     ██║██████╔╝███████║   ██║     ██║     ██║│
│  ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║   ██║     ██║     ██║│
│   ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║   ╚██████╗███████╗██║│
│    ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝╚══════╝╚═╝│
│                                                                 │
│                 Vajra Serverless Platform CLI                   │
│                     Enterprise Edition v3.0                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
        """
        print(banner)
    
    def print_section(self, title):
        print(f"\n┌─ {title} " + "─" * (60 - len(title)) + "┐")
    
    def print_end_section(self):
        print("└" + "─" * 62 + "┘")
    
    def print_status(self, status, message):
        symbols = {
            'success': '[OK]',
            'error': '[ERROR]',
            'warning': '[WARN]',
            'info': '[INFO]',
            'progress': '[PROGRESS]'
        }
        symbol = symbols.get(status, '[INFO]')
        print(f"  {symbol} {message}")
    
    def check_auth(self):
        """Check if current token is valid"""
        if not self.token:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/auth/user", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def init_auth(self):
        self.print_section("AUTHENTICATION")
        
        # Check if already authenticated
        if self.token and self.check_auth():
            print("  User already authenticated:")
            print(f"  Email: {self.config.get('user_email', 'Unknown')}")
            print(f"  User ID: {self.config.get('user_id', 'Unknown')}")
            print(f"  Auth Method: {self.config.get('auth_method', 'Unknown')}")
            print()
            
            choice = input("  Continue with current account? (y/n): ").strip().lower()
            if choice == 'y':
                self.print_status('info', "Using existing authentication")
                self.print_end_section()
                return True
            else:
                print("  Logging out current user...")
                self.logout()
        
        print("  Secure OAuth Authentication")
        print("  This will open your browser for Google authentication.")
        print()
        
        return self.oauth_auth()
        
    def logout(self):
        """Logout and clear authentication"""
        self.print_section("LOGOUT")
        
        if not self.token:
            self.print_status('info', "No active session found")
            self.print_end_section()
            return True
        
        print(f"  Current User: {self.config.get('user_email', 'Unknown')}")
        confirm = input("  Confirm logout? (y/n): ").strip().lower()
        
        if confirm != 'y':
            self.print_status('info', "Logout cancelled")
            self.print_end_section()
            return False
        
        try:
            if TOKEN_FILE.exists():
                TOKEN_FILE.unlink()
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            self.token = None
            self.config = {}
            
            self.print_status('success', "Successfully logged out")
            self.print_end_section()
            return True
        except Exception as e:
            self.print_status('error', f"Error during logout: {str(e)}")
            self.print_end_section()
            return False
    
    def dev_auth(self):
        """Simple development authentication"""
        print("\n  Development Authentication:")
        email = input("  Enter your email: ").strip()
        
        if not email or "@" not in email:
            self.print_status('error', "Invalid email address")
            self.print_end_section()
            return False
        
        token = f"user:{email}"
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.api_base}/auth/user", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                self.save_token(token)
                
                config = {
                    "user_email": email,
                    "user_id": user_info['user']['user_id'],
                    "authenticated_at": datetime.now().isoformat(),
                    "auth_method": "development"
                }
                self.save_config(config)
                
                self.print_status('success', f"Authenticated as {email}")
                self.print_end_section()
                return True
            else:
                self.print_status('error', f"Authentication failed: {response.text}")
                self.print_end_section()
                return False
                
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
            self.print_end_section()
            return False
    
    def oauth_auth(self):
        """OAuth browser-based authentication"""
        print("\n  Secure OAuth Authentication:")
        print("  This will open your browser for Google authentication.")
        print()
        try:
            # Get OAuth URL from server
            response = requests.get(f"{self.api_base}/auth/oauth/url")
            if response.status_code != 200:
                self.print_status('error', f"Failed to get OAuth URL: {response.text}")
                self.print_end_section()
                return False
            
            oauth_data = response.json()
            oauth_url = oauth_data["oauth_url"]
            state = oauth_data["state"]
            
            # Start local callback server on port 8080
            callback_result = {"token": None, "user": None, "error": None}
            api_base = self.api_base
            
            class CallbackHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path.startswith('/callback'):
                        parsed = urlparse(self.path)
                        params = parse_qs(parsed.query)
                        
                        if 'code' in params and 'state' in params:
                            code = params['code'][0]
                            callback_state = params['state'][0]
                            
                            try:
                                callback_response = requests.get(
                                    f"{api_base}/auth/oauth/callback?code={code}&state={callback_state}"
                                )
                                
                                if callback_response.status_code == 200:
                                    auth_data = callback_response.json()
                                    callback_result["token"] = auth_data["token"]
                                    callback_result["user"] = auth_data["user"]
                                    
                                    self.send_response(200)
                                    self.send_header('Content-type', 'text/html')
                                    self.end_headers()
                                    self.wfile.write(b'''
                                    <!DOCTYPE html>
                                    <html><head><title>Vajra CLI</title></head>
                                    <body style="margin:0;padding:0;background:#000;color:#fff;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;height:100vh;display:flex;align-items:center;justify-content:center">
                                    <div style="max-width:480px;padding:48px;text-align:center">
                                    <h1 style="margin:0 0 24px 0;font-size:24px;font-weight:600;letter-spacing:-0.025em">Authentication Successful</h1>
                                    <p style="margin:0 0 16px 0;font-size:16px;color:#888;line-height:1.5">You have been successfully authenticated with Vajra CLI.</p>
                                    <p style="margin:0;font-size:14px;color:#666">You can close this window and return to the terminal.</p>
                                    </div>
                                    <script>setTimeout(() => window.close(), 2000);</script>
                                    </body></html>
                                    ''')
                                else:
                                    callback_result["error"] = f"Authentication failed: {callback_response.text}"
                                    self.send_response(400)
                                    self.send_header('Content-type', 'text/html')
                                    self.end_headers()
                                    self.wfile.write(b'''
                                    <!DOCTYPE html>
                                    <html><head><title>Vajra CLI</title></head>
                                    <body style="margin:0;padding:0;background:#000;color:#fff;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;height:100vh;display:flex;align-items:center;justify-content:center">
                                    <div style="max-width:480px;padding:48px;text-align:center">
                                    <h1 style="margin:0 0 24px 0;font-size:24px;font-weight:600;letter-spacing:-0.025em">Authentication Failed</h1>
                                    <p style="margin:0 0 16px 0;font-size:16px;color:#888;line-height:1.5">There was an error during authentication.</p>
                                    <p style="margin:0;font-size:14px;color:#666">Please try again or contact support.</p>
                                    </div>
                                    </body></html>
                                    ''')
                            except Exception as e:
                                callback_result["error"] = f"Error: {str(e)}"
                                self.send_response(500)
                                self.send_header('Content-type', 'text/html')
                                self.end_headers()
                                self.wfile.write(b'<html><body><h2>Error</h2></body></html>')
                        else:
                            callback_result["error"] = "Invalid parameters"
                            self.send_response(400)
                            self.send_header('Content-type', 'text/html')
                            self.end_headers()
                            self.wfile.write(b'<html><body><h2>Invalid Request</h2></body></html>')
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    pass
            
            # Start server on port 8080
            with socketserver.TCPServer(("", 8080), CallbackHandler) as httpd:
                print(f"  Starting callback server on port 8080...")
                print(f"  Opening browser for authentication...")
                print(f"  If browser doesn't open, visit: {oauth_url}")
                print()
                
                # Open browser
                webbrowser.open(oauth_url)
                
                # Wait for callback
                timeout = 300
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    httpd.handle_request()
                    if callback_result["token"] or callback_result["error"]:
                        break
                    time.sleep(0.1)
                
                if callback_result["error"]:
                    self.print_status('error', callback_result["error"])
                    self.print_end_section()
                    return False
                elif callback_result["token"]:
                    self.save_token(callback_result["token"])
                    
                    user_info = callback_result["user"]
                    config = {
                        "user_email": user_info["email"],
                        "user_id": user_info["user_id"],
                        "authenticated_at": datetime.now().isoformat(),
                        "auth_method": "oauth"
                    }
                    self.save_config(config)
                    
                    self.print_status('success', f"Authenticated as {user_info['email']}")
                    self.print_end_section()
                    return True
                else:
                    self.print_status('error', "Authentication timeout")
                    self.print_end_section()
                    return False
                    
        except Exception as e:
            self.print_status('error', f"OAuth error: {str(e)}")
            self.print_end_section()
            return False
    
    def whoami(self):
        if not self.check_auth():
            return
        
        self.print_section("USER INFORMATION")
        
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_base}/auth/user", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                user = user_info['user']
                
                print(f"  Email: {user['email']}")
                print(f"  User ID: {user['user_id']}")
                print(f"  Status: Authenticated")
                
                if 'authenticated_at' in self.config:
                    print(f"  Authenticated: {self.config['authenticated_at']}")
                
            else:
                self.print_status('error', "Failed to get user information")
                
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        
        self.print_end_section()
    
    def deploy_function(self, name, path, runtime="python3.11", handler="main", 
                       memory=512, timeout=30, description="", env_vars=None):
        if not self.check_auth():
            return None
            
        self.print_section("FUNCTION DEPLOYMENT")
        
        print(f"  Function Name    : {name}")
        print(f"  Runtime          : {runtime}")
        print(f"  Handler          : {handler}")
        print(f"  Memory           : {memory}MB")
        print(f"  Timeout          : {timeout}s")
        print(f"  Source Path      : {path}")
        print(f"  User             : {self.config.get('user_email', 'Unknown')}")
        
        if runtime == "auto":
            runtime = self.detect_runtime(path)
            self.print_status('info', f"Auto-detected runtime: {runtime}")
        
        self.print_status('progress', "Installing dependencies...")
        
        # Create temporary directory for packaging
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = os.path.join(temp_dir, "package")
            os.makedirs(package_dir)
            
            # Copy source files
            if os.path.isfile(path):
                shutil.copy2(path, package_dir)
            else:
                shutil.copytree(path, package_dir, dirs_exist_ok=True)
            
            # Install dependencies based on runtime
            if runtime.startswith("python"):
                self._install_python_deps(package_dir)
            elif runtime.startswith("nodejs"):
                self._install_nodejs_deps(package_dir)
            
            self.print_status('progress', "Creating deployment package...")
            
            # Create zip with all dependencies
            zip_path = f"{name}.zip"
            file_count = 0
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, package_dir)
                        zf.write(file_path, arc_path)
                        file_count += 1
        
        self.print_status('info', f"Packaged {file_count} files with dependencies")
        self.print_status('progress', "Uploading to Vajra platform...")
        
        try:
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
                
                headers = self.get_auth_headers()
                response = requests.post(f"{self.api_base}/functions", 
                                       files=files, data=data, headers=headers)
            
            os.remove(zip_path)
            
            if response.status_code == 200:
                result = response.json()
                self.print_status('success', f"Function deployed successfully!")
                print(f"  Function ID: {result['function_id']}")
                print(f"  Status: {result['status']}")
                print(f"  Version: {result['version']}")
                self.print_end_section()
                return result
            else:
                self.print_status('error', f"Deployment failed: {response.text}")
                self.print_end_section()
                return None
                
        except Exception as e:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            self.print_status('error', f"Deployment error: {str(e)}")
            self.print_end_section()
            return None
    
    def _install_python_deps(self, package_dir):
        """Install Python dependencies"""
        requirements_file = os.path.join(package_dir, "requirements.txt")
        if os.path.exists(requirements_file):
            self.print_status('info', "Installing Python packages...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "-r", requirements_file, 
                    "-t", package_dir,
                    "--no-deps", "--upgrade"
                ], check=True, capture_output=True)
                self.print_status('success', "Python dependencies installed")
            except subprocess.CalledProcessError as e:
                self.print_status('warning', f"Some dependencies failed to install: {e}")
        else:
            self.print_status('info', "No requirements.txt found, skipping dependency installation")
    
    def _install_nodejs_deps(self, package_dir):
        """Install Node.js dependencies"""
        package_json = os.path.join(package_dir, "package.json")
        if os.path.exists(package_json):
            self.print_status('info', "Installing Node.js packages...")
            try:
                subprocess.run([
                    "npm", "install", "--production"
                ], cwd=package_dir, check=True, capture_output=True)
                self.print_status('success', "Node.js dependencies installed")
            except subprocess.CalledProcessError as e:
                self.print_status('warning', f"Some dependencies failed to install: {e}")
        else:
            self.print_status('info', "No package.json found, skipping dependency installation")
    
    def invoke_function(self, name, payload=None, test_mode=False):
        if not self.check_auth():
            return None
            
        self.print_section("FUNCTION INVOCATION")
        
        print(f"  Function Name    : {name}")
        print(f"  Test Mode        : {'Yes' if test_mode else 'No'}")
        print(f"  Payload Size     : {len(json.dumps(payload or {}))} bytes")
        print(f"  User             : {self.config.get('user_email', 'Unknown')}")
        
        data = {
            "payload": payload or {},
            "test_mode": test_mode
        }
        
        self.print_status('progress', "Invoking function...")
        
        try:
            headers = self.get_auth_headers()
            start_time = time.time()
            response = requests.post(f"{self.api_base}/functions/{name}/invoke", 
                                   json=data, headers=headers)
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
                
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
            self.print_end_section()
            return None
    
    def list_functions(self):
        if not self.check_auth():
            return None
            
        self.print_section("FUNCTION LIST")
        
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_base}/functions", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                functions = result['functions']
                
                if functions:
                    print(f"  Total Functions  : {result['total']}")
                    print(f"  Data Source      : {result['source']}")
                    print(f"  User             : {result['user']}")
                    print()
                    
                    for func in functions:
                        print(f"  * {func['name']}")
                        print(f"     Runtime       : {func['runtime']}")
                        print(f"     Status        : {func['status']}")
                        print(f"     Version       : {func['version']}")
                        print(f"     Invocations   : {func['invocation_count']}")
                        print(f"     Created       : {func['created_at']}")
                        if func.get('description'):
                            print(f"     Description   : {func['description']}")
                        print()
                else:
                    self.print_status('info', "No functions found")
                    
                self.print_end_section()
                return result
            else:
                self.print_status('error', f"Failed to list functions: {response.text}")
                self.print_end_section()
                return None
                
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
            self.print_end_section()
            return None

    def detect_runtime(self, path):
        if os.path.exists(os.path.join(path, "requirements.txt")) or \
           any(f.endswith('.py') for f in os.listdir(path)):
            return "python3.11"
        elif os.path.exists(os.path.join(path, "package.json")):
            return "nodejs18"
        elif any(f.endswith('.go') for f in os.listdir(path)):
            return "go1.21"
        elif any(f.endswith('.java') for f in os.listdir(path)):
            return "java17"
        else:
            return "python3.11"
def main():
    parser = argparse.ArgumentParser(description='Vajra Serverless Platform CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    subparsers.add_parser('init', help='Initialize authentication')
    subparsers.add_parser('logout', help='Logout and clear authentication')
    subparsers.add_parser('whoami', help='Show current user')
    subparsers.add_parser('list', help='List all functions')
    
    # Function details
    details_parser = subparsers.add_parser('details', help='Get function details')
    details_parser.add_argument('name', help='Function name')
    
    # Function deletion
    delete_parser = subparsers.add_parser('delete', help='Delete a function')
    delete_parser.add_argument('name', help='Function name')
    delete_parser.add_argument('--force', action='store_true', help='Force delete without confirmation')
    
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a function')
    deploy_parser.add_argument('name', help='Function name')
    deploy_parser.add_argument('path', help='Path to function code')
    deploy_parser.add_argument('--runtime', default='auto', help='Runtime')
    deploy_parser.add_argument('--handler', default='main', help='Function handler')
    deploy_parser.add_argument('--memory', type=int, default=512, help='Memory in MB')
    deploy_parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    deploy_parser.add_argument('--description', default='', help='Function description')
    
    invoke_parser = subparsers.add_parser('invoke', help='Invoke a function')
    invoke_parser.add_argument('name', help='Function name')
    invoke_parser.add_argument('--payload', help='JSON payload')
    invoke_parser.add_argument('--test', action='store_true', help='Enable test mode')
    
    args = parser.parse_args()
    
    cli = VajraCLI()
    
    if args.command == 'init':
        cli.print_banner()
        cli.init_auth()
    elif args.command == 'logout':
        cli.print_banner()
        cli.logout()
    elif args.command == 'whoami':
        cli.print_banner()
        cli.whoami()
    elif args.command == 'list':
        cli.print_banner()
        cli.list_functions()
    elif args.command == 'details':
        cli.print_banner()
        # Add simple details method
        if not cli.check_auth():
            return
        try:
            headers = cli.get_auth_headers()
            response = requests.get(f"{cli.api_base}/functions/{args.name}", headers=headers)
            if response.status_code == 200:
                result = response.json()
                func = result['function']
                print(f"\n* {func['name']}")
                print(f"   Runtime: {func['runtime']}")
                print(f"   Status: {func['status']}")
                print(f"   Memory: {func['memory']}MB")
                print(f"   Invocations: {func['invocation_count']}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    elif args.command == 'delete':
        cli.print_banner()
        # Add simple delete method
        if not cli.check_auth():
            return
        if not args.force:
            confirm = input(f"Delete function '{args.name}'? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Cancelled")
                return
        try:
            headers = cli.get_auth_headers()
            response = requests.delete(f"{cli.api_base}/functions/{args.name}", headers=headers)
            if response.status_code == 200:
                print(f"[OK] Function '{args.name}' deleted successfully")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    elif args.command == 'deploy':
        cli.print_banner()
        cli.deploy_function(
            name=args.name,
            path=args.path,
            runtime=args.runtime,
            handler=args.handler,
            memory=args.memory,
            timeout=args.timeout,
            description=args.description
        )
    elif args.command == 'invoke':
        cli.print_banner()
        payload = json.loads(args.payload) if args.payload else {}
        cli.invoke_function(args.name, payload, args.test)
    else:
        cli.print_banner()
        parser.print_help()

if __name__ == "__main__":
    main()