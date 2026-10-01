"""
Base Agent Module

Defines the abstract interface for LLM agents in the EvoMem pipeline.
Includes retrieval strategy hooks and context building utilities.
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
    Abstract base class for all agents in the EvoMem pipeline.

    Defines the standard interface for:
    - Retrieval strategies (how to select memory patches)
    - Context building (how to construct the prompt)
    - Task execution (how to run the task and log results)
    """

    def __init__(self, agent_name: str, seed: int = 42):
        """
        Initialize the base agent.

        Args:
            agent_name: Name identifier for this agent variant
            seed: Random seed for reproducibility
        """
        self.agent_name = agent_name
        self.seed = seed
        self._set_seeds(seed)

    def _set_seeds(self, seed: int) -> None:
        """Set deterministic seeds for reproducibility."""
        set_deterministic_seed(seed)

    @abstractmethod
    def retrieve_patches(
        self,
        task_id: str,
        memory_store: List[Dict[str, Any]],
        max_patches: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memory patches for the current task.

        This is the core retrieval strategy hook that each agent variant
        must implement.

        Args:
            task_id: Identifier of the current task
            memory_store: List of all available memory patches
            max_patches: Maximum number of patches to retrieve
            **kwargs: Additional strategy-specific parameters

        Returns:
            List of selected memory patches to include in context
        """
        pass

    @abstractmethod
    def build_context(
        self,
        task_description: str,
        retrieved_patches: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Build the final prompt context from task description and retrieved patches.

        Args:
            task_description: The current task instruction
            retrieved_patches: List of patches selected by retrieve_patches()
            **kwargs: Additional context-building parameters

        Returns:
            Formatted context string ready for LLM input
        """
        pass

    @abstractmethod
    def execute_task(
        self,
        task_description: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the task using the built context.

        Args:
            task_description: The current task instruction
            context: Formatted context string
            **kwargs: Execution parameters

        Returns:
            Dictionary containing execution results including:
            - success: bool
            - output: str
            - context_tokens: int
            - inference_time: float
        """
        pass

    def run(
        self,
        task: Dict[str, Any],
        memory_store: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Full pipeline execution: retrieve, build context, execute.

        Args:
            task: Task dictionary with at least 'task_id' and 'description'
            memory_store: List of all available memory patches
            **kwargs: Passed to retrieve_patches, build_context, execute_task

        Returns:
            Execution results dictionary
        """
        task_id = task.get("task_id", "unknown")
        task_description = task.get("description", "")

        # Retrieve relevant patches
        retrieved_patches = self.retrieve_patches(
            task_id=task_id,
            memory_store=memory_store,
            **kwargs
        )

        # Build context
        context = self.build_context(
            task_description=task_description,
            retrieved_patches=retrieved_patches,
            **kwargs
        )

        # Execute task
        result = self.execute_task(
            task_description=task_description,
            context=context,
            **kwargs
        )

        # Add metadata
        result["agent_variant"] = self.agent_name
        result["task_id"] = task_id
        result["patches_retrieved"] = len(retrieved_patches)

        return result

    def get_config(self) -> Dict[str, Any]:
        """Return agent configuration as a dictionary."""
        return {
            "agent_name": self.agent_name,
            "seed": self.seed,
        }