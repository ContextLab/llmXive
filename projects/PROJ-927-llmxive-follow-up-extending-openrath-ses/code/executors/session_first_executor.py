"""
Session-First Executor Implementation.

Implements the Session-First architecture for executing multi-agent workflows.
This executor focuses on atomic, single-object state recording (write-to-temp-then-rename).
"""
import os
import json
import time
import random
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List

from executors.base_executor import BaseExecutor, ExecutionResult
from config import ensure_directories, load_state, save_state, CORRUPTION_RATE

logger = logging.getLogger(__name__)

class SessionFirstExecutor(BaseExecutor):
    """
    Executor that implements the Session-First architecture.
    
    Key characteristics:
    - Atomic, single-object state recording
    - Write-to-temp-then-rename strategy for data integrity
    - Stochastic network delay (jitter) simulation in tool_call()
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SessionFirstExecutor.
        
        Args:
            config: Configuration dictionary containing execution parameters.
                   Expected keys: 'jitter_ms', 'seed', 'output_dir'
        """
        super().__init__(config)
        self.jitter_ms = config.get('jitter_ms', 100)
        self.output_dir = config.get('output_dir', 'data/processed/session_first')
        
        # Ensure output directory exists
        ensure_directories([self.output_dir])

    def _atomic_write(self, data: Dict[str, Any], filepath: str) -> None:
        """
        Atomically write data to a file using write-to-temp-then-rename strategy.
        
        This ensures data integrity even if the process is interrupted during write.
        
        Args:
            data: Dictionary to serialize and write.
            filepath: Target file path.
        """
        dir_path = os.path.dirname(filepath)
        ensure_directories([dir_path])
        
        # Create a temporary file in the same directory to ensure atomic rename
        fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Atomic rename
            os.replace(temp_path, filepath)
            logger.debug(f"Atomic write completed: {filepath}")
        except Exception as e:
            # Clean up temp file if something goes wrong
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e

    def tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a tool call with stochastic network delay (jitter).
        
        Implements FR-004: Stochastic network delay simulation.
        Injects a random delay between 0 and jitter_ms milliseconds.
        
        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments to pass to the tool.
        
        Returns:
            Dictionary containing tool execution result.
        """
        # FR-004: Inject stochastic network delay (jitter)
        # This simulates network latency variations in the session-first architecture
        jitter_delay = random.uniform(0, self.jitter_ms / 1000.0)  # Convert ms to seconds
        time.sleep(jitter_delay)
        
        # Simulate tool execution
        result = {
            'tool_name': tool_name,
            'arguments': arguments,
            'status': 'success',
            'output': f"Result from {tool_name}",
            'timestamp': time.time()
        }
        
        # Add some variability based on tool type
        if tool_name == 'debug_breakpoint':
            result['output'] = f"Breakpoint hit at {arguments.get('location', 'unknown')}"
        elif tool_name == 'log_analysis':
            result['output'] = f"Analyzed {arguments.get('log_size', 0)} log entries"
        elif tool_name == 'state_snapshot':
            result['output'] = {
                'snapshot_id': f"snap_{int(time.time())}",
                'state': arguments.get('state', {})
            }
        
        logger.debug(f"Tool call completed: {tool_name} (jitter: {jitter_delay*1000:.2f}ms)")
        return result

    def execute_workflow(self, workflow: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a complete workflow using the Session-First architecture.
        
        Args:
            workflow: Workflow definition containing steps and configuration.
        
        Returns:
            ExecutionResult containing execution status and final state.
        """
        workflow_id = workflow.get('id', 'unknown')
        logger.info(f"Starting Session-First execution for workflow: {workflow_id}")
        
        start_time = time.time()
        final_state = {}
        execution_log = []
        
        try:
            # Process each step in the workflow
            for step in workflow.get('steps', []):
                step_id = step.get('id', 'unknown')
                tool_name = step.get('tool', 'unknown')
                arguments = step.get('arguments', {})
                
                logger.info(f"Executing step {step_id}: {tool_name}")
                
                # Execute the tool call (with jitter simulation)
                tool_result = self.tool_call(tool_name, arguments)
                
                # Update final state atomically
                final_state[step_id] = tool_result
                
                # Log the step execution
                execution_log.append({
                    'step_id': step_id,
                    'tool_name': tool_name,
                    'result': tool_result,
                    'timestamp': time.time()
                })
                
                # Atomic write of intermediate state (Session-First characteristic)
                state_file = os.path.join(
                    self.output_dir, 
                    f"{workflow_id}_state_{step_id}.json"
                )
                self._atomic_write({
                    'workflow_id': workflow_id,
                    'step_id': step_id,
                    'state': final_state,
                    'timestamp': time.time()
                }, state_file)
            
            # Final atomic write of complete state
            final_state_file = os.path.join(
                self.output_dir, 
                f"{workflow_id}_final_state.json"
            )
            self._atomic_write({
                'workflow_id': workflow_id,
                'final_state': final_state,
                'execution_log': execution_log,
                'total_duration': time.time() - start_time,
                'timestamp': time.time()
            }, final_state_file)
            
            logger.info(f"Session-First execution completed successfully for workflow: {workflow_id}")
            
            return ExecutionResult(
                success=True,
                workflow_id=workflow_id,
                final_state=final_state,
                execution_log=execution_log,
                duration=time.time() - start_time,
                architecture='session_first'
            )
            
        except Exception as e:
            logger.error(f"Session-First execution failed for workflow {workflow_id}: {str(e)}")
            return ExecutionResult(
                success=False,
                workflow_id=workflow_id,
                final_state=final_state,
                execution_log=execution_log,
                duration=time.time() - start_time,
                architecture='session_first',
                error=str(e)
            )

    def get_architecture_type(self) -> str:
        """Return the architecture type identifier."""
        return 'session_first'

    def get_metadata(self) -> Dict[str, Any]:
        """Return executor metadata for logging and analysis."""
        return {
            'architecture': 'session_first',
            'jitter_ms': self.jitter_ms,
            'atomic_writes': True,
            'output_dir': self.output_dir
        }