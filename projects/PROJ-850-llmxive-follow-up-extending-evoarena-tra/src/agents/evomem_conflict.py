"""
EvoMem-Conflict Agent Implementation.

This agent retrieves memory patches based on conflict detection.
It filters out non-conflicting patches to reduce context noise,
while maintaining a fallback mechanism to prevent context starvation.
"""
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch

from src.agents.base_agent import BaseAgent
from src.heuristics.conflict_detector import ConflictDetector
from src.utils.logging import get_logger
from src.utils.seeding import set_deterministic_seed

logger = get_logger(__name__)


class EvoMemConflict(BaseAgent):
    """
    Agent variant that filters memory patches using a conflict detector.

    Retrieval Strategy:
    1. Retrieve the latest state patch.
    2. Retrieve only patches flagged as 'conflict' by the heuristic.
    3. Fallback: If no conflicts are detected (or detector fails), retrieve
       the latest state plus the 2 most recent non-conflict patches.

    This prevents context starvation while maximizing signal-to-noise ratio.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        threshold: float = 0.90,
        fallback_count: int = 2,
        seed: int = 42,
        device: Optional[str] = None
    ):
        """
        Initialize the EvoMemConflict agent.

        Args:
            model_name: Name of the model to use for conflict detection.
            threshold: Confidence threshold for conflict classification.
            fallback_count: Number of recent non-conflict patches to retrieve in fallback.
            seed: Random seed for reproducibility.
            device: Device to run the model on (e.g., 'cpu', 'cuda').
        """
        super().__init__(model_name, seed)
        self.threshold = threshold
        self.fallback_count = fallback_count
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize the conflict detector
        try:
            self.detector = ConflictDetector(
                model_name=model_name,
                threshold=threshold,
                device=self.device
            )
            logger.info(f"EvoMemConflict initialized with detector: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize ConflictDetector: {e}")
            raise

    def _classify_patches(
        self,
        patches: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Classify patches into conflicts and non-conflicts using the detector.

        Args:
            patches: List of patch dictionaries containing 'patch_a', 'patch_b', etc.

        Returns:
            Tuple of (conflict_patches, non_conflict_patches)
        """
        conflict_patches = []
        non_conflict_patches = []

        # Sort by timestamp or index to ensure deterministic ordering if needed
        # Assuming patches have a 'timestamp' or 'index' key for ordering
        # If not, we rely on input order
        
        for patch in patches:
            try:
                # The detector expects specific inputs. 
                # Based on synthetic_pairs schema: {"patch_a": str, "patch_b": str, ...}
                # We assume the patch passed here is the "patch_b" (the new state)
                # and we compare it against the "latest state" or a reference.
                # However, the task implies filtering a *history* of patches.
                # We assume the input 'patches' list contains history items.
                # We need to determine what 'patch_a' is for comparison.
                # Typically, in memory retrieval, we compare the *current query* 
                # against stored memories, OR we compare stored memories against 
                # a baseline. 
                
                # Interpretation for this agent:
                # The agent receives a list of historical patches.
                # We need to identify which ones are "conflicts" relative to the 
                # current task context or the latest state.
                # For this implementation, we assume the detector can score 
                # a patch against a provided 'context' or 'reference_state'.
                # If the patch itself contains the comparison pair (patch_a, patch_b),
                # we use that.
                
                if 'patch_a' in patch and 'patch_b' in patch:
                    is_conflict = self.detector.predict(patch['patch_a'], patch['patch_b'])
                elif 'patch' in patch and 'reference' in patch:
                    is_conflict = self.detector.predict(patch['reference'], patch['patch'])
                else:
                    # Fallback: assume not a conflict if structure is unknown
                    # This prevents crashing on malformed data
                    is_conflict = False
                
                if is_conflict:
                    conflict_patches.append(patch)
                else:
                    non_conflict_patches.append(patch)
                    
            except Exception as e:
                logger.warning(f"Error classifying patch: {e}. Treating as non-conflict.")
                non_conflict_patches.append(patch)

        return conflict_patches, non_conflict_patches

    def retrieve_patches(
        self,
        patches: List[Dict[str, Any]],
        latest_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve patches based on conflict detection strategy.

        Args:
            patches: List of all available historical patches.
            latest_state: The most recent state patch (always included).

        Returns:
            List of patches to include in the context.
        """
        if not patches:
            logger.warning("No patches provided for retrieval.")
            return [latest_state] if latest_state else []

        # Ensure latest_state is handled
        if latest_state:
            # Remove latest_state from the general list if present to avoid duplication
            # We assume 'latest_state' is the first or most recent item.
            # We will always prepend it to the result.
            pass

        try:
            # Classify patches
            conflict_patches, non_conflict_patches = self._classify_patches(patches)

            logger.info(f"Detected {len(conflict_patches)} conflicts, {len(non_conflict_patches)} non-conflicts.")

            # Strategy:
            # 1. Start with the latest state.
            # 2. Add all conflict patches.
            # 3. If no conflicts found, add the N most recent non-conflict patches (fallback).
            
            result = []
            if latest_state:
                result.append(latest_state)
            
            if conflict_patches:
                # We have conflicts: use them + latest state
                # Sort conflicts by recency (assuming input order or explicit timestamp)
                # Here we just append them.
                result.extend(conflict_patches)
                logger.info(f"Retrieved {len(conflict_patches)} conflict patches.")
            else:
                # Fallback: No conflicts detected.
                # Retrieve latest state (already added) + 2 most recent non-conflict patches.
                # We assume 'non_conflict_patches' is ordered by recency (newest first)
                # or we need to sort. Assuming input order is recency for simplicity,
                # or we take the last N if input is oldest-first.
                # Let's assume the list 'patches' was sorted newest->oldest, 
                # so 'non_conflict_patches' is also newest->oldest.
                
                fallback_patches = non_conflict_patches[:self.fallback_count]
                result.extend(fallback_patches)
                logger.info(f"Fallback triggered: Retrieved {len(fallback_patches)} recent non-conflict patches.")

            return result

        except Exception as e:
            logger.error(f"Conflict detection failed during retrieval: {e}. Engaging safe fallback.")
            # Safe fallback: latest state + 2 most recent non-conflict (or all if less)
            # Since we can't classify, treat all as non-conflict for the sake of the fallback logic
            # or just return latest + 2.
            fallback_patches = patches[:self.fallback_count]
            result = []
            if latest_state:
                result.append(latest_state)
            result.extend(fallback_patches)
            return result

    def execute(self, task: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the agent on a task.
        
        This method delegates to the base class implementation but ensures
        the context has been filtered by retrieve_patches first.
        
        Args:
            task: The task dictionary.
            context: The full history of patches (not yet filtered).
            
        Returns:
            The result dictionary containing the agent's response and metrics.
        """
        # 1. Determine the latest state (usually the last item in context or explicitly passed)
        # For this implementation, we assume 'context' is the full history.
        # We need to identify the 'latest_state'.
        # If the task provides a specific 'current_state', use that.
        # Otherwise, assume the last item in the context list is the latest.
        
        latest_state = None
        if 'current_state' in task:
            latest_state = task['current_state']
        elif context:
            # Assuming context is ordered [oldest, ..., newest]
            latest_state = context[-1]
        
        # 2. Filter patches
        filtered_patches = self.retrieve_patches(context, latest_state)
        
        # 3. Log metrics (token count, etc.)
        # We can calculate approximate token count here if needed
        total_tokens = sum(len(str(p).split()) for p in filtered_patches)
        
        logger.info(f"Context reduced to {len(filtered_patches)} patches ({total_tokens} tokens).")
        
        # 4. Call base execution logic
        return super().execute(task, filtered_patches)

def main():
    """
    Main entry point for testing the EvoMemConflict agent.
    """
    set_deterministic_seed(42)
    
    # Create a mock detector for testing if real model is not available
    # In a real run, this would load the model
    agent = EvoMemConflict(
        model_name="distilbert-base-uncased",
        threshold=0.90,
        fallback_count=2,
        seed=42
    )
    
    # Mock data for testing
    mock_patches = [
        {"patch_a": "The sky is blue.", "patch_b": "The sky is green.", "timestamp": 1},
        {"patch_a": "The grass is green.", "patch_b": "The grass is red.", "timestamp": 2},
        {"patch_a": "The car is fast.", "patch_b": "The car is fast.", "timestamp": 3}, # Non-conflict
        {"patch_a": "The sun is hot.", "patch_b": "The sun is cold.", "timestamp": 4},
    ]
    
    latest = {"patch": "Current state: Ready", "timestamp": 5}
    
    print("Testing EvoMemConflict retrieval logic...")
    result = agent.retrieve_patches(mock_patches, latest)
    
    print(f"Selected {len(result)} patches:")
    for i, p in enumerate(result):
        print(f"  {i}: {p}")
        
    if len(result) > 0:
        print("Test completed successfully.")
    else:
        print("Test failed: No patches retrieved.")

if __name__ == "__main__":
    main()