from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch
from src.agents.base_agent import BaseAgent
from src.utils.seeding import set_deterministic_seed
from src.utils.logging import get_logger, ExecutionTimer

logger = get_logger(__name__)

class EvoMemAll(BaseAgent):
    """
    Baseline agent that retrieves the last N patches from memory.
    This variant does not perform any conflict filtering; it simply
    takes the most recent N state patches to construct the context.
    """

    def __init__(
        self,
        memory_path: Path,
        n_patches: int = 10,
        seed: int = 42,
        name: str = "EvoMem-All"
    ):
        """
        Initialize the EvoMem-All agent.

        Args:
            memory_path: Path to the directory containing state patches.
            n_patches: Number of most recent patches to retrieve.
            seed: Random seed for reproducibility.
            name: Agent identifier for logging.
        """
        super().__init__(memory_path=memory_path, seed=seed, name=name)
        self.n_patches = n_patches
        set_deterministic_seed(seed)
        logger.info(f"Initialized {name} with n_patches={n_patches}")

    def retrieve_context(
        self,
        task_id: str,
        patches: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieve the last N patches from the provided list or memory.

        This implements the baseline strategy: take the most recent N patches
        regardless of their content or conflict status.

        Args:
            task_id: Identifier of the current task (for logging).
            patches: Optional list of patches. If None, loads from memory_path.

        Returns:
            Tuple of (selected_patches, context_token_count).
            context_token_count is an estimate based on string length.
        """
        if patches is None:
            patches = self._load_all_patches()
            if not patches:
                logger.warning(f"No patches found for task {task_id}.")
                return [], 0

        # Baseline logic: retrieve the last N patches
        if len(patches) <= self.n_patches:
            selected = patches
        else:
            selected = patches[-self.n_patches:]

        # Calculate approximate token count (1 token ~ 4 chars)
        context_text = "\n".join(
            [str(p.get("state_description", "")) for p in selected]
        )
        estimated_tokens = len(context_text) // 4

        logger.debug(
            f"{self.name} retrieved {len(selected)} patches for {task_id} "
            f"(est. {estimated_tokens} tokens)"
        )

        return selected, estimated_tokens

    def execute_task(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task using the retrieved context.

        For this baseline agent, execution involves retrieving the context
        and returning a mock result structure that includes the context size.
        In a full implementation, this would call an LLM.

        Args:
            task: Task dictionary containing 'task_id' and other metadata.

        Returns:
            Dictionary containing execution results (mocked for this baseline).
        """
        task_id = task.get("task_id", "unknown")
        patches = task.get("patches", [])

        with ExecutionTimer() as timer:
            selected_patches, token_count = self.retrieve_context(task_id, patches)

        # Mock execution result since we are not calling an actual LLM here
        # In a real scenario, this would involve model inference
        success = len(selected_patches) > 0

        result = {
            "task_id": task_id,
            "agent_variant": self.name,
            "context_tokens": token_count,
            "patches_retrieved": len(selected_patches),
            "success": success,
            "execution_time_ms": timer.elapsed_ms
        }

        logger.info(
            f"{self.name} completed {task_id}: "
            f"tokens={token_count}, patches={len(selected_patches)}, success={success}"
        )

        return result

    def _load_all_patches(self) -> List[Dict[str, Any]]:
        """
        Load all patches from the memory directory.
        Assumes patches are stored in JSON files or a single JSONL file.
        """
        all_patches = []
        if not self.memory_path.exists():
            logger.warning(f"Memory path {self.memory_path} does not exist.")
            return all_patches

        # Check for a single JSONL file first
        jsonl_path = self.memory_path / "patches.jsonl"
        if jsonl_path.exists():
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        all_patches.append(json.loads(line))
            return all_patches

        # Fallback: scan directory for JSON files
        for file_path in sorted(self.memory_path.glob("*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_patches.extend(data)
                else:
                    all_patches.append(data)

        return all_patches
