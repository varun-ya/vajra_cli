# Vajra CLI Documentation

Complete command reference with examples for Vajra platform CLI tools.

---

## Overview

| CLI | Purpose | Backend |
|-----|---------|---------|
| `vajra-cli.py` | Serverless functions | Cloud (production) |
| `vajra-llm-cli.py` | LLM platform | `localhost:8000` |

---

# vajra-llm-cli.py (LLM Platform)

## Quick Start
```bash
cd vajra-serverless
python vajra-llm-cli.py health
```

---

## Commands Reference

### `health` - Check API Status
```bash
python3 vajra-llm-cli.py health
```

**Example Output:**
```
┌─ HEALTH CHECK ──────────────────────────────────────────────────┐
  [OK] Status: healthy
  API URL: http://localhost:8000
  Timestamp: 2026-01-14T19:30:00
└──────────────────────────────────────────────────────────────────┘
```

---

### `models` - List LLM Models
```bash
python3 vajra-llm-cli.py models
```

**Example Output:**
```
┌─ AVAILABLE MODELS ──────────────────────────────────────────────┐
  Total Models: 5

  ● Llama 3.1 8B Instruct
     ID         : llama-3.1-8b
     Parameters : 8B
     GPU        : 1x A100-40GB
     Status     : deployed
     Latency    : 45ms
     Instances  : 3/8

  ● Mistral 7B Instruct
     ID         : mistral-7b
     Parameters : 7B
     GPU        : 1x A100-40GB
     Status     : deployed
     Latency    : 38ms
     Instances  : 2/6
└──────────────────────────────────────────────────────────────────┘
```

---

### `adapters` - List LoRA/QLoRA Adapters
```bash
python3 vajra-llm-cli.py adapters
```

**Example Output:**
```
┌─ ADAPTERS ──────────────────────────────────────────────────────┐
  Total Adapters: 3

  ● customer-support-v2
     Type       : LORA
     Base Model : llama-3.1-8b
     Rank       : 16
     Status     : active
     Accuracy   : 94.2%

  ○ code-review-adapter
     Type       : QLORA
     Base Model : codellama-34b
     Rank       : 32
     Status     : training
└──────────────────────────────────────────────────────────────────┘
```

---

### `gpu` - GPU Pool Status
```bash
python3 vajra-llm-cli.py gpu
```

**Example Output:**
```
┌─ GPU POOLS ─────────────────────────────────────────────────────┐
  Total GPUs: 48
  Available : 21

  A100-40GB
     [████████████░░░░░░░░] 60%
     Total    : 20
     In Use   : 12
     Available: 5
     Cost     : $2.50/hr
     Regions  : us-central1, us-east1

  H100-80GB
     [██████░░░░░░░░░░░░░░] 30%
     Total    : 8
     In Use   : 2
     Available: 4
     Cost     : $6.50/hr
     Regions  : us-central1
└──────────────────────────────────────────────────────────────────┘
```

---

### `jobs` - Fine-tuning Jobs
```bash
python3 vajra-llm-cli.py jobs
```

**Example Output:**
```
┌─ FINE-TUNING JOBS ──────────────────────────────────────────────┐
  Total Jobs: 4

  ▶ customer-support-v3
     ID       : ft-abc123
     Model    : llama-3.1-8b
     Type     : lora
     Status   : RUNNING
     Progress : 67%
     GPU      : 2x A100-40GB
     Cost     : $8.50

  ✓ code-assistant-v1
     ID       : ft-def456
     Model    : codellama-34b
     Type     : qlora
     Status   : COMPLETED
     Progress : 100%
     GPU      : 4x A100-80GB
     Cost     : $45.20
└──────────────────────────────────────────────────────────────────┘
```

---

### `usage` - Usage Statistics
```bash
python3 vajra-llm-cli.py usage
```

**Example Output:**
```
┌─ USAGE STATISTICS ──────────────────────────────────────────────┐
  Total Requests : 1,284,567
  Total Tokens   : 45,678,901
  Total Cost     : $892.45
  GPU Hours      : 156

  Usage by Model:
     llama-3.1-8b: 456,789 requests, $312.50
     mistral-7b: 234,567 requests, $187.25
     gemma-2-9b: 123,456 requests, $145.80
└──────────────────────────────────────────────────────────────────┘
```

---

### `metrics` - Real-time Metrics
```bash
python3 vajra-llm-cli.py metrics
```

**Example Output:**
```
┌─ REAL-TIME METRICS ─────────────────────────────────────────────┐
  Inference:
     Requests/sec : 125.3
     P50 Latency  : 45ms
     P99 Latency  : 180ms
     Error Rate   : 0.02%

  GPU:
     Utilization  : 78%
     Memory Used  : 65%
     Active GPUs  : 18

  Scaling:
     Warm Instances: 15
     Cold Starts   : 3
└──────────────────────────────────────────────────────────────────┘
```

---

### `chat` - Chat Completion
```bash
python3 vajra-llm-cli.py chat <model> "<message>" [--adapter <name>]
```

**Examples:**
```bash
# Basic chat
python3 vajra-llm-cli.py chat llama-3.1-8b "What is machine learning?"

# With adapter
python3 vajra-llm-cli.py chat llama-3.1-8b "Help me with my order" --adapter customer-support-v2

# Code generation
python3 vajra-llm-cli.py chat codellama-34b "Write a Python function to sort a list"
```

**Example Output:**
```
┌─ CHAT COMPLETION ───────────────────────────────────────────────┐
  Model   : llama-3.1-8b
  Message : What is machine learning?

  Response:
  ------------------------------------------------------------
  Machine learning is a subset of artificial intelligence that
  enables systems to learn and improve from experience without
  being explicitly programmed. It focuses on developing algorithms
  that can access data and use it to learn for themselves.
  ------------------------------------------------------------

  Tokens     : 156 (prompt: 8, completion: 148)
  Latency    : 234ms (server: 189ms)
  Cost       : $0.000312

  [OK] Completion successful
└──────────────────────────────────────────────────────────────────┘
```

---

### `create-job` - Create Fine-tuning Job
```bash
python3 vajra-llm-cli.py create-job <model> <adapter-name> <data-path> [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--type` | lora | `lora` or `qlora` |
| `--epochs` | 3 | Training epochs |

**Examples:**
```bash
# Basic LoRA training
python3 vajra-llm-cli.py create-job llama-3.1-8b support-bot gs://my-bucket/support.jsonl

# QLoRA with 5 epochs
python3 vajra-llm-cli.py create-job llama-3.1-8b code-helper gs://data/code.jsonl --type qlora --epochs 5
```

**Example Output:**
```
┌─ CREATE FINE-TUNING JOB ────────────────────────────────────────┐
  Base Model    : llama-3.1-8b
  Adapter Name  : support-bot
  Adapter Type  : lora
  Training Data : gs://my-bucket/support.jsonl
  Epochs        : 3

  [OK] Job created: ft-xyz789
  Status: queued
  GPU: A100-40GB
└──────────────────────────────────────────────────────────────────┘
```

---

# vajra-cli.py (Serverless Functions)

## Commands Reference

### `init` - Authenticate
```bash
python3 vajra-cli.py init
```
Opens browser for Google OAuth authentication.

### `logout` - Clear Auth
```bash
python3 vajra-cli.py logout
```

### `whoami` - Current User
```bash
python3 vajra-cli.py whoami
```

**Example Output:**
```
┌─ USER INFORMATION ──────────────────────────────────────────────┐
  Email: varun@example.com
  User ID: user_abc123
  Status: Authenticated
  Authenticated: 2026-01-14T18:00:00
└──────────────────────────────────────────────────────────────────┘
```

### `list` - List Functions
```bash
python3 vajra-cli.py list
```

**Example Output:**
```
┌─ FUNCTION LIST ─────────────────────────────────────────────────┐
  Total Functions  : 3

  * hello-world
     Runtime       : python3.11
     Status        : deployed
     Version       : 1
     Invocations   : 1,234
     Created       : 2026-01-10

  * image-processor
     Runtime       : python3.11
     Status        : deployed
     Version       : 3
     Invocations   : 567
└──────────────────────────────────────────────────────────────────┘
```

### `deploy` - Deploy Function
```bash
python3 vajra-cli.py deploy <name> <path> [options]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--runtime` | auto | python3.11, nodejs18, go1.21, java17 |
| `--handler` | main | Entry point function |
| `--memory` | 512 | Memory in MB |
| `--timeout` | 30 | Timeout in seconds |
| `--description` | "" | Function description |

**Examples:**
```bash
# Auto-detect runtime
python3 vajra-cli.py deploy my-func ./src

# Python with custom config
python3 vajra-cli.py deploy api-handler ./api --runtime python3.11 --memory 1024 --timeout 60

# Node.js function
python3 vajra-cli.py deploy webhook ./handlers --runtime nodejs18 --handler index.handler
```

### `invoke` - Invoke Function
```bash
python3 vajra-cli.py invoke <name> [--payload JSON] [--test]
```

**Examples:**
```bash
# Simple invoke
python3 vajra-cli.py invoke hello-world

# With payload
python3 vajra-cli.py invoke process-data --payload '{"id": 123, "action": "process"}'

# Test mode
python3 vajra-cli.py invoke my-func --payload '{"test": true}' --test
```

**Example Output:**
```
┌─ FUNCTION INVOCATION ───────────────────────────────────────────┐
  Function Name    : hello-world
  Test Mode        : No
  Payload Size     : 24 bytes

  [OK] Function executed successfully
  Execution Time   : 45ms
  Memory Used      : 128MB
  Total Latency    : 234.56ms
  Result           :
    {"message": "Hello, World!", "processed": true}
└──────────────────────────────────────────────────────────────────┘
```

### `details` - Function Details
```bash
python3 vajra-cli.py details <name>
```

### `delete` - Delete Function
```bash
python3 vajra-cli.py delete <name> [--force]
```

---

## Environment Variables

```bash
# LLM CLI - API endpoint (default: http://localhost:8000)
export VAJRA_API_URL=http://localhost:8000

# Serverless CLI - uses cloud API by default
# Configured in ~/.vajra/config.json
```

---

## Supported Models

| Model | ID | Parameters | GPU |
|-------|-----|------------|-----|
| Llama 3.1 8B | `llama-3.1-8b` | 8B | 1x A100-40GB |
| Llama 3.1 70B | `llama-3.1-70b` | 70B | 4x A100-80GB |
| Mistral 7B | `mistral-7b` | 7B | 1x A100-40GB |
| Gemma 2 9B | `gemma-2-9b` | 9B | 1x A100-40GB |
| CodeLlama 34B | `codellama-34b` | 34B | 2x A100-80GB |

---

## GPU Pricing

| GPU | VRAM | Cost/hr |
|-----|------|---------|
| L4 | 24GB | $0.80 |
| A100-40GB | 40GB | $2.50 |
| A100-80GB | 80GB | $4.00 |
| H100-80GB | 80GB | $6.50 |
