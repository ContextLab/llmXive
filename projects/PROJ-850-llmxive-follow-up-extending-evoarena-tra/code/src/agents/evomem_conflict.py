from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch

from src.agents.base_agent import BaseAgent
from src.heuristics.conflict_detector import ConflictDetector, ModelResult
from src.utils.seeding import set_deterministic_seed
from src.utils.logging import get_logger, ExecutionTimer

logger = get_logger(__name__)


class EvoMemConflict(BaseAgent):
    """
    Agent variant that retrieves only the latest state plus patches flagged as conflicts.
    
    Implements fallback logic (FR-002, FR-007):
    If the conflict detector returns no flags or fails, retrieve the latest state 
    plus the 2 most recent non-conflict patches to prevent context starvation.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        threshold: float = 0.90,
        max_patches: int = 10,
        seed: Optional[int] = None
    ):
        super().__init__(seed=seed)
        self.model_name = model_name
        self.threshold = threshold
        self.max_patches = max_patches
        
        # Initialize the conflict detector
        self.detector = ConflictDetector(
            model_name=model_name,
            threshold=threshold
        )
        
        logger.info(f"Initialized EvoMemConflict agent with model: {model_name}, threshold: {threshold}")

    def _detect_conflicts(
        self,
        patches: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Run conflict detection on a list of patches.
        
        Returns:
            Tuple of (conflict_patches, non_conflict_patches)
        """
        conflict_patches = []
        non_conflict_patches = []
        
        if not patches:
            return conflict_patches, non_conflict_patches

        try:
            # Run detection on each patch pair (current vs history)
            # For this implementation, we assume patches are ordered chronologically
            # and we check each patch against the "latest state" (first patch)
            
            # Identify the latest state (first in list, assuming chronological order)
            latest_state = patches[0] if patches else None
            history_patches = patches[1:] if len(patches) > 1 else []
            
            for patch in history_patches:
                try:
                    result = self.detector.detect_conflict(latest_state, patch)
                    if result.is_conflict:
                        conflict_patches.append(patch)
                    else:
                        non_conflict_patches.append(patch)
                except Exception as e:
                    logger.warning(f"Conflict detection failed for patch: {e}. Treating as non-conflict.")
                    non_conflict_patches.append(patch)
                    
        except Exception as e:
            logger.error(f"Conflict detection failed entirely: {e}")
            raise
        
        return conflict_patches, non_conflict_patches

    def retrieve_context(
        self,
        task: Dict[str, Any],
        memory_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context for the task based on conflict detection.
        
        Implements FR-002 and FR-007:
        - Primary: Retrieve latest state + conflict patches
        - Fallback: If no conflicts detected or detection fails, retrieve 
          latest state + 2 most recent non-conflict patches
        
        Args:
            task: The task dictionary (not used in retrieval logic but part of interface)
            memory_history: List of memory patches ordered chronologically 
                           (latest first or last - implementation assumes latest first)
                           
        Returns:
            List of patches to include in context
        """
        if not memory_history:
            logger.warning("Memory history is empty. Returning empty context.")
            return []

        # Ensure deterministic behavior if seed is set
        if self.seed is not None:
            set_deterministic_seed(self.seed)

        try:
            # Detect conflicts
            conflict_patches, non_conflict_patches = self._detect_conflicts(memory_history)
            
            # Get the latest state (first element in memory_history)
            latest_state = memory_history[0]
            
            # Primary strategy: latest state + conflict patches
            if conflict_patches:
                selected_patches = [latest_state] + conflict_patches
                logger.info(f"Retrieved {len(selected_patches)} patches: latest + {len(conflict_patches)} conflicts")
            else:
                # Fallback: No conflicts detected
                # Retrieve latest state + 2 most recent non-conflict patches
                logger.info("No conflicts detected. Activating fallback logic (FR-002, FR-007).")
                
                # Sort non-conflict patches by recency if needed (assuming they are already ordered)
                # Take the 2 most recent (first 2 in the list if ordered by recency)
                fallback_non_conflicts = non_conflict_patches[:2]
                
                selected_patches = [latest_state] + fallback_non_conflicts
                logger.info(f"Fallback: Retrieved {len(selected_patches)} patches: latest + {len(fallback_non_conflicts)} non-conflicts")
                
        except Exception as e:
            # Detection failed entirely - trigger fallback
            logger.error(f"Conflict detection failed with error: {e}. Activating fallback logic (FR-007).")
            
            latest_state = memory_history[0]
            non_conflict_patches = memory_history[1:]  # Treat all others as potential non-conflicts
            
            fallback_non_conflicts = non_conflict_patches[:2]
            selected_patches = [latest_state] + fallback_non_conflicts
            logger.info(f"Fallback (error): Retrieved {len(selected_patches)} patches: latest + {len(fallback_non_conflicts)} non-conflicts")

        # Limit to max_patches if necessary (keep latest state priority)
        if len(selected_patches) > self.max_patches:
            # Always keep the latest state
            selected_patches = [selected_patches[0]] + selected_patches[1:self.max_patches]
            logger.debug(f"Trimmed context to {self.max_patches} patches")

        return selected_patches

    def execute_task(
        self,
        task: Dict[str, Any],
        memory_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a task using the conflict-filtered context.
        
        Args:
            task: The task dictionary
            memory_history: List of memory patches
            
        Returns:
            Dictionary with execution results including context used
        """
        with ExecutionTimer() as timer:
            # Retrieve filtered context
            context = self.retrieve_context(task, memory_history)
            
            # In a full implementation, this would:
            # 1. Build prompt from context
            # 2. Call LLM
            # 3. Parse response
            # 4. Execute commands
            # 5. Return results
            
            # For this task (T021), we focus on the retrieval logic
            # which is now complete with fallback behavior
            
            result = {
                "task_id": task.get("task_id", "unknown"),
                "context_patches": len(context),
                "context": context,
                "success": True,
                "inference_time": timer.elapsed
            }
            
        return result


def main():
    """
    Main entry point for standalone testing of EvoMemConflict agent.
    Demonstrates the fallback logic when no conflicts are detected.
    """
    set_deterministic_seed(42)
    
    # Create agent instance
    agent = EvoMemConflict(
        model_name="distilbert-base-uncased",
        threshold=0.90,
        max_patches=10,
        seed=42
    )
    
    # Simulate memory history (latest state first)
    # In a real scenario, these would be actual state patches
    memory_history = [
        {"id": "state_0", "content": "Latest state of the system", "timestamp": "2023-01-01T12:00:00"},
        {"id": "patch_1", "content": "Non-conflicting update 1", "timestamp": "2023-01-01T11:00:00"},
        {"id": "patch_2", "content": "Non-conflicting update 2", "timestamp": "2023-01-01T10:00:00"},
        {"id": "patch_3", "content": "Non-conflicting update 3", "timestamp": "2023-01-01T09:00:00"},
    ]
    
    task = {"task_id": "demo_task", "instruction": "Test fallback logic"}
    
    print("Testing EvoMemConflict Agent - Fallback Logic Demonstration")
    print("=" * 60)
    print(f"Memory history size: {len(memory_history)} patches")
    print(f"Agent threshold: {agent.threshold}")
    print("-" * 60)
    
    try:
        result = agent.execute_task(task, memory_history)
        
        print(f"Task ID: {result['task_id']}")
        print(f"Context patches retrieved: {result['context_patches']}")
        print(f"Success: {result['success']}")
        print(f"Inference time: {result['inference_time']:.4f}s")
        print("-" * 60)
        print("Context content:")
        for i, patch in enumerate(result['context']):
            print(f"  [{i}] {patch['id']}: {patch['content'][:50]}...")
            
        print("-" * 60)
        print("Fallback logic executed successfully!")
        print("Expected: Latest state + 2 most recent non-conflict patches")
        print(f"Actual: {result['context_patches']} patches (should be 3 if no conflicts)")
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()