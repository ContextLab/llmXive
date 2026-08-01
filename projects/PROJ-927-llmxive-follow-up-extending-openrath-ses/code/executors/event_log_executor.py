import os
import json
import time
import random
import logging
from typing import Dict, Any, Optional, List

from executors.base_executor import ExecutionResult, BaseExecutor
from config import load_state

logger = logging.getLogger(__name__)


class EventLogExecutor(BaseExecutor):
    """
    Executor for the Baseline Event-Log architecture.
    
    Stores transcripts, snapshots, and outputs as separate fragmented files
    asynchronously, simulating a distributed logging system.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.output_dir = config.get("raw_data_dir", "data/raw/workflows")
        self.jitter_enabled = config.get("jitter_enabled", True)
        self.max_jitter_ms = config.get("max_jitter_ms", 100)
        
        # Load state for checkpointing if available
        self.state = load_state()

    def _write_log_fragment(self, file_path: str, data: Dict[str, Any]) -> None:
        """
        Writes a single log fragment (transcript, snapshot, or output) to disk.
        Simulates asynchronous writes by appending to the file.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Append mode for fragmented logs
        mode = "a" if os.path.exists(file_path) else "w"
        if mode == "w":
            # If writing a new file, ensure it's a JSONL or array structure
            # For simplicity in this simulation, we write line-by-line JSON (JSONL)
            pass

        with open(file_path, mode) as f:
            f.write(json.dumps(data) + "\n")

    def tool_call(self, tool_name: str, inputs: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """
        Simulates a tool call with stochastic network delay (jitter).
        
        FR-004: Inject stochastic network delay (jitter) simulation.
        Injects time.sleep(random.uniform(0, jitter_ms)) specifically inside this method.
        """
        # Inject stochastic network delay if enabled
        if self.jitter_enabled:
            jitter_ms = self.max_jitter_ms
            delay = random.uniform(0, jitter_ms / 1000.0)  # Convert ms to seconds
            time.sleep(delay)
            logger.debug(f"Tool '{tool_name}' experienced network jitter: {delay*1000:.2f}ms")

        # Simulate tool execution logic
        # In a real scenario, this would call an external API or function
        result = {
            "tool": tool_name,
            "inputs": inputs,
            "output": f"Result of {tool_name} with {inputs}",
            "timestamp": time.time(),
            "status": "success"
        }
        
        # Log the tool call to the fragmented log system
        log_path = os.path.join(self.output_dir, f"{workflow_id}_tool_logs.jsonl")
        self._write_log_fragment(log_path, result)
        
        return result

    def save_snapshot(self, state_snapshot: Dict[str, Any], workflow_id: str, step_id: str) -> None:
        """
        Saves a state snapshot to a separate file.
        """
        snapshot_path = os.path.join(self.output_dir, f"{workflow_id}_snapshot_{step_id}.json")
        self._write_log_fragment(snapshot_path, state_snapshot)
        logger.debug(f"Snapshot saved for workflow {workflow_id}, step {step_id}")

    def execute_workflow(self, workflow_definition: Dict[str, Any]) -> ExecutionResult:
        """
        Executes the full workflow definition using the Event-Log architecture.
        """
        workflow_id = workflow_definition.get("id", "unknown")
        steps = workflow_definition.get("steps", [])
        
        start_time = time.time()
        execution_log = []
        final_state = {}
        
        logger.info(f"Starting execution of workflow {workflow_id} (Event-Log Arch)")

        for step in steps:
            step_id = step.get("id")
            tool_name = step.get("tool")
            inputs = step.get("inputs", {})
            
            try:
                # Execute tool call (includes jitter injection)
                tool_result = self.tool_call(tool_name, inputs, workflow_id)
                
                # Update final state
                final_state[step_id] = tool_result["output"]
                
                # Save intermediate snapshot
                self.save_snapshot(final_state, workflow_id, step_id)
                
                execution_log.append({
                    "step_id": step_id,
                    "status": "success",
                    "result": tool_result
                })
                
            except Exception as e:
                logger.error(f"Step {step_id} failed: {e}")
                execution_log.append({
                    "step_id": step_id,
                    "status": "failed",
                    "error": str(e)
                })
                # Continue execution or break based on policy (default: continue)
                continue

        end_time = time.time()
        
        result = ExecutionResult(
            workflow_id=workflow_id,
            success=all(e["status"] == "success" for e in execution_log),
            execution_log=execution_log,
            final_state=final_state,
            latency=end_time - start_time,
            architecture="event_log"
        )
        
        logger.info(f"Completed execution of workflow {workflow_id}: Success={result.success}, Latency={result.latency:.3f}s")
        return result

    def finalize(self, workflow_id: str) -> None:
        """
        Finalizes the execution for a workflow (e.g., closes files, commits logs).
        For Event-Log, this might mean ensuring all fragments are flushed.
        """
        logger.info(f"Finalizing workflow {workflow_id} in Event-Log executor")
        # No special action needed for JSONL append mode in this simulation
        pass