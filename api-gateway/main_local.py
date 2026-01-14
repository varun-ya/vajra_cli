"""
Vajra Serverless Platform - Local Development Server
A simplified version that runs without Google Cloud dependencies.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import uuid
import datetime
import asyncio
import os
import tempfile
import zipfile

app = FastAPI(title="Vajra Serverless Platform (Local)", version="3.0.0-local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for local development
functions_store: Dict[str, dict] = {}
function_versions: Dict[str, list] = {}
function_logs: Dict[str, list] = {}

# Runtime configurations
RUNTIMES = {
    "python3.8": {"image": "python:3.8-slim", "cmd": ["python", "main.py"], "ext": ".py"},
    "python3.9": {"image": "python:3.9-slim", "cmd": ["python", "main.py"], "ext": ".py"},
    "python3.10": {"image": "python:3.10-slim", "cmd": ["python", "main.py"], "ext": ".py"},
    "python3.11": {"image": "python:3.11-slim", "cmd": ["python", "main.py"], "ext": ".py"},
    "python3.12": {"image": "python:3.12-slim", "cmd": ["python", "main.py"], "ext": ".py"},
    "nodejs16": {"image": "node:16-alpine", "cmd": ["node", "index.js"], "ext": ".js"},
    "nodejs18": {"image": "node:18-alpine", "cmd": ["node", "index.js"], "ext": ".js"},
    "nodejs20": {"image": "node:20-alpine", "cmd": ["node", "index.js"], "ext": ".js"},
    "go1.19": {"image": "golang:1.19-alpine", "cmd": ["go", "run", "main.go"], "ext": ".go"},
    "go1.20": {"image": "golang:1.20-alpine", "cmd": ["go", "run", "main.go"], "ext": ".go"},
    "go1.21": {"image": "golang:1.21-alpine", "cmd": ["go", "run", "main.go"], "ext": ".go"},
    "java11": {"image": "openjdk:11-jdk-slim", "cmd": ["java", "Main.java"], "ext": ".java"},
    "java17": {"image": "openjdk:17-jdk-slim", "cmd": ["java", "Main.java"], "ext": ".java"},
    "java21": {"image": "openjdk:21-jdk-slim", "cmd": ["java", "Main.java"], "ext": ".java"},
    "rust1.70": {"image": "rust:1.70", "cmd": ["cargo", "run"], "ext": ".rs"},
    "dotnet6": {"image": "mcr.microsoft.com/dotnet/runtime:6.0", "cmd": ["dotnet", "run"], "ext": ".cs"},
    "dotnet8": {"image": "mcr.microsoft.com/dotnet/runtime:8.0", "cmd": ["dotnet", "run"], "ext": ".cs"}
}

class FunctionConfig(BaseModel):
    name: str
    runtime: str
    handler: str
    memory: Optional[int] = 512
    timeout: Optional[int] = 30
    environment: Optional[Dict[str, str]] = {}
    description: Optional[str] = ""

class InvokeRequest(BaseModel):
    payload: Dict = {}
    test_mode: Optional[bool] = False

@app.get("/")
async def root():
    return {
        "service": "Vajra Serverless Platform (Local Development)",
        "version": "3.0.0-local",
        "status": "running",
        "features": [
            "multi-runtime", "in-memory-storage", "function-deployment",
            "function-invocation", "logging", "versioning"
        ],
        "supported_runtimes": list(RUNTIMES.keys()),
        "runtime_count": len(RUNTIMES),
        "functions_deployed": len(functions_store),
        "mode": "local-development"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.post("/functions")
async def create_function(
    background_tasks: BackgroundTasks,
    name: str = Form(),
    runtime: str = Form(),
    handler: str = Form(),
    memory: int = Form(512),
    timeout: int = Form(30),
    description: str = Form(""),
    environment: str = Form("{}"),
    code: UploadFile = File(None)
):
    """Deploy a new serverless function"""
    if runtime not in RUNTIMES:
        raise HTTPException(400, f"Unsupported runtime: {runtime}. Supported: {list(RUNTIMES.keys())}")
    
    if name in functions_store:
        raise HTTPException(400, f"Function '{name}' already exists. Use PUT to update.")
    
    function_id = str(uuid.uuid4())
    
    try:
        env_vars = json.loads(environment) if environment else {}
    except json.JSONDecodeError:
        env_vars = {}
    
    # Read code if provided
    code_content = None
    if code:
        code_content = await code.read()
    
    function_data = {
        "id": function_id,
        "name": name,
        "runtime": runtime,
        "handler": handler,
        "memory": memory,
        "timeout": timeout,
        "description": description,
        "environment": env_vars,
        "version": 1,
        "status": "deploying",
        "code_size": len(code_content) if code_content else 0,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "invocation_count": 0,
        "error_count": 0,
        "endpoint": f"http://localhost:8000/functions/{name}/invoke"
    }
    
    functions_store[name] = function_data
    function_versions[name] = [{"version": 1, "created_at": function_data["created_at"]}]
    function_logs[name] = []
    
    # Simulate deployment
    background_tasks.add_task(deploy_function, name)
    
    add_log(name, "INFO", f"Function '{name}' created with runtime {runtime}")
    
    return {
        "function_id": function_id,
        "name": name,
        "status": "deploying",
        "version": 1,
        "endpoint": function_data["endpoint"]
    }

async def deploy_function(name: str):
    """Simulate function deployment"""
    await asyncio.sleep(2)  # Simulate build time
    if name in functions_store:
        functions_store[name]["status"] = "deployed"
        functions_store[name]["updated_at"] = datetime.datetime.utcnow().isoformat()
        add_log(name, "INFO", f"Function '{name}' deployed successfully")

@app.get("/functions")
async def list_functions():
    """List all deployed functions"""
    functions = []
    for name, data in functions_store.items():
        functions.append({
            "name": data["name"],
            "runtime": data["runtime"],
            "status": data["status"],
            "version": data["version"],
            "invocation_count": data["invocation_count"],
            "created_at": data["created_at"],
            "description": data["description"]
        })
    
    return {
        "functions": functions,
        "total": len(functions),
        "source": "local-memory"
    }

@app.get("/functions/{name}")
async def get_function(name: str):
    """Get function details"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    function_data = functions_store[name]
    logs = function_logs.get(name, [])[-10:]  # Last 10 logs
    
    return {
        "function": function_data,
        "logs": logs,
        "metrics": {
            "invocations": function_data["invocation_count"],
            "errors": function_data["error_count"],
            "success_rate": calculate_success_rate(function_data),
            "avg_duration_ms": 45
        }
    }

@app.post("/functions/{name}/invoke")
async def invoke_function(name: str, request: InvokeRequest):
    """Invoke a function"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    function_data = functions_store[name]
    
    if function_data["status"] != "deployed":
        raise HTTPException(400, f"Function is not deployed yet. Status: {function_data['status']}")
    
    # Increment invocation count
    functions_store[name]["invocation_count"] += 1
    
    add_log(name, "INFO", f"Function invoked with payload: {json.dumps(request.payload)[:100]}")
    
    # Simulate function execution
    try:
        result = await execute_function_simulation(function_data, request.payload)
        
        return {
            "result": result,
            "function": name,
            "status": "success",
            "execution_time": "45ms",
            "memory_used": f"{function_data['memory'] // 4}MB",
            "test_mode": request.test_mode
        }
    except Exception as e:
        functions_store[name]["error_count"] += 1
        add_log(name, "ERROR", f"Execution failed: {str(e)}")
        raise HTTPException(500, f"Function execution failed: {str(e)}")

async def execute_function_simulation(function_data: dict, payload: dict):
    """Simulate function execution"""
    await asyncio.sleep(0.05)  # Simulate execution time
    
    runtime = function_data["runtime"]
    handler = function_data["handler"]
    
    # Return simulated response based on payload
    return {
        "message": f"Hello from {function_data['name']}!",
        "runtime": runtime,
        "handler": handler,
        "input": payload,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "processed": True
    }

@app.delete("/functions/{name}")
async def delete_function(name: str):
    """Delete a function"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    del functions_store[name]
    if name in function_versions:
        del function_versions[name]
    if name in function_logs:
        del function_logs[name]
    
    return {"status": "deleted", "function": name}

@app.get("/functions/{name}/logs")
async def get_logs(name: str, limit: int = 50):
    """Get function logs"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    logs = function_logs.get(name, [])[-limit:]
    return {"logs": logs, "total": len(logs)}

@app.get("/functions/{name}/versions")
async def get_versions(name: str):
    """Get function version history"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    versions = function_versions.get(name, [])
    return {"versions": versions, "current": functions_store[name]["version"]}

@app.post("/functions/{name}/versions")
async def create_version(name: str, description: str = ""):
    """Create a new version of the function"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    current_version = functions_store[name]["version"]
    new_version = current_version + 1
    
    functions_store[name]["version"] = new_version
    functions_store[name]["updated_at"] = datetime.datetime.utcnow().isoformat()
    
    function_versions[name].append({
        "version": new_version,
        "description": description,
        "created_at": datetime.datetime.utcnow().isoformat()
    })
    
    add_log(name, "INFO", f"New version {new_version} created")
    
    return {"version": new_version, "status": "created"}

@app.get("/functions/{name}/cost")
async def get_cost_analysis(name: str, days: int = 30):
    """Get cost analysis for a function"""
    if name not in functions_store:
        raise HTTPException(404, f"Function '{name}' not found")
    
    function_data = functions_store[name]
    invocations = function_data["invocation_count"]
    
    # Simulated cost calculation
    compute_cost = invocations * 0.0000002 * function_data["memory"]
    request_cost = invocations * 0.0000002
    
    return {
        "function_name": name,
        "period_days": days,
        "total_invocations": invocations,
        "costs": {
            "compute_cost": round(compute_cost, 4),
            "request_cost": round(request_cost, 4),
            "total_cost": round(compute_cost + request_cost, 4)
        },
        "currency": "USD"
    }

@app.get("/runtimes")
async def list_runtimes():
    """List all supported runtimes"""
    return {
        "runtimes": [
            {"name": name, "image": config["image"], "extension": config["ext"]}
            for name, config in RUNTIMES.items()
        ],
        "total": len(RUNTIMES)
    }

# Helper functions
def add_log(function_name: str, level: str, message: str):
    """Add a log entry for a function"""
    if function_name not in function_logs:
        function_logs[function_name] = []
    
    function_logs[function_name].append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "level": level,
        "message": message
    })

def calculate_success_rate(function_data: dict) -> float:
    """Calculate success rate for a function"""
    total = function_data["invocation_count"]
    if total == 0:
        return 100.0
    errors = function_data["error_count"]
    return round((total - errors) / total * 100, 2)

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("    VAJRA SERVERLESS PLATFORM - LOCAL DEVELOPMENT")
    print("="*60)
    print(f"    Supported Runtimes: {len(RUNTIMES)}")
    print("    API Docs: http://localhost:8000/docs")
    print("    Health: http://localhost:8000/health")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
