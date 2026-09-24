"""
Base Agent implementation for EvoMem agents.

This module defines the abstract base class for all agent variants,
providing a common interface and retrieval strategy hooks.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import random
import numpy as np
import torch
from src.utils.seeding import set_deterministic_seed


class BaseAgent(ABC):
    """
    Abstract base class for all agent variants.
    
    Defines the common interface and retrieval strategy hooks that all
    agent implementations must follow.
    """
    
    def __init__(self, name: str, seed: int = 42):
        """
        Initialize the base agent.
        
        Args:
            name (str): Name of the agent variant.
            seed (int): Random seed for reproducibility.
        """
        self.name = name
        self.seed = seed
        set_deterministic_seed(seed)
        
        # Initialize logging and metrics
        self.metrics = {
            'context_tokens': 0,
            'inference_time': 0.0,
            'success_status': False
        }
    
    @abstractmethod
    def retrieve_patches(self, task_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve relevant patches based on the task context.
        
        This method must be implemented by subclasses to define their
        specific retrieval strategy.
        
        Args:
            task_context (Dict[str, Any]): The current task context.
        
        Returns:
            List[Dict[str, Any]]: List of retrieved patches.
        """
        pass
    
    @abstractmethod
    def execute_task(self, task: Dict[str, Any], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a task using the retrieved patches.
        
        Args:
            task (Dict[str, Any]): The task to execute.
            patches (List[Dict[str, Any]]): Retrieved patches to use.
        
        Returns:
            Dict[str, Any]: Execution results including success status and output.
        """
        pass
    
    def build_context(self, patches: List[Dict[str, Any]]) -> str:
        """
        Build a context string from retrieved patches.
        
        Args:
            patches (List[Dict[str, Any]]): List of patches to include.
        
        Returns:
            str: Formatted context string.
        """
        context_parts = []
        for i, patch in enumerate(patches):
            context_parts.append(f"Patch {i+1}:\n{patch.get('content', '')}")
        return "\n\n".join(context_parts)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text (str): The text to count tokens for.
        
        Returns:
            int: Estimated token count.
        """
        # Simple approximation: 1 token ~ 4 characters
        return len(text) // 4
    
    def reset_metrics(self) -> None:
        """Reset the agent's metrics to initial state."""
        self.metrics = {
            'context_tokens': 0,
            'inference_time': 0.0,
            'success_status': False
        }
