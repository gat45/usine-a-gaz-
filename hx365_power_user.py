"""
HX365 Command Center - Power User Features Module
====================================================

Implementation of advanced features for power users:
- Hybrid mode with Companion integration
- Command parsing for advanced operations
- System logs and debugging tools
- NPU management functions
"""

import asyncio
import os
import logging
import json
import subprocess
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from hx365_core import hx365_engine
from hx365_hardware import hardware_optimizer
from hx365_rag import rag_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HX365-PowerUser")

class CommandType(Enum):
    RESET_SESSION = "reset"
    CONFIG_RUNTIME = "config"
    NPU_REBOOT = "npu-reboot"
    DEBUG_INFO = "debug"
    LOGS = "logs"
    RAG_MANAGE = "rag"
    HARDWARE_STATUS = "hw-status"
    PERFORMANCE_REPORT = "perf-report"

class CommandRegistry:
    """
    Registry for slash commands
    """
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {
            "/reset": self.reset_session,
            "/config": self.config_runtime,
            "/npu-reboot": self.npu_reboot,
            "/debug": self.debug_info,
            "/logs": self.show_logs,
            "/rag-add": self.rag_add_document,
            "/rag-search": self.rag_search,
            "/hw-status": self.hardware_status,
            "/perf-report": self.performance_report,
            "/help": self.show_help
        }
    
    async def execute_command(self, command: str, session_id: str, params: str = "") -> Dict[str, Any]:
        """
        Execute a slash command
        """
        cmd = command.lower()
        if cmd in self.commands:
            try:
                return await self.commands[cmd](session_id, params)
            except Exception as e:
                logger.error(f"Error executing command {cmd}: {e}")
                return {"error": f"Command execution failed: {str(e)}"}
        else:
            return {"error": f"Unknown command: {cmd}. Type /help for available commands."}
    
    async def reset_session(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Reset the current session"""
        hx365_engine.reset_session(session_id)
        return {"message": f"Session {session_id} has been reset."}
    
    async def config_runtime(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Configure runtime parameters"""
        if not params:
            # Return current config
            current_params = hx365_engine.session_params.get(session_id, {})
            return {
                "message": "Current session parameters:",
                "params": current_params
            }
        
        # Parse parameters (format: "param1=value1 param2=value2")
        try:
            param_pairs = params.split()
            updates = {}
            
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Try to convert to appropriate type
                    if value.isdigit():
                        updates[key] = int(value)
                    elif value.replace('.', '').isdigit():
                        updates[key] = float(value)
                    elif value.lower() in ('true', 'false'):
                        updates[key] = value.lower() == 'true'
                    else:
                        updates[key] = value
            
            # Update session parameters
            if session_id not in hx365_engine.session_params:
                hx365_engine.session_params[session_id] = {}
            
            hx365_engine.session_params[session_id].update(updates)
            
            return {
                "message": f"Updated session parameters: {updates}",
                "params": hx365_engine.session_params[session_id]
            }
        except Exception as e:
            return {"error": f"Invalid parameter format: {str(e)}"}
    
    async def npu_reboot(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Reboot NPU (simulation)"""
        try:
            # In a real implementation, this would interface with AMD drivers
            # to reset/reinitialize the NPU
            logger.info("Simulating NPU reboot sequence...")
            
            # Simulate reboot process
            await asyncio.sleep(1)  # Simulate reboot time
            
            # Refresh hardware status
            hw_status = hardware_optimizer.get_hardware_status()
            
            return {
                "message": "NPU reboot initiated successfully",
                "status": hw_status
            }
        except Exception as e:
            return {"error": f"NPU reboot failed: {str(e)}"}
    
    async def debug_info(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Show debug information"""
        system_status = hx365_engine.get_system_status()
        hw_status = hardware_optimizer.get_hardware_status()
        
        return {
            "system_status": system_status,
            "hardware_status": hw_status,
            "session_info": {
                "id": session_id,
                "message_count": len(hx365_engine.get_session_history(session_id)),
                "params": hx365_engine.session_params.get(session_id, {})
            }
        }
    
    async def show_logs(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Show system logs"""
        # In a real implementation, this would access the actual log system
        # For now, we'll simulate by returning recent logs
        return {
            "message": "Recent system logs:",
            "logs": [
                "[INFO] HX365 Command Center initialized",
                "[DEBUG] Ryzen 9 HX optimizations applied",
                "[INFO] FastFlowLM connected and ready",
                "[INFO] NPU acceleration enabled",
                "[RAG] Vector index loaded with 1,248 chunks",
                "[PERF] CPU affinity set to cores [0, 1, 2, 3]"
            ]
        }
    
    async def rag_add_document(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Add document to RAG system"""
        if not params:
            return {"error": "Please provide document content or path"}
        
        try:
            # If params looks like a file path, try to read it
            if os.path.exists(params):
                with open(params, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc_id = rag_engine.ingest_document(content, doc_id=params.split('/')[-1])
            else:
                # Treat as direct content
                doc_id = rag_engine.ingest_document(params)
            
            return {
                "message": f"Document added to RAG system",
                "doc_id": doc_id
            }
        except Exception as e:
            return {"error": f"Failed to add document to RAG: {str(e)}"}
    
    async def rag_search(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Search in RAG system"""
        if not params:
            return {"error": "Please provide search query"}
        
        try:
            results = await rag_engine.retrieve(params, k=3)
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "content_preview": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "document_id": result.document_id,
                    "metadata": result.metadata
                })
            
            return {
                "message": f"Found {len(results)} results for query: '{params}'",
                "results": formatted_results
            }
        except Exception as e:
            return {"error": f"RAG search failed: {str(e)}"}
    
    async def hardware_status(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Show hardware status"""
        return hardware_optimizer.get_hardware_status()
    
    async def performance_report(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Generate performance report"""
        hw_status = hardware_optimizer.get_hardware_status()
        system_status = hx365_engine.get_system_status()
        
        # Calculate some performance metrics
        avg_cpu = sum(hw_status["cpu"]["usage_per_core"]) / len(hw_status["cpu"]["usage_per_core"])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "avg_cpu_utilization": avg_cpu,
                "ram_utilization": hw_status["cpu"]["avg_usage"],
                "npu_utilization": hw_status["npu"]["utilization"],
                "active_sessions": system_status["active_sessions"]
            },
            "recommendations": hardware_optimizer.get_optimization_suggestions()
        }
        
        return {
            "message": "Performance report generated",
            "report": report
        }
    
    async def show_help(self, session_id: str, params: str = "") -> Dict[str, Any]:
        """Show help information"""
        help_text = """
Available commands:
  /reset - Reset current session
  /config [param=value] - View or set runtime parameters
  /npu-reboot - Reboot NPU (if available)
  /debug - Show system debug information
  /logs - Show system logs
  /rag-add <content|path> - Add document to RAG system
  /rag-search <query> - Search in RAG system
  /hw-status - Show hardware status
  /perf-report - Generate performance report
  /help - Show this help message
        """
        return {"message": help_text.strip()}

class HybridModeController:
    """
    Controller for hybrid mode using Companion to enrich prompts before NPU inference
    """
    
    def __init__(self):
        self.is_active = False
        self.enrichment_enabled = True
    
    async def process_with_hybrid_enrichment(self, 
                                           session_id: str, 
                                           user_message: str) -> Dict[str, Any]:
        """
        Process a message using hybrid mode with Companion enrichment
        """
        if not self.enrichment_enabled:
            # Fallback to normal processing
            return await hx365_engine.process_user_request(
                session_id, 
                user_message, 
                use_companion=False, 
                enrich_with_companion=False
            )
        
        # First, try to enrich with Companion
        try:
            # Check if Companion is available
            service_status = hx365_engine.orchestrator.get_service_status()
            companion_ready = service_status["companion"].status.value == "ready"
            
            if companion_ready:
                # Enrich the query using Companion
                enriched_result = await self._enrich_with_companion(user_message)
                
                if "error" not in enriched_result:
                    # Process with enriched context
                    return await hx365_engine.process_user_request(
                        session_id,
                        user_message,
                        use_companion=False,  # Don't use companion directly
                        enrich_with_companion=False,  # We already enriched
                        enriched_context=enriched_result.get("enriched_query", user_message)
                    )
            
            # Fallback to normal processing if Companion is not available
            return await hx365_engine.process_user_request(
                session_id,
                user_message,
                use_companion=False,
                enrich_with_companion=False
            )
        except Exception as e:
            logger.error(f"Hybrid mode processing failed: {e}")
            # Fallback to normal processing
            return await hx365_engine.process_user_request(
                session_id,
                user_message,
                use_companion=False,
                enrich_with_companion=False
            )
    
    async def _enrich_with_companion(self, query: str) -> Dict[str, Any]:
        """
        Enrich a query using FastFlow Companion
        """
        try:
            import httpx
            
            # Determine the type of enrichment needed
            needs_search = any(word in query.lower() for word in [
                'search', 'find', 'lookup', 'research', 'latest', 'news', 
                'information', 'data', 'fact', 'current'
            ])
            
            needs_tools = any(word in query.lower() for word in [
                'calculate', 'compute', 'math', 'convert', 'translate',
                'analyze', 'summarize', 'compare'
            ])
            
            if needs_search:
                # Use Companion's search capability
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{os.getenv('COMPANION_BASE', 'http://127.0.0.1:52626/v1')}/search",
                        json={
                            "query": query,
                            "mode": "search",
                            "depth": "deep"  # Use deep search for better results
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        enriched_query = f"Context from search: {data.get('results', '')}\n\nOriginal query: {query}"
                        return {
                            "enriched_query": enriched_query,
                            "source": "companion_search",
                            "results": data
                        }
                    else:
                        return {"error": f"Companion search failed: {response.status_code}"}
            
            elif needs_tools:
                # Use Companion's tool capability
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{os.getenv('COMPANION_BASE', 'http://127.0.0.1:52626/v1')}/tools",
                        json={
                            "query": query,
                            "tool": "calculator" if any(op in query for op in ['+', '-', '*', '/', '=']) else "general"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        enriched_query = f"Tool result: {data.get('result', '')}\n\nOriginal query: {query}"
                        return {
                            "enriched_query": enriched_query,
                            "source": "companion_tool",
                            "results": data
                        }
                    else:
                        return {"error": f"Companion tool failed: {response.status_code}"}
            else:
                # General enrichment
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{os.getenv('COMPANION_BASE', 'http://127.0.0.1:52626/v1')}/enrich",
                        json={
                            "query": query,
                            "context": "general"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        enriched_query = f"Additional context: {data.get('context', '')}\n\nOriginal query: {query}"
                        return {
                            "enriched_query": enriched_query,
                            "source": "companion_general",
                            "results": data
                        }
                    else:
                        return {"error": f"Companion enrichment failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Companion enrichment error: {str(e)}"}

class SystemLogger:
    """
    Advanced logging system for debugging and reverse engineering
    """
    
    def __init__(self, log_file: str = "hx365_debug.log"):
        self.log_file = log_file
        self.logs = []
        self.max_logs = 1000  # Keep last 1000 entries
        
        # Set up file handler
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_handler.setFormatter(formatter)
        
        # Add handler to the power user logger
        logger.addHandler(self.file_handler)
    
    def log_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log an event with details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        self.logs.append(log_entry)
        
        # Keep log size manageable
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to file
        logger.info(f"{event_type}: {details}")
    
    def get_recent_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent log entries
        """
        return self.logs[-count:]
    
    def search_logs(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search logs for a specific term
        """
        results = []
        search_term_lower = search_term.lower()
        
        for log in self.logs:
            # Search in event type and details
            if (search_term_lower in log["event_type"].lower() or 
                any(search_term_lower in str(v).lower() for v in log["details"].values() if isinstance(v, str))):
                results.append(log)
        
        return results
    
    def export_logs(self, filename: str = None) -> str:
        """
        Export logs to a file
        """
        if filename is None:
            filename = f"hx365_logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
        
        return filename

class PowerUserFeatures:
    """
    Main class that combines all power user features
    """
    
    def __init__(self):
        self.command_registry = CommandRegistry()
        self.hybrid_controller = HybridModeController()
        self.system_logger = SystemLogger()
        self.is_initialized = False
    
    async def initialize(self):
        """
        Initialize power user features
        """
        if not self.is_initialized:
            logger.info("Initializing power user features")
            self.is_initialized = True
    
    async def shutdown(self):
        """
        Shutdown power user features
        """
        if self.is_initialized:
            logger.info("Shutting down power user features")
            self.is_initialized = False
    
    async def process_command(self, command: str, session_id: str, params: str = "") -> Dict[str, Any]:
        """
        Process a slash command
        """
        self.system_logger.log_event("command_execution", {
            "command": command,
            "session_id": session_id,
            "params": params
        })
        
        result = await self.command_registry.execute_command(command, session_id, params)
        
        self.system_logger.log_event("command_result", {
            "command": command,
            "session_id": session_id,
            "result": result
        })
        
        return result
    
    async def process_message_with_hybrid(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Process a message using hybrid mode
        """
        self.system_logger.log_event("hybrid_processing", {
            "session_id": session_id,
            "message": message[:100] + "..." if len(message) > 100 else message
        })
        
        result = await self.hybrid_controller.process_with_hybrid_enrichment(session_id, message)
        
        self.system_logger.log_event("hybrid_result", {
            "session_id": session_id,
            "result_success": "error" not in result
        })
        
        return result
    
    def get_system_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent system logs
        """
        return self.system_logger.get_recent_logs(count)
    
    def search_system_logs(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search system logs
        """
        return self.system_logger.search_logs(search_term)
    
    def export_system_logs(self, filename: str = None) -> str:
        """
        Export system logs to file
        """
        return self.system_logger.export_logs(filename)
    
    def get_hardware_status(self) -> Dict[str, Any]:
        """
        Get current hardware status
        """
        return hardware_optimizer.get_hardware_status()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report
        """
        return hardware_optimizer.get_hardware_status()  # Using hardware status as base for now

# Global instance
power_user_features = PowerUserFeatures()

# Initialize when module is loaded
async def init_power_user_features():
    await power_user_features.initialize()

# Run initialization
if __name__ != "__main__":
    # If imported, initialize in the background
    asyncio.create_task(init_power_user_features())