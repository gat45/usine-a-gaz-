"""
HX365 Command Center - API Server Module
==========================================

FastAPI server that integrates all components:
- Core engine
- Hardware optimization
- RAG system
- Power user features
"""

import asyncio
import os
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

from hx365_core import hx365_engine
from hx365_hardware import hardware_optimizer
from hx365_rag import rag_engine
from hx365_power_user import power_user_features

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HX365-API")

app = FastAPI(title="HX365 Command Center API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatCompletionRequest(BaseModel):
    model: str = "fastflow-hx"
    messages: List[Dict[str, str]]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = 2048
    top_p: float = 0.9
    user: Optional[str] = "default_user"
    use_companion: Optional[bool] = False
    enrich_with_companion: Optional[bool] = False

class SystemStatusResponse(BaseModel):
    timestamp: str
    services: Dict[str, Any]
    system_metrics: Dict[str, Any]
    active_sessions: int

class RAGIngestRequest(BaseModel):
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RAGSearchRequest(BaseModel):
    query: str
    k: Optional[int] = 5

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    logger.info("Starting up HX365 Command Center API")
    await hx365_engine.initialize()
    await hardware_optimizer.initialize()
    await power_user_features.initialize()
    logger.info("All components initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all components on shutdown"""
    logger.info("Shutting down HX365 Command Center API")
    await power_user_features.shutdown()
    await hardware_optimizer.shutdown()
    await hx365_engine.shutdown()
    logger.info("All components shut down")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "core_engine": "initialized",
            "hardware_optimizer": "initialized",
            "rag_engine": "loaded",
            "power_user_features": "initialized"
        }
    }

@app.get("/v1/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    return hx365_engine.get_system_status()

@app.get("/v1/hardware/status")
async def get_hardware_status():
    """Get hardware-specific status"""
    return hardware_optimizer.get_hardware_status()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Main chat completions endpoint compatible with OpenAI API"""
    try:
        # Create session if it doesn't exist
        session_id = request.user or "default_user"
        if session_id not in hx365_engine.sessions:
            hx365_engine.create_session(session_id)
        
        # Check if this is a command
        last_message = request.messages[-1] if request.messages else {"role": "user", "content": ""}
        if last_message["content"].strip().startswith("/"):
            # Process as command
            command = last_message["content"].split()[0]
            params = " ".join(last_message["content"].split()[1:])
            
            result = await power_user_features.process_command(command, session_id, params)
            return {
                "id": f"cmd-{int(time.time())}",
                "object": "text.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": str(result)},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": len(str(result)), "total_tokens": len(str(result))}
            }
        
        # Check if hybrid mode should be used
        if request.enrich_with_companion or "search" in last_message["content"].lower():
            # Use hybrid mode with Companion enrichment
            result = await power_user_features.process_message_with_hybrid(
                session_id, 
                last_message["content"]
            )
        else:
            # Process normally
            result = await hx365_engine.process_user_request(
                session_id,
                last_message["content"],
                use_companion=request.use_companion,
                **request.dict(exclude={'messages', 'user'})
            )
        
        # Format response according to OpenAI API spec
        if "choices" in result:
            return result
        else:
            # Format error response
            return {
                "id": f"error-{int(time.time())}",
                "object": "text.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": f"Error: {result.get('error', 'Unknown error')}"},
                    "finish_reason": "error"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
    except Exception as e:
        logger.error(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/rag/ingest")
async def ingest_document(request: RAGIngestRequest):
    """Ingest a document into the RAG system"""
    try:
        doc_id = rag_engine.ingest_document(
            request.content, 
            doc_id=request.title,
            metadata=request.metadata
        )
        return {
            "message": "Document ingested successfully",
            "doc_id": doc_id,
            "chunk_count": len([c for c in rag_engine.vector_index.document_chunks.values() if c.document_id == doc_id])
        }
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/rag/search")
async def search_documents(request: RAGSearchRequest):
    """Search for relevant documents in the RAG system"""
    try:
        results = await rag_engine.retrieve(request.query, k=request.k)
        return {
            "query": request.query,
            "results": [
                {
                    "content": result.content,
                    "score": result.score,
                    "document_id": result.document_id,
                    "chunk_id": result.chunk_id,
                    "metadata": result.metadata
                }
                for result in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/rag/document/{doc_id}")
async def get_document_summary(doc_id: str):
    """Get summary information about a document"""
    try:
        summary = rag_engine.get_document_summary(doc_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return summary
    except Exception as e:
        logger.error(f"Error getting document summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/logs/recent")
async def get_recent_logs(count: int = 50):
    """Get recent system logs"""
    try:
        logs = power_user_features.get_system_logs(count)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/logs/search")
async def search_logs(search_term: str, count: int = 50):
    """Search system logs"""
    try:
        results = power_user_features.search_system_logs(search_term)
        return {"search_term": search_term, "results": results[:count], "total_found": len(results)}
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/system/command")
async def execute_system_command(request: Request):
    """Execute a system command (for power users)"""
    try:
        body = await request.json()
        command = body.get("command", "")
        session_id = body.get("session_id", "default_user")
        params = body.get("params", "")
        
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")
        
        result = await power_user_features.process_command(command, session_id, params)
        return result
    except Exception as e:
        logger.error(f"Error executing system command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/performance/report")
async def get_performance_report():
    """Get system performance report"""
    try:
        report = power_user_features.get_performance_report()
        return {
            "timestamp": datetime.now().isoformat(),
            "report": report,
            "recommendations": hardware_optimizer.get_optimization_suggestions()
        }
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/sessions/list")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": list(hx365_engine.sessions.keys()),
        "count": len(hx365_engine.sessions),
        "active_sessions": hx365_engine.get_system_status()["active_sessions"]
    }

@app.post("/v1/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a specific session"""
    try:
        hx365_engine.reset_session(session_id)
        return {"message": f"Session {session_id} reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "fastflow-hx",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "hx365"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=os.getenv("HOST", "127.0.0.1"), 
        port=int(os.getenv("PORT", "8080")),
        log_level="info"
    )