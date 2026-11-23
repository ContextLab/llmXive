from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch
from src.agents.base_agent import BaseAgent
from src.utils.seeding import set_deterministic_seed

class EvoMemAll(BaseAgent):
    """
    Agent variant that retrieves the last N patches without filtering.
    This serves as the baseline for comparison.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EvoMemAll agent.

        Args:
            config: Configuration dictionary. Expected keys:
                    - 'max_context_size': Maximum number of patches to retrieve.
        """
        super().__init__(config)
        self.max_context_size = self.config.get('max_context_size', 10)
        set_deterministic_seed(self.seed)

    def retrieve_context(self, task_id: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Retrieve the last N patches from history.

        Args:
            task_id: The identifier of the current task.
            history: The history of previous states/patches.

        Returns:
            A list of the last N patches.
        """
        set_deterministic_seed(self.seed)
        # Retrieve the last N patches
        if len(history) <= self.max_context_size:
            return history
        return history[-self.max_context_size:]

    def execute(self, task_id: str, context: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Execute the task using the full context.

        Args:
            task_id: The identifier of the current task.
            context: The context (patches) retrieved for this task.

        Returns:
            A tuple containing (result_description, inference_time).
        """
        # Placeholder implementation - actual execution logic would go here
        # This ensures the agent is functional for testing
        import time
        start_time = time.time()

        # Simulate processing (in a real implementation, this would call an LLM)
        result = f"Executed task {task_id} with {len(context)} context patches."

        inference_time = time.time() - start_time
        return result, inference_time
