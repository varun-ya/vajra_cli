#!/usr/bin/env python3

import requests
import zipfile
import os
import sys
import json
import time
import webbrowser
import http.server
import socketserver
import threading
import urllib.parse
from datetime import datetime
import argparse
from pathlib import Path

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
        """Load CLI configuration"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config):
        """Save CLI configuration"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def load_token(self):
        """Load authentication token"""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                return f.read().strip()
        return None
    
    def save_token(self, token):
        """Save authentication token"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        # Set file permissions to be readable only by owner
        os.chmod(TOKEN_FILE, 0o600)
        self.token = token
    
    def get_auth_headers(self):
        """Get authentication headers"""
        if not self.token:
            raise Exception("Not authenticated. Run 'vajra init' first.")
        return {"Authorization": f"Bearer {self.token}"}
    
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
│                 Vajra Serverless Platform CLI                   │
│                     Enterprise Edition v3.0                     │
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
    
    def init_auth(self):
        """Initialize authentication"""
        self.print_section("AUTHENTICATION SETUP")
        
        print("  Welcome to Vajra Serverless Platform!")
        print("  You need to authenticate with Google to continue.")
        print()
        
        # For development, use simple email-based auth
        email = input("  Enter your email address: ").strip()
        if not email or "@" not in email:
            self.print_status('error', "Invalid email address")
            self.print_end_section()
            return False
        
        # Create a simple token (in production, this would be OAuth flow)
        token = f"user:{email}"
        
        # Test the token
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.api_base}/auth/user", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                self.save_token(token)
                
                self.print_status('success', f"Successfully authenticated as {email}")
                print(f"  User ID: {user_info['user']['user_id']}")
                print(f"  Email: {user_info['user']['email']}")
                
                # Save user info to config
                config = {
                    "user_email": email,
                    "user_id": user_info['user']['user_id'],
                    "authenticated_at": datetime.now().isoformat()
                }
                self.save_config(config)
                
                self.print_end_section()
                return True
            else:
                self.print_status('error', f"Authentication failed: {response.text}")
                self.print_end_section()
                return False
                
        except Exception as e:
            self.print_status('error', f"Authentication error: {str(e)}")
            self.print_end_section()
            return False
    
    def check_auth(self):
        """Check if user is authenticated"""
        if not self.token:
            print("Not authenticated. Please run 'vajra init' first.")
            return False
        
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.api_base}/auth/user", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def whoami(self):
        """Show current user information"""
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
        """Deploy function with advanced configuration"""
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
        
        try:
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
                
                headers = self.get_auth_headers()
                response = requests.post(f"{self.api_base}/functions", 
                                       files=files, data=data, headers=headers)
            
            # Clean up zip file
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
            # Clean up zip file on error
            if os.path.exists(zip_path):
                os.remove(zip_path)
            self.print_status('error', f"Deployment error: {str(e)}")
            self.print_end_section()
            return None
    
    def detect_runtime(self, path):
        """Auto-detect runtime based on files in directory"""
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
            return "python3.11"  # Default

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Vajra Serverless Platform CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize authentication')
    
    # Whoami command
    whoami_parser = subparsers.add_parser('whoami', help='Show current user')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a function')
    deploy_parser.add_argument('name', help='Function name')
    deploy_parser.add_argument('path', help='Path to function code')
    deploy_parser.add_argument('--runtime', default='auto', help='Runtime (auto-detect if not specified)')
    deploy_parser.add_argument('--handler', default='main', help='Function handler')
    deploy_parser.add_argument('--memory', type=int, default=512, help='Memory in MB')
    deploy_parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    deploy_parser.add_argument('--description', default='', help='Function description')
    
    args = parser.parse_args()
    
    cli = VajraCLI()
    
    if args.command == 'init':
        cli.print_banner()
        cli.init_auth()
    elif args.command == 'whoami':
        cli.print_banner()
        cli.whoami()
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
    else:
        cli.print_banner()
        parser.print_help()

if __name__ == "__main__":
    main()