"""
Base abstract executor for architecture execution.

Defines the common interface for Event-Log and Session-First architectures.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import time
import random
import os

# Import config for shared constants
from config import CORRUPTION_RATE, SEED, PROCESSED_DATA_DIR, RAW_DATA_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExecutionResult:
    """Container for the result of a workflow execution."""
    
    def __init__(
        self,
        workflow_id: str,
        success: bool,
        final_state: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        error_message: Optional[str] = None,
        corrupted_entries: List[str] = None
    ):
        self.workflow_id = workflow_id
        self.success = success
        self.final_state = final_state or {}
        self.latency_ms = latency_ms
        self.error_message = error_message
        self.corrupted_entries = corrupted_entries or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "final_state": self.final_state,
            "latency_ms": self.latency_ms,
            "error_message": self.error_message,
            "corrupted_entries": self.corrupted_entries
        }


class BaseExecutor(ABC):
    """
    Abstract base class for executing multi-agent workflows.
    
    Subclasses must implement the specific storage and execution logic
    for their respective architectures (Event-Log vs Session-First).
    """
    
    def __init__(self, workflow_id: str, config: Optional[Dict[str, Any]] = None):
        self.workflow_id = workflow_id
        self.config = config or {}
        self.jitter_enabled = self.config.get('inject_jitter', True)
        self.jitter_max_ms = self.config.get('jitter_max_ms', 100)
        self.corruption_rate = self.config.get('corruption_rate', CORRUPTION_RATE)
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        
        # Ensure output directories exist
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    @abstractmethod
    def execute(self, workflow_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the workflow and return the result.
        
        Args:
            workflow_data: The workflow definition containing steps and tool calls.
            
        Returns:
            ExecutionResult containing final state, latency, and success status.
        """
        pass

    @abstractmethod
    def tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single tool call with potential network jitter.
        
        Args:
            tool_name: Name of the tool to execute.
            params: Parameters for the tool.
            
        Returns:
            Result of the tool execution.
        """
        pass

    @abstractmethod
    def save_state(self, state: Dict[str, Any], output_path: str) -> None:
        """
        Persist the final state to disk.
        
        Args:
            state: The state dictionary to save.
            output_path: Path where the state should be written.
        """
        pass

    def _inject_jitter(self) -> None:
        """Inject stochastic network delay if enabled."""
        if self.jitter_enabled:
            delay = random.uniform(0, self.jitter_max_ms / 1000.0)
            time.sleep(delay)

    def _validate_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """Basic validation of workflow structure."""
        if not isinstance(workflow_data, dict):
            logger.error("Workflow data must be a dictionary")
            return False
        
        required_keys = ['workflow_id', 'steps']
        for key in required_keys:
            if key not in workflow_data:
                logger.error(f"Missing required key: {key}")
                return False
        
        if not isinstance(workflow_data['steps'], list):
            logger.error("Steps must be a list")
            return False
        
        return True

    def _record_start(self) -> None:
        """Record the start time of execution."""
        self._start_time = time.time()

    def _record_end(self) -> None:
        """Record the end time of execution."""
        self._end_time = time.time()

    def get_latency_ms(self) -> float:
        """Calculate execution latency in milliseconds."""
        if self._start_time is None or self._end_time is None:
            return 0.0
        return (self._end_time - self._start_time) * 1000.0

    def get_state_snapshot(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a snapshot of the current state from workflow data.
        
        This is a default implementation; subclasses may override for
        architecture-specific state extraction.
        """
        return {
            "workflow_id": self.workflow_id,
            "total_steps": len(workflow_data.get('steps', [])),
            "timestamp": time.time()
        }