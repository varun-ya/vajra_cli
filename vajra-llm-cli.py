#!/usr/bin/env python3
"""
Vajra LLM Platform CLI
Command-line interface for managing LLM models, adapters, fine-tuning, and inference.
"""

import requests
import os
import sys
import json
import time
import argparse
from datetime import datetime

# Default to local development server
API_BASE = os.environ.get("VAJRA_API_URL", "http://localhost:8000")

class VajraLLMCLI:
    def __init__(self):
        self.api_base = API_BASE
    
    def print_banner(self):
        banner = """
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ██╗   ██╗ █████╗      ██╗██████╗  █████╗                      │
│  ██║   ██║██╔══██╗     ██║██╔══██╗██╔══██╗                     │
│  ██║   ██║███████║     ██║██████╔╝███████║                     │
│  ╚██╗ ██╔╝██╔══██║██   ██║██╔══██╗██╔══██║                     │
│   ╚████╔╝ ██║  ██║╚█████╔╝██║  ██║██║  ██║                     │
│    ╚═══╝  ╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                     │
│                                                                 │
│                    Vajra LLM Platform CLI                       │
│                        Version 1.0.0                            │
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
        }
        symbol = symbols.get(status, '[INFO]')
        print(f"  {symbol} {message}")
    
    def health_check(self):
        """Check API health"""
        self.print_section("HEALTH CHECK")
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_status('success', f"Status: {data['status']}")
                print(f"  API URL: {self.api_base}")
                print(f"  Timestamp: {data['timestamp']}")
            else:
                self.print_status('error', f"Health check failed: {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_status('error', f"Cannot connect to {self.api_base}")
            self.print_status('info', "Make sure the backend is running:")
            print("  cd vajra-serverless/api-gateway")
            print("  python -m uvicorn main_llm:app --host 0.0.0.0 --port 8000")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def list_models(self):
        """List all available LLM models"""
        self.print_section("AVAILABLE MODELS")
        try:
            response = requests.get(f"{self.api_base}/v1/models")
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                print(f"  Total Models: {len(models)}\n")
                
                for model in models:
                    status_icon = "●" if model['status'] == 'deployed' else "○"
                    status_color = "deployed" if model['status'] == 'deployed' else model['status']
                    print(f"  {status_icon} {model['name']}")
                    print(f"     ID         : {model['id']}")
                    print(f"     Parameters : {model['parameters']}")
                    print(f"     GPU        : {model['gpu_count']}x {model['gpu_type']}")
                    print(f"     Status     : {status_color}")
                    print(f"     Latency    : {model['avg_latency_ms']}ms")
                    print(f"     Instances  : {model['warm_instances']}/{model['max_instances']}")
                    print()
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def list_adapters(self):
        """List all adapters (LoRA/QLoRA)"""
        self.print_section("ADAPTERS")
        try:
            response = requests.get(f"{self.api_base}/v1/adapters")
            if response.status_code == 200:
                data = response.json()
                adapters = data.get('data', [])
                print(f"  Total Adapters: {len(adapters)}\n")
                
                for adapter in adapters:
                    status_icon = "●" if adapter['status'] == 'active' else "○"
                    print(f"  {status_icon} {adapter['name']}")
                    print(f"     Type       : {adapter['type'].upper()}")
                    print(f"     Base Model : {adapter['base_model']}")
                    print(f"     Rank       : {adapter['rank']}")
                    print(f"     Status     : {adapter['status']}")
                    if adapter.get('accuracy'):
                        print(f"     Accuracy   : {adapter['accuracy']*100:.1f}%")
                    print()
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def list_gpu_pools(self):
        """List GPU pools"""
        self.print_section("GPU POOLS")
        try:
            response = requests.get(f"{self.api_base}/v1/gpu/pools")
            if response.status_code == 200:
                data = response.json()
                pools = data.get('pools', {})
                print(f"  Total GPUs: {data.get('total_gpus', 0)}")
                print(f"  Available : {data.get('available_gpus', 0)}\n")
                
                for name, pool in pools.items():
                    utilization = (pool['in_use'] / pool['total']) * 100
                    bar_len = 20
                    filled = int(bar_len * pool['in_use'] / pool['total'])
                    bar = "█" * filled + "░" * (bar_len - filled)
                    
                    print(f"  {pool['gpu_type']}")
                    print(f"     [{bar}] {utilization:.0f}%")
                    print(f"     Total    : {pool['total']}")
                    print(f"     In Use   : {pool['in_use']}")
                    print(f"     Available: {pool['available']}")
                    print(f"     Cost     : ${pool['cost_per_hour']}/hr")
                    print(f"     Regions  : {', '.join(pool['regions'])}")
                    print()
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def list_jobs(self):
        """List fine-tuning jobs"""
        self.print_section("FINE-TUNING JOBS")
        try:
            response = requests.get(f"{self.api_base}/v1/fine-tuning/jobs")
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                print(f"  Total Jobs: {len(jobs)}\n")
                
                status_icons = {
                    'running': '▶',
                    'queued': '◌',
                    'completed': '✓',
                    'failed': '✗',
                    'cancelled': '○'
                }
                
                for job in jobs:
                    icon = status_icons.get(job['status'], '?')
                    print(f"  {icon} {job.get('adapter_name', job.get('adapter', 'Unnamed'))}")
                    print(f"     ID       : {job['id']}")
                    print(f"     Model    : {job['model']}")
                    print(f"     Type     : {job['type']}")
                    print(f"     Status   : {job['status'].upper()}")
                    print(f"     Progress : {job['progress']*100:.0f}%")
                    print(f"     GPU      : {job['gpu_count']}x {job['gpu_type']}")
                    if job.get('cost_so_far'):
                        print(f"     Cost     : ${job['cost_so_far']:.2f}")
                    print()
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def get_usage(self):
        """Get usage statistics"""
        self.print_section("USAGE STATISTICS")
        try:
            response = requests.get(f"{self.api_base}/v1/usage")
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', {})
                
                print(f"  Total Requests : {summary.get('total_requests', 0):,}")
                print(f"  Total Tokens   : {summary.get('total_tokens', 0):,}")
                print(f"  Total Cost     : ${summary.get('total_cost', 0):.2f}")
                print(f"  GPU Hours      : {summary.get('gpu_hours', 0)}")
                
                print("\n  Usage by Model:")
                for model in data.get('by_model', []):
                    print(f"     {model['model']}: {model['requests']:,} requests, ${model['cost']:.2f}")
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def get_metrics(self):
        """Get real-time metrics"""
        self.print_section("REAL-TIME METRICS")
        try:
            response = requests.get(f"{self.api_base}/v1/metrics")
            if response.status_code == 200:
                data = response.json()
                
                inf = data.get('inference', {})
                gpu = data.get('gpu', {})
                scaling = data.get('scaling', {})
                
                print("  Inference:")
                print(f"     Requests/sec : {inf.get('requests_per_second', 0):.1f}")
                print(f"     P50 Latency  : {inf.get('p50_latency_ms', 0)}ms")
                print(f"     P99 Latency  : {inf.get('p99_latency_ms', 0)}ms")
                print(f"     Error Rate   : {inf.get('error_rate', 0)*100:.2f}%")
                
                print("\n  GPU:")
                print(f"     Utilization  : {gpu.get('utilization', '0%')}")
                print(f"     Memory Used  : {gpu.get('memory_used', '0%')}")
                print(f"     Active GPUs  : {gpu.get('active_gpus', 0)}")
                
                print("\n  Scaling:")
                print(f"     Warm Instances: {scaling.get('warm_instances', 0)}")
                print(f"     Cold Starts   : {scaling.get('cold_starts_last_hour', 0)}")
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def chat(self, model, message, adapter=None):
        """Send a chat completion request"""
        self.print_section("CHAT COMPLETION")
        print(f"  Model   : {model}")
        if adapter:
            print(f"  Adapter : {adapter}")
        print(f"  Message : {message[:50]}{'...' if len(message) > 50 else ''}")
        print()
        
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": 512,
                "temperature": 0.7
            }
            if adapter:
                payload["adapter"] = adapter
            
            start = time.time()
            response = requests.post(f"{self.api_base}/v1/chat/completions", json=payload)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                meta = data.get('meta', {})
                
                print("  Response:")
                print("  " + "-" * 60)
                for line in content.split('\n'):
                    print(f"  {line}")
                print("  " + "-" * 60)
                print()
                print(f"  Tokens     : {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")
                print(f"  Latency    : {latency:.0f}ms (server: {meta.get('latency_ms', 0)}ms)")
                print(f"  Cost       : ${meta.get('cost', 0):.6f}")
                
                self.print_status('success', "Completion successful")
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()
    
    def create_job(self, base_model, adapter_name, training_data, adapter_type="lora", epochs=3):
        """Create a fine-tuning job"""
        self.print_section("CREATE FINE-TUNING JOB")
        print(f"  Base Model    : {base_model}")
        print(f"  Adapter Name  : {adapter_name}")
        print(f"  Adapter Type  : {adapter_type}")
        print(f"  Training Data : {training_data}")
        print(f"  Epochs        : {epochs}")
        print()
        
        try:
            payload = {
                "base_model": base_model,
                "adapter_name": adapter_name,
                "adapter_type": adapter_type,
                "training_data": training_data,
                "epochs": epochs
            }
            
            response = requests.post(f"{self.api_base}/v1/fine-tuning/jobs", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.print_status('success', f"Job created: {data.get('job_id', 'unknown')}")
                print(f"  Status: {data.get('status', 'unknown')}")
                print(f"  GPU: {data.get('gpu_type', 'unknown')}")
            else:
                self.print_status('error', f"Failed: {response.text}")
        except Exception as e:
            self.print_status('error', f"Error: {str(e)}")
        self.print_end_section()


def main():
    parser = argparse.ArgumentParser(
        description='Vajra LLM Platform CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vajra-llm-cli.py health              Check API health
  vajra-llm-cli.py models              List available models
  vajra-llm-cli.py adapters            List adapters
  vajra-llm-cli.py gpu                 Show GPU pools
  vajra-llm-cli.py jobs                List fine-tuning jobs
  vajra-llm-cli.py usage               Show usage statistics
  vajra-llm-cli.py metrics             Show real-time metrics
  vajra-llm-cli.py chat llama-3.1-8b "Hello, how are you?"
  vajra-llm-cli.py create-job llama-3.1-8b my-adapter gs://data.jsonl
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Health check
    subparsers.add_parser('health', help='Check API health')
    
    # Models
    subparsers.add_parser('models', help='List available models')
    
    # Adapters
    subparsers.add_parser('adapters', help='List adapters')
    
    # GPU pools
    subparsers.add_parser('gpu', help='Show GPU pools')
    
    # Fine-tuning jobs
    subparsers.add_parser('jobs', help='List fine-tuning jobs')
    
    # Usage
    subparsers.add_parser('usage', help='Show usage statistics')
    
    # Metrics
    subparsers.add_parser('metrics', help='Show real-time metrics')
    
    # Chat
    chat_parser = subparsers.add_parser('chat', help='Send chat completion')
    chat_parser.add_argument('model', help='Model ID (e.g., llama-3.1-8b)')
    chat_parser.add_argument('message', help='Message to send')
    chat_parser.add_argument('--adapter', help='Adapter to use')
    
    # Create job
    job_parser = subparsers.add_parser('create-job', help='Create fine-tuning job')
    job_parser.add_argument('base_model', help='Base model ID')
    job_parser.add_argument('adapter_name', help='Name for the adapter')
    job_parser.add_argument('training_data', help='GCS path to training data')
    job_parser.add_argument('--type', default='lora', choices=['lora', 'qlora'], help='Adapter type')
    job_parser.add_argument('--epochs', type=int, default=3, help='Number of epochs')
    
    args = parser.parse_args()
    
    cli = VajraLLMCLI()
    
    if args.command == 'health':
        cli.print_banner()
        cli.health_check()
    elif args.command == 'models':
        cli.print_banner()
        cli.list_models()
    elif args.command == 'adapters':
        cli.print_banner()
        cli.list_adapters()
    elif args.command == 'gpu':
        cli.print_banner()
        cli.list_gpu_pools()
    elif args.command == 'jobs':
        cli.print_banner()
        cli.list_jobs()
    elif args.command == 'usage':
        cli.print_banner()
        cli.get_usage()
    elif args.command == 'metrics':
        cli.print_banner()
        cli.get_metrics()
    elif args.command == 'chat':
        cli.print_banner()
        cli.chat(args.model, args.message, args.adapter)
    elif args.command == 'create-job':
        cli.print_banner()
        cli.create_job(args.base_model, args.adapter_name, args.training_data, args.type, args.epochs)
    else:
        cli.print_banner()
        parser.print_help()


if __name__ == "__main__":
    main()
