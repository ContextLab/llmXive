from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch
from src.agents.base_agent import BaseAgent
from src.heuristics.conflict_detector import ConflictDetector, ModelResult
from src.utils.logging import get_logger, ExecutionTimer
from src.utils.seeding import set_deterministic_seed

logger = get_logger(__name__)

class EvoMemConflict(BaseAgent):
    """
    EvoMem-Conflict Agent: Retrieves memory patches based on conflict detection.
    
    Strategy:
    1. Run conflict detector on incoming state patches.
    2. If conflicts are found: Retrieve latest state + conflict patches.
    3. Fallback (FR-002, FR-007): If NO conflicts found OR detector fails:
       Retrieve latest state + 2 most recent non-conflict patches.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        threshold: float = 0.90,
        max_context_tokens: int = 4096,
        seed: int = 42
    ):
        super().__init__(max_context_tokens=max_context_tokens, seed=seed)
        self.model_name = model_name
        self.threshold = threshold
        self.detector = ConflictDetector(model_name=model_name, threshold=threshold)
        set_deterministic_seed(seed)

    def _detect_conflicts(
        self,
        patches: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Run the conflict detector on a list of patches.
        
        Returns:
            Tuple of (list_of_conflict_patches, success_flag)
            If success_flag is False, the detector failed (timeout/error).
        """
        if not patches:
            return [], True

        try:
            with ExecutionTimer("conflict_detection"):
                # The detector expects a list of dicts with 'text' or 'content' keys
                # Assuming patches have a 'state' or 'text' key based on typical usage
                # If the detector expects a specific format, we adapt here.
                # Based on T012/T013, it computes semantic contradiction scores.
                
                # We assume patches are dictionaries with a 'state' or 'text' field.
                # Let's assume 'state' as per typical state patching logic.
                texts = [p.get('state', p.get('text', str(p))) for p in patches]
                
                results = self.detector.detect_conflicts(texts)
                
                # Filter patches where score >= threshold
                conflict_patches = []
                for patch, result in zip(patches, results):
                    if result.score >= self.threshold:
                        conflict_patches.append(patch)
                        
                return conflict_patches, True

        except Exception as e:
            logger.error(f"Conflict detector failed: {e}. Triggering fallback.")
            return [], False

    def retrieve_patches(
        self,
        patches: List[Dict[str, Any]],
        task_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant patches for the current task context.
        
        Implements FR-002 and FR-007 Fallback Logic:
        - If conflicts detected: Return latest state + conflict patches.
        - If NO conflicts OR detector failure: Return latest state + 2 most recent non-conflict patches.
        """
        if not patches:
            logger.warning("No patches provided for retrieval.")
            return []

        # Ensure deterministic behavior for sorting
        set_deterministic_seed(self.seed)

        # 1. Identify the latest state patch (assumed to be the last one chronologically)
        #    If the list is not sorted, we might need to sort by timestamp.
        #    For this implementation, we assume the input list is chronological (oldest -> newest).
        latest_state = patches[-1]
        
        # 2. Run conflict detection
        conflict_patches, success = self._detect_conflicts(patches)
        
        if success and len(conflict_patches) > 0:
            logger.info(f"Detected {len(conflict_patches)} conflicting patches. Retrieving latest + conflicts.")
            # Strategy: Latest State + Conflicts
            selected = [latest_state]
            # Add conflicts, excluding the latest state if it was already included in conflicts
            for cp in conflict_patches:
                if cp != latest_state:
                    selected.append(cp)
            return selected
        
        else:
            # Fallback Logic (FR-002, FR-007)
            reason = "No conflicts detected" if success else "Detector failure"
            logger.warning(f"Triggering fallback logic: {reason}. Retrieving latest state + 2 most recent non-conflicts.")
            
            # Identify non-conflict patches
            # If detector failed, treat all as non-conflict for the purpose of fallback
            # If detector succeeded but found no conflicts, all (except latest) are non-conflicts
            
            non_conflict_candidates = []
            for p in patches:
                if p != latest_state:
                    non_conflict_candidates.append(p)
            
            # We need the 2 MOST RECENT non-conflict patches.
            # Since the list is chronological (oldest -> newest), the last 2 items are the most recent.
            # But we must exclude the latest_state itself from this count if it was the only one.
            
            # Sort candidates by time if necessary, assuming input order is time-order
            # Take the last 2 from the non-conflict list
            fallback_patches = non_conflict_candidates[-2:] if len(non_conflict_candidates) >= 2 else non_conflict_candidates
            
            selected = [latest_state] + fallback_patches
            logger.info(f"Fallback selected {len(selected)} patches (1 latest + {len(fallback_patches)} recent non-conflicts).")
            return selected

    def execute_task(
        self,
        task: Dict[str, Any],
        patches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a task using the conflict-filtered context.
        """
        selected_patches = self.retrieve_patches(patches, task)
        
        # Build context from selected patches
        context = self.build_context(selected_patches, task)
        
        # Execute the task (placeholder for actual LLM call logic)
        # In a real implementation, this would call an LLM API
        result = {
            "task_id": task.get("id"),
            "agent": "EvoMem-Conflict",
            "context_patches_count": len(selected_patches),
            "context_tokens": self.count_tokens(context),
            "success": True, # Placeholder
            "output": "Task executed with conflict-filtered context."
        }
        
        return result

def main():
    """
    Entry point for testing the EvoMemConflict agent directly.
    """
    import sys
    import json
    
    # Create a mock set of patches
    mock_patches = [
        {"id": 1, "state": "System initialized.", "timestamp": "00:00:01"},
        {"id": 2, "state": "User logged in.", "timestamp": "00:00:02"},
        {"id": 3, "state": "System initialized.", "timestamp": "00:00:03"}, # Potential conflict if logic is strict, but text is same
        {"id": 4, "state": "User logged out.", "timestamp": "00:00:04"},
        {"id": 5, "state": "System shutting down.", "timestamp": "00:00:05"} # Latest state
    ]
    
    task = {"id": "test_task_01", "instruction": "Check system status."}
    
    agent = EvoMemConflict(threshold=0.90)
    
    print("Running EvoMemConflict retrieval...")
    result = agent.execute_task(task, mock_patches)
    
    print(json.dumps(result, indent=2))
    
    if __name__ == "__main__":
        main()
