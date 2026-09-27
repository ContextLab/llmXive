from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import random
import numpy as np
import torch
from src.utils.seeding import set_deterministic_seed

class BaseAgent(ABC):
    """
    Abstract base class for all agent implementations.
    Defines the interface and retrieval strategy hooks.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        # Ensure deterministic behavior by setting seed
        set_deterministic_seed()
        self.seed = 42  # Default seed, can be overridden by config

    @abstractmethod
    def retrieve_context(self, task_id: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve the context (patches) relevant to the current task.

        Args:
            task_id: The identifier of the current task.
            history: The history of previous states/patches.

        Returns:
            A list of patches to include in the context.
        """
        pass

    @abstractmethod
    def execute(self, task_id: str, context: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Execute the task using the provided context.

        Args:
            task_id: The identifier of the current task.
            context: The context (patches) retrieved for this task.

        Returns:
            A tuple containing (result_description, inference_time).
        """
        pass

    def _set_seed(self, seed: int) -> None:
        """
        Set the seed for this specific agent instance.

        Args:
            seed: The seed value to use.
        """
        self.seed = seed
        set_deterministic_seed(seed)

    def count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a string.
        Simple approximation: 1 token ≈ 4 characters.

        Args:
            text: The input string.

        Returns:
            Estimated token count.
        """
        return len(text) // 4
