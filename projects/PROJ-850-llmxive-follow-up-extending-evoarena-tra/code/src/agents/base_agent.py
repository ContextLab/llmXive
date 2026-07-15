from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import random
import numpy as np
import torch

# Import seeding utility
try:
    from src.utils.seeding import set_deterministic_seed
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.seeding import set_deterministic_seed

# Set seed at module load time
set_deterministic_seed(42)

from src.utils.logging import get_logger, ExecutionTimer

class BaseAgent(ABC):
    """Abstract base class for all agents in the EvoArena system."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent variant
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.logger = get_logger(name)
        self.logger.info(f"Initialized {name} agent")

    @abstractmethod
    def retrieve_patches(self, task_id: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve relevant patches for the given task and history.
        
        Args:
            task_id: The ID of the current task
            history: List of previous state patches
        
        Returns:
            List of patches to include in the context
        """
        pass

    @abstractmethod
    def build_context(self, task: Dict[str, Any], patches: List[Dict[str, Any]]) -> str:
        """
        Build the context string for the LLM.
        
        Args:
            task: The current task description
            patches: List of retrieved patches
        
        Returns:
            Formatted context string
        """
        pass

    @abstractmethod
    def execute(self, task: Dict[str, Any], history: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """
        Execute the agent on a task.
        
        Args:
            task: The task to execute
            history: Previous execution history
        
        Returns:
            Tuple of (result, metrics)
        """
        pass

    def _count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        Args:
            text: The text to count tokens for
        
        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Log execution metrics.
        
        Args:
            metrics: Dictionary of metrics to log
        """
        self.logger.info(f"Metrics: {metrics}")
