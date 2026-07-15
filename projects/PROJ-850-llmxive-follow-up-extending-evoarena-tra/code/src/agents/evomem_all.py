"""
EvoMem-All Agent Implementation.

This module implements the baseline agent variant that retrieves the last N patches
from the memory history without any conflict filtering.
"""
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch

from src.agents.base_agent import BaseAgent
from src.utils.logging import get_logger, ExecutionTimer
from src.utils.seeding import set_deterministic_seed

# Configure logger for this module
logger = get_logger(__name__)


class EvoMemAll(BaseAgent):
    """
    Baseline agent that retrieves the last N patches from memory.

    This agent implements the 'EvoMem-All' strategy:
    - Retrieves the last N patches from the history regardless of content.
    - Does not perform conflict detection.
    - Serves as the baseline for comparison against EvoMem-Conflict.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        seed: int = 42
    ):
        """
        Initialize the EvoMem-All agent.

        Args:
            config: Dictionary containing agent configuration.
                    Expected keys:
                    - 'memory_window_size': int, number of patches to retrieve (N)
                    - 'model_name': str, LLM model identifier (optional)
            seed: Random seed for reproducibility.
        """
        super().__init__(config, seed)
        self.memory_window_size = config.get('memory_window_size', 50)
        logger.info(f"EvoMemAll initialized with memory_window_size={self.memory_window_size}")

    def retrieve_context(
        self,
        memory_history: List[Dict[str, Any]],
        current_task_state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve the last N patches from the memory history.

        This is the core retrieval logic for the baseline agent.
        It simply takes the last N items from the provided history.

        Args:
            memory_history: List of memory patches (dictionaries).
            current_task_state: Current state of the task (unused in this baseline).

        Returns:
            Tuple containing:
            - List of retrieved patches (context)
            - Number of patches retrieved
        """
        with ExecutionTimer("retrieve_context_evo_all") as timer:
            if not memory_history:
                logger.warning("Memory history is empty. Returning empty context.")
                return [], 0

            # Retrieve the last N patches
            start_index = max(0, len(memory_history) - self.memory_window_size)
            context_patches = memory_history[start_index:]

            num_retrieved = len(context_patches)
            logger.info(
                f"Retrieved {num_retrieved} patches (window size: {self.memory_window_size}, "
                f"total history: {len(memory_history)})"
            )

            return context_patches, num_retrieved

    def execute_task(
        self,
        task_id: str,
        task_description: str,
        memory_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a task using the retrieved context.

        This method orchestrates the retrieval and execution flow.
        Note: The actual LLM inference is delegated to the base class or a mock
        for this implementation, as the focus is on the retrieval strategy.

        Args:
            task_id: Unique identifier for the task.
            task_description: String description of the task.
            memory_history: List of memory patches.

        Returns:
            Dictionary containing execution results:
            - 'task_id': str
            - 'agent_variant': str ('EvoMem-All')
            - 'context_tokens': int (estimated)
            - 'context_patches': int
            - 'success_status': bool
            - 'inference_time': float (seconds)
            - 'retrieved_patches': List[Dict]
        """
        logger.info(f"Starting execution for task {task_id} with EvoMem-All agent")

        # Build context by retrieving patches
        context_patches, num_patches = self.retrieve_context(
            memory_history,
            {}  # Empty state for baseline
        )

        # Estimate context tokens (simple heuristic: ~50 tokens per patch)
        # In a real implementation, this would use the actual tokenizer
        estimated_tokens = sum(len(str(p)) // 5 for p in context_patches)

        # Simulate execution (in a full implementation, this would call the LLM)
        # For now, we return a successful status with the retrieved context
        result = {
            'task_id': task_id,
            'agent_variant': 'EvoMem-All',
            'context_tokens': estimated_tokens,
            'context_patches': num_patches,
            'success_status': True,  # Placeholder for actual execution result
            'inference_time': 0.0,  # Placeholder
            'retrieved_patches': context_patches
        }

        logger.info(
            f"Task {task_id} completed. Retrieved {num_patches} patches, "
            f"estimated {estimated_tokens} tokens."
        )

        return result

    def get_variant_name(self) -> str:
        """Return the name of this agent variant."""
        return "EvoMem-All"

    def _count_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.

        Args:
            text: Input text string.

        Returns:
            Estimated token count.
        """
        # Simple heuristic: 1 token ≈ 4 characters (rough estimate for English)
        # In production, use the actual tokenizer from transformers
        return max(1, len(text) // 4)