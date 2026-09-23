from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the llmXive pipeline.
    
    This class defines the interface that all agent implementations (Baseline, Augmented, etc.)
    must adhere to. It ensures consistent execution signatures across the pipeline.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent with an optional configuration dictionary.
        
        Args:
            config: Optional dictionary containing agent-specific hyperparameters and settings.
        """
        self.config = config or {}
    
    @abstractmethod
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent on a given task.
        
        Args:
            task: Dictionary containing task details (e.g., 'instruction', 'input', 'ground_truth').
            
        Returns:
            Dictionary containing the execution result, typically including:
                - 'status': 'success' or 'failure'
                - 'output': The agent's generated response or action trace
                - 'metadata': Optional diagnostic information (latency, token usage, etc.)
        """
        pass
    
    def _log_step(self, step_name: str, details: Dict[str, Any]) -> None:
        """
        Helper method for agents to log internal steps if logging is configured.
        
        Args:
            step_name: Name of the step being executed.
            details: Dictionary of details to log.
        """
        # Default implementation does nothing; subclasses can override if they manage their own logging
        pass