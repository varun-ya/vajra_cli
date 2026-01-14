"""
VAJRA LLM Platform - Serverless LLM Infrastructure
A Lambda-like platform optimized for LLM inference and fine-tuning on GCP.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uuid
import datetime
import asyncio
import random

app = FastAPI(
    title="VAJRA LLM Platform",
    description="Enterprise Serverless LLM Infrastructure - Deploy, Fine-tune, and Scale LLMs",
    version="1.0.0-beta"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MOCK DATA - Pre-populated LLM Models, Adapters, and Jobs
# ============================================================================

MOCK_MODELS = {
    "llama-3.1-8b": {
        "id": "model_llama31_8b",
        "name": "Llama 3.1 8B",
        "provider": "meta",
        "parameters": "8B",
        "context_length": 128000,
        "status": "deployed",
        "gpu_type": "A100-40GB",
        "gpu_count": 1,
        "cold_start_ms": 2500,
        "warm_instances": 3,
        "max_instances": 10,
        "requests_today": 15420,
        "avg_latency_ms": 145,
        "cost_per_1k_tokens": 0.0015,
        "created_at": "2026-01-10T08:00:00Z"
    },
    "llama-3.1-70b": {
        "id": "model_llama31_70b",
        "name": "Llama 3.1 70B",
        "provider": "meta",
        "parameters": "70B",
        "context_length": 128000,
        "status": "deployed",
        "gpu_type": "A100-80GB",
        "gpu_count": 4,
        "cold_start_ms": 8500,
        "warm_instances": 2,
        "max_instances": 5,
        "requests_today": 8230,
        "avg_latency_ms": 420,
        "cost_per_1k_tokens": 0.009,
        "created_at": "2026-01-08T10:30:00Z"
    },
    "mistral-7b": {
        "id": "model_mistral_7b",
        "name": "Mistral 7B Instruct",
        "provider": "mistral",
        "parameters": "7B",
        "context_length": 32768,
        "status": "deployed",
        "gpu_type": "L4",
        "gpu_count": 1,
        "cold_start_ms": 1800,
        "warm_instances": 5,
        "max_instances": 20,
        "requests_today": 42150,
        "avg_latency_ms": 85,
        "cost_per_1k_tokens": 0.0008,
        "created_at": "2026-01-05T14:00:00Z"
    },
    "gemma-2-9b": {
        "id": "model_gemma2_9b",
        "name": "Gemma 2 9B",
        "provider": "google",
        "parameters": "9B",
        "context_length": 8192,
        "status": "deployed",
        "gpu_type": "L4",
        "gpu_count": 1,
        "cold_start_ms": 2100,
        "warm_instances": 4,
        "max_instances": 15,
        "requests_today": 28900,
        "avg_latency_ms": 110,
        "cost_per_1k_tokens": 0.001,
        "created_at": "2026-01-12T09:15:00Z"
    },
    "codellama-34b": {
        "id": "model_codellama_34b",
        "name": "Code Llama 34B",
        "provider": "meta",
        "parameters": "34B",
        "context_length": 16384,
        "status": "warming",
        "gpu_type": "A100-40GB",
        "gpu_count": 2,
        "cold_start_ms": 5200,
        "warm_instances": 1,
        "max_instances": 8,
        "requests_today": 5670,
        "avg_latency_ms": 280,
        "cost_per_1k_tokens": 0.005,
        "created_at": "2026-01-14T06:00:00Z"
    }
}

MOCK_ADAPTERS = {
    "customer-support-v2": {
        "id": "adapter_cs_v2",
        "name": "Customer Support v2",
        "base_model": "llama-3.1-8b",
        "type": "lora",
        "rank": 16,
        "parameters": "4.2M",
        "status": "active",
        "accuracy": 0.94,
        "training_tokens": 2500000,
        "created_at": "2026-01-12T15:30:00Z"
    },
    "legal-docs-analyzer": {
        "id": "adapter_legal_v1",
        "name": "Legal Document Analyzer",
        "base_model": "llama-3.1-70b",
        "type": "lora",
        "rank": 32,
        "parameters": "16.8M",
        "status": "active",
        "accuracy": 0.91,
        "training_tokens": 8000000,
        "created_at": "2026-01-10T11:00:00Z"
    },
    "code-review-assistant": {
        "id": "adapter_code_v1",
        "name": "Code Review Assistant",
        "base_model": "codellama-34b",
        "type": "lora",
        "rank": 64,
        "parameters": "33.5M",
        "status": "training",
        "accuracy": None,
        "training_tokens": 12000000,
        "training_progress": 0.67,
        "created_at": "2026-01-14T08:00:00Z"
    },
    "medical-qa": {
        "id": "adapter_med_v1",
        "name": "Medical Q&A Specialist",
        "base_model": "mistral-7b",
        "type": "qlora",
        "rank": 16,
        "parameters": "2.1M",
        "status": "active",
        "accuracy": 0.89,
        "training_tokens": 5000000,
        "created_at": "2026-01-08T09:45:00Z"
    }
}

MOCK_JOBS = [
    {
        "id": "job_ft_001",
        "type": "fine-tuning",
        "model": "llama-3.1-8b",
        "adapter_name": "sales-email-writer",
        "status": "running",
        "progress": 0.45,
        "gpu_type": "A100-40GB",
        "gpu_count": 2,
        "epochs_completed": 2,
        "total_epochs": 5,
        "training_loss": 0.342,
        "validation_loss": 0.389,
        "tokens_processed": 4500000,
        "estimated_completion": "2026-01-14T20:30:00Z",
        "cost_so_far": 12.45,
        "created_at": "2026-01-14T14:00:00Z"
    },
    {
        "id": "job_ft_002",
        "type": "fine-tuning",
        "model": "gemma-2-9b",
        "adapter_name": "sentiment-analyzer",
        "status": "queued",
        "progress": 0,
        "gpu_type": "L4",
        "gpu_count": 1,
        "epochs_completed": 0,
        "total_epochs": 3,
        "estimated_start": "2026-01-14T21:00:00Z",
        "created_at": "2026-01-14T16:30:00Z"
    },
    {
        "id": "job_eval_001",
        "type": "evaluation",
        "model": "llama-3.1-70b",
        "adapter": "legal-docs-analyzer",
        "status": "completed",
        "progress": 1.0,
        "metrics": {
            "accuracy": 0.91,
            "f1_score": 0.89,
            "perplexity": 4.23,
            "latency_p50_ms": 380,
            "latency_p99_ms": 890
        },
        "completed_at": "2026-01-14T10:15:00Z",
        "created_at": "2026-01-14T09:00:00Z"
    }
]

MOCK_GPU_POOLS = {
    "a100-40gb": {
        "gpu_type": "A100-40GB",
        "total": 24,
        "available": 8,
        "reserved": 4,
        "in_use": 12,
        "regions": ["us-central1", "us-east4", "europe-west4"],
        "cost_per_hour": 3.67
    },
    "a100-80gb": {
        "gpu_type": "A100-80GB",
        "total": 16,
        "available": 4,
        "reserved": 2,
        "in_use": 10,
        "regions": ["us-central1", "europe-west4"],
        "cost_per_hour": 5.12
    },
    "l4": {
        "gpu_type": "L4",
        "total": 48,
        "available": 22,
        "reserved": 6,
        "in_use": 20,
        "regions": ["us-central1", "us-east4", "us-west1", "europe-west4", "asia-east1"],
        "cost_per_hour": 0.81
    },
    "h100": {
        "gpu_type": "H100-80GB",
        "total": 8,
        "available": 2,
        "reserved": 0,
        "in_use": 6,
        "regions": ["us-central1"],
        "cost_per_hour": 8.25
    }
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    adapter: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    stream: Optional[bool] = False

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    adapter: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7

class DeployModelRequest(BaseModel):
    model_id: str
    gpu_type: str = "L4"
    gpu_count: int = 1
    min_instances: int = 0
    max_instances: int = 10

class FineTuneRequest(BaseModel):
    base_model: str
    adapter_name: str
    training_data: str  # GCS path
    adapter_type: str = "lora"
    lora_rank: int = 16
    epochs: int = 3
    learning_rate: float = 2e-4
    batch_size: int = 4

class WarmupRequest(BaseModel):
    model: str
    instances: int = 1
    adapter: Optional[str] = None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Platform overview and status"""
    return {
        "platform": "VAJRA LLM Platform",
        "version": "1.0.0-beta",
        "status": "operational",
        "description": "Enterprise Serverless LLM Infrastructure",
        "features": [
            "Multi-model deployment",
            "LoRA/QLoRA adapter support",
            "Frozen Core architecture",
            "Auto-scaling (0 to N)",
            "GPU warm pools",
            "Per-token billing",
            "Fine-tuning jobs",
            "Real-time streaming"
        ],
        "stats": {
            "models_deployed": len([m for m in MOCK_MODELS.values() if m["status"] == "deployed"]),
            "active_adapters": len([a for a in MOCK_ADAPTERS.values() if a["status"] == "active"]),
            "gpu_utilization": "68%",
            "requests_today": sum(m["requests_today"] for m in MOCK_MODELS.values()),
            "avg_latency_ms": 180
        },
        "endpoints": {
            "inference": "/v1/completions, /v1/chat/completions",
            "models": "/v1/models",
            "adapters": "/v1/adapters",
            "fine-tuning": "/v1/fine-tuning/jobs",
            "gpu": "/v1/gpu/pools"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "gpu_available": True,
        "services": {
            "inference": "up",
            "fine-tuning": "up",
            "scheduler": "up",
            "billing": "up"
        }
    }

# ============================================================================
# INFERENCE ENDPOINTS
# ============================================================================

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    """Generate text completion (OpenAI-compatible)"""
    if request.model not in MOCK_MODELS:
        raise HTTPException(404, f"Model '{request.model}' not found. Available: {list(MOCK_MODELS.keys())}")
    
    model = MOCK_MODELS[request.model]
    
    # Simulate inference
    await asyncio.sleep(0.1)
    
    # Generate mock response based on prompt
    mock_responses = [
        f"Based on your query about '{request.prompt[:50]}...', here's a comprehensive analysis...",
        f"I understand you're asking about {request.prompt[:30]}. Let me explain...",
        f"Great question! Regarding '{request.prompt[:40]}', consider the following points..."
    ]
    
    completion_text = random.choice(mock_responses)
    tokens_generated = len(completion_text.split()) * 1.3  # Approximate tokens
    
    return {
        "id": f"cmpl-{uuid.uuid4().hex[:12]}",
        "object": "text_completion",
        "created": int(datetime.datetime.utcnow().timestamp()),
        "model": request.model,
        "adapter": request.adapter,
        "choices": [
            {
                "text": completion_text,
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": int(tokens_generated),
            "total_tokens": len(request.prompt.split()) + int(tokens_generated)
        },
        "meta": {
            "cold_start": False,
            "latency_ms": random.randint(80, 200),
            "gpu_type": model["gpu_type"],
            "cost": round(tokens_generated * model["cost_per_1k_tokens"] / 1000, 6)
        }
    }

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatRequest):
    """Chat completion (OpenAI-compatible)"""
    if request.model not in MOCK_MODELS:
        raise HTTPException(404, f"Model '{request.model}' not found")
    
    model = MOCK_MODELS[request.model]
    
    # Get last user message
    user_message = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
    
    await asyncio.sleep(0.1)
    
    # Generate contextual mock response
    if "code" in user_message.lower():
        response = "Here's a code solution for your request:\n\n```python\ndef solution():\n    # Implementation here\n    return result\n```\n\nThis approach uses efficient algorithms to solve the problem."
    elif "explain" in user_message.lower():
        response = "Let me break this down for you:\n\n1. **Key Concept**: The fundamental principle here is...\n2. **How it works**: The mechanism involves...\n3. **Best practices**: You should consider..."
    else:
        response = f"I've analyzed your request regarding '{user_message[:50]}'. Here are my thoughts and recommendations based on the context provided."
    
    tokens = len(response.split()) * 1.3
    
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(datetime.datetime.utcnow().timestamp()),
        "model": request.model,
        "adapter": request.adapter,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
            "completion_tokens": int(tokens),
            "total_tokens": sum(len(m.content.split()) for m in request.messages) + int(tokens)
        },
        "meta": {
            "cold_start": False,
            "latency_ms": random.randint(100, 300),
            "gpu_type": model["gpu_type"]
        }
    }

# ============================================================================
# MODEL MANAGEMENT
# ============================================================================

@app.get("/v1/models")
async def list_models():
    """List all available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": key,
                "object": "model",
                **value
            }
            for key, value in MOCK_MODELS.items()
        ],
        "total": len(MOCK_MODELS)
    }

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """Get model details"""
    if model_id not in MOCK_MODELS:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    model = MOCK_MODELS[model_id]
    adapters = [a for a in MOCK_ADAPTERS.values() if a["base_model"] == model_id]
    
    return {
        "model": model,
        "adapters": adapters,
        "metrics": {
            "requests_1h": random.randint(500, 2000),
            "requests_24h": model["requests_today"],
            "avg_latency_ms": model["avg_latency_ms"],
            "p99_latency_ms": int(model["avg_latency_ms"] * 2.5),
            "error_rate": round(random.uniform(0.001, 0.005), 4),
            "warm_instances": model["warm_instances"],
            "cold_starts_1h": random.randint(5, 20)
        }
    }

@app.post("/v1/models/deploy")
async def deploy_model(request: DeployModelRequest):
    """Deploy a new model instance"""
    return {
        "id": f"deploy_{uuid.uuid4().hex[:8]}",
        "model": request.model_id,
        "status": "deploying",
        "gpu_type": request.gpu_type,
        "gpu_count": request.gpu_count,
        "min_instances": request.min_instances,
        "max_instances": request.max_instances,
        "estimated_ready": "2-5 minutes",
        "message": f"Deploying {request.model_id} on {request.gpu_count}x {request.gpu_type}"
    }

@app.post("/v1/models/{model_id}/warmup")
async def warmup_model(model_id: str, request: WarmupRequest):
    """Pre-warm model instances"""
    if model_id not in MOCK_MODELS:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    return {
        "model": model_id,
        "instances_requested": request.instances,
        "instances_warming": request.instances,
        "adapter": request.adapter,
        "status": "warming",
        "estimated_ready_seconds": random.randint(30, 90),
        "message": f"Warming {request.instances} instances of {model_id}"
    }

@app.get("/v1/models/{model_id}/instances")
async def get_model_instances(model_id: str):
    """Get running instances of a model"""
    if model_id not in MOCK_MODELS:
        raise HTTPException(404, f"Model '{model_id}' not found")
    
    model = MOCK_MODELS[model_id]
    instances = []
    
    for i in range(model["warm_instances"]):
        instances.append({
            "id": f"inst_{model_id}_{i}",
            "status": "running",
            "gpu_type": model["gpu_type"],
            "region": random.choice(["us-central1", "us-east4", "europe-west4"]),
            "uptime_hours": random.randint(1, 72),
            "requests_served": random.randint(500, 5000),
            "memory_used_gb": round(random.uniform(10, 35), 1),
            "gpu_utilization": f"{random.randint(40, 85)}%"
        })
    
    return {
        "model": model_id,
        "instances": instances,
        "total_warm": len(instances),
        "max_instances": model["max_instances"]
    }

# ============================================================================
# ADAPTER MANAGEMENT
# ============================================================================

@app.get("/v1/adapters")
async def list_adapters():
    """List all adapters (LoRA, QLoRA)"""
    return {
        "object": "list",
        "data": [
            {"id": key, **value}
            for key, value in MOCK_ADAPTERS.items()
        ],
        "total": len(MOCK_ADAPTERS)
    }

@app.get("/v1/adapters/{adapter_id}")
async def get_adapter(adapter_id: str):
    """Get adapter details"""
    if adapter_id not in MOCK_ADAPTERS:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")
    
    adapter = MOCK_ADAPTERS[adapter_id]
    
    return {
        "adapter": adapter,
        "usage": {
            "requests_24h": random.randint(1000, 10000),
            "avg_latency_overhead_ms": random.randint(5, 15),
            "memory_overhead_mb": random.randint(50, 200)
        },
        "compatible_models": [adapter["base_model"]]
    }

@app.post("/v1/adapters")
async def create_adapter(
    name: str,
    base_model: str,
    adapter_type: str = "lora",
    rank: int = 16
):
    """Register a new adapter"""
    adapter_id = f"adapter_{name.lower().replace(' ', '_')}"
    
    return {
        "id": adapter_id,
        "name": name,
        "base_model": base_model,
        "type": adapter_type,
        "rank": rank,
        "status": "created",
        "message": "Adapter registered. Use fine-tuning API to train."
    }

@app.delete("/v1/adapters/{adapter_id}")
async def delete_adapter(adapter_id: str):
    """Delete an adapter"""
    if adapter_id not in MOCK_ADAPTERS:
        raise HTTPException(404, f"Adapter '{adapter_id}' not found")
    
    return {
        "id": adapter_id,
        "deleted": True,
        "message": f"Adapter '{adapter_id}' deleted successfully"
    }

# ============================================================================
# FINE-TUNING JOBS
# ============================================================================

@app.get("/v1/fine-tuning/jobs")
async def list_fine_tuning_jobs(
    status: Optional[str] = None,
    limit: int = Query(10, le=100)
):
    """List fine-tuning jobs"""
    jobs = MOCK_JOBS
    
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    
    return {
        "object": "list",
        "data": jobs[:limit],
        "total": len(jobs)
    }

@app.get("/v1/fine-tuning/jobs/{job_id}")
async def get_fine_tuning_job(job_id: str):
    """Get fine-tuning job details"""
    job = next((j for j in MOCK_JOBS if j["id"] == job_id), None)
    
    if not job:
        raise HTTPException(404, f"Job '{job_id}' not found")
    
    return {
        "job": job,
        "logs": [
            {"timestamp": "2026-01-14T14:00:00Z", "message": "Job started"},
            {"timestamp": "2026-01-14T14:05:00Z", "message": "Loading dataset..."},
            {"timestamp": "2026-01-14T14:10:00Z", "message": "Epoch 1 started"},
            {"timestamp": "2026-01-14T15:30:00Z", "message": f"Epoch 1 completed. Loss: 0.542"},
            {"timestamp": "2026-01-14T16:45:00Z", "message": f"Epoch 2 completed. Loss: 0.342"}
        ]
    }

@app.post("/v1/fine-tuning/jobs")
async def create_fine_tuning_job(request: FineTuneRequest):
    """Create a new fine-tuning job"""
    job_id = f"job_ft_{uuid.uuid4().hex[:6]}"
    
    return {
        "id": job_id,
        "status": "queued",
        "base_model": request.base_model,
        "adapter_name": request.adapter_name,
        "adapter_type": request.adapter_type,
        "lora_rank": request.lora_rank,
        "training_data": request.training_data,
        "hyperparameters": {
            "epochs": request.epochs,
            "learning_rate": request.learning_rate,
            "batch_size": request.batch_size
        },
        "estimated_cost": round(random.uniform(15, 50), 2),
        "estimated_duration": "2-4 hours",
        "created_at": datetime.datetime.utcnow().isoformat()
    }

@app.post("/v1/fine-tuning/jobs/{job_id}/cancel")
async def cancel_fine_tuning_job(job_id: str):
    """Cancel a fine-tuning job"""
    return {
        "id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    }

# ============================================================================
# GPU MANAGEMENT
# ============================================================================

@app.get("/v1/gpu/pools")
async def list_gpu_pools():
    """List available GPU pools"""
    return {
        "pools": MOCK_GPU_POOLS,
        "total_gpus": sum(p["total"] for p in MOCK_GPU_POOLS.values()),
        "available_gpus": sum(p["available"] for p in MOCK_GPU_POOLS.values()),
        "utilization": f"{round(sum(p['in_use'] for p in MOCK_GPU_POOLS.values()) / sum(p['total'] for p in MOCK_GPU_POOLS.values()) * 100)}%"
    }

@app.get("/v1/gpu/pools/{gpu_type}")
async def get_gpu_pool(gpu_type: str):
    """Get GPU pool details"""
    pool_key = gpu_type.lower().replace("-", "-")
    
    # Find matching pool
    pool = None
    for key, value in MOCK_GPU_POOLS.items():
        if gpu_type.upper() in value["gpu_type"].upper():
            pool = value
            break
    
    if not pool:
        raise HTTPException(404, f"GPU pool '{gpu_type}' not found")
    
    return {
        "pool": pool,
        "queue": {
            "pending_requests": random.randint(0, 5),
            "avg_wait_time_seconds": random.randint(0, 120)
        }
    }

@app.post("/v1/gpu/reserve")
async def reserve_gpu(
    gpu_type: str,
    count: int = 1,
    duration_hours: int = 1
):
    """Reserve GPU capacity"""
    return {
        "reservation_id": f"res_{uuid.uuid4().hex[:8]}",
        "gpu_type": gpu_type,
        "count": count,
        "duration_hours": duration_hours,
        "status": "confirmed",
        "cost_estimate": round(count * duration_hours * random.uniform(2, 8), 2),
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)).isoformat()
    }

# ============================================================================
# BILLING & USAGE
# ============================================================================

@app.get("/v1/usage")
async def get_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get usage and billing summary"""
    return {
        "period": {
            "start": start_date or "2026-01-01",
            "end": end_date or "2026-01-14"
        },
        "summary": {
            "total_requests": 1250430,
            "total_tokens": 45678900,
            "total_cost": 342.67,
            "gpu_hours": 156.4
        },
        "by_model": [
            {"model": "llama-3.1-8b", "requests": 420000, "tokens": 18500000, "cost": 92.50},
            {"model": "mistral-7b", "requests": 580000, "tokens": 15200000, "cost": 60.80},
            {"model": "llama-3.1-70b", "requests": 150000, "tokens": 8500000, "cost": 127.50},
            {"model": "gemma-2-9b", "requests": 100430, "tokens": 3478900, "cost": 61.87}
        ],
        "by_day": [
            {"date": "2026-01-14", "requests": 95420, "cost": 28.45},
            {"date": "2026-01-13", "requests": 102300, "cost": 31.20},
            {"date": "2026-01-12", "requests": 88900, "cost": 26.80}
        ]
    }

@app.get("/v1/usage/realtime")
async def get_realtime_usage():
    """Get real-time usage metrics"""
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "last_minute": {
            "requests": random.randint(800, 1500),
            "tokens": random.randint(50000, 150000),
            "avg_latency_ms": random.randint(100, 200),
            "error_rate": round(random.uniform(0.001, 0.01), 4)
        },
        "active_sessions": random.randint(150, 400),
        "gpu_utilization": f"{random.randint(55, 85)}%",
        "warm_instances": sum(m["warm_instances"] for m in MOCK_MODELS.values())
    }

# ============================================================================
# TRACES & OBSERVABILITY
# ============================================================================

@app.get("/v1/traces")
async def list_traces(
    model: Optional[str] = None,
    limit: int = Query(20, le=100)
):
    """List recent traces"""
    traces = []
    for i in range(limit):
        model_name = model or random.choice(list(MOCK_MODELS.keys()))
        traces.append({
            "trace_id": f"trace_{uuid.uuid4().hex[:12]}",
            "model": model_name,
            "adapter": random.choice([None, "customer-support-v2", "legal-docs-analyzer"]),
            "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(minutes=i*5)).isoformat(),
            "duration_ms": random.randint(80, 500),
            "cold_start": random.random() < 0.1,
            "status": random.choices(["success", "error"], weights=[0.98, 0.02])[0],
            "tokens": random.randint(50, 500)
        })
    
    return {"traces": traces, "total": len(traces)}

@app.get("/v1/metrics")
async def get_metrics():
    """Get platform metrics"""
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "inference": {
            "requests_per_second": round(random.uniform(150, 300), 1),
            "p50_latency_ms": random.randint(100, 150),
            "p95_latency_ms": random.randint(200, 350),
            "p99_latency_ms": random.randint(400, 600),
            "error_rate": round(random.uniform(0.001, 0.005), 4)
        },
        "gpu": {
            "utilization": f"{random.randint(55, 80)}%",
            "memory_used": f"{random.randint(60, 85)}%",
            "active_gpus": sum(p["in_use"] for p in MOCK_GPU_POOLS.values())
        },
        "scaling": {
            "warm_instances": sum(m["warm_instances"] for m in MOCK_MODELS.values()),
            "cold_starts_last_hour": random.randint(10, 50),
            "scale_up_events": random.randint(2, 10),
            "scale_down_events": random.randint(1, 5)
        }
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("    VAJRA LLM PLATFORM - Serverless LLM Infrastructure")
    print("="*70)
    print(f"    Models Available: {len(MOCK_MODELS)}")
    print(f"    Active Adapters: {len(MOCK_ADAPTERS)}")
    print(f"    GPU Pools: {len(MOCK_GPU_POOLS)}")
    print("    API Docs: http://localhost:8000/docs")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
