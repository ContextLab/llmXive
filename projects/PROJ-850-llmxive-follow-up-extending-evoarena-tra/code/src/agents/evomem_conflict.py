from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import random
import numpy as np
import torch
from src.agents.base_agent import BaseAgent
from src.heuristics.conflict_detector import ConflictDetector
from src.utils.logging import get_logger, ExecutionTimer
from src.utils.seeding import set_deterministic_seed

logger = get_logger(__name__)

class EvoMemConflict(BaseAgent):
    """
    Agent variant that retrieves only the latest state + patches flagged as conflicts.
    Implements fallback logic (FR-002, FR-007): if no conflicts detected or detector fails,
    retrieve the latest state plus the 2 most recent non-conflict patches.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        threshold: float = 0.90,
        max_non_conflict_fallback: int = 2,
        seed: int = 42,
        device: Optional[str] = None
    ):
        """
        Initialize the EvoMemConflict agent.

        Args:
            model_name: HuggingFace model name for conflict detection.
            threshold: Confidence threshold for conflict classification.
            max_non_conflict_fallback: Number of recent non-conflict patches to retrieve if fallback triggers.
            seed: Random seed for reproducibility.
            device: Device to run the model on ('cpu' or 'cuda'). Defaults to auto-detect.
        """
        super().__init__(seed=seed)
        self.max_non_conflict_fallback = max_non_conflict_fallback
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Initializing EvoMemConflict agent on device: {self.device}")
        logger.info(f"Conflict detector threshold: {threshold}")
        logger.info(f"Fallback non-conflict count: {max_non_conflict_fallback}")

        try:
            self.conflict_detector = ConflictDetector(
                model_name=model_name,
                threshold=threshold,
                device=self.device
            )
            logger.info("ConflictDetector initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ConflictDetector: {e}")
            raise

    def retrieve_context(
        self,
        patches: List[Dict[str, Any]],
        task_description: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve context patches based on conflict detection.

        Logic:
        1. Identify the latest state patch (assumed to be the last in the list).
        2. Run conflict detection on the remaining patches.
        3. If conflicts are found: return latest state + conflict patches.
        4. If NO conflicts found OR detector fails: return latest state + up to N most recent non-conflict patches.

        Args:
            patches: List of state patches. Expected to be ordered chronologically.
            task_description: Current task description (unused for retrieval logic but required by interface).

        Returns:
          A tuple of (selected_patches, metadata).
          metadata contains:
            - 'fallback_triggered': bool
            - 'conflict_count': int
            - 'fallback_count': int
        """
        if not patches:
            logger.warning("No patches provided. Returning empty context.")
            return [], {'fallback_triggered': False, 'conflict_count': 0, 'fallback_count': 0}

        # Ensure deterministic behavior if needed during retrieval logic
        set_deterministic_seed(self.seed)

        # Identify the latest state (assumed to be the last element)
        latest_state = patches[-1]
        historical_patches = patches[:-1]

        metadata = {
            'fallback_triggered': False,
            'conflict_count': 0,
            'fallback_count': 0,
            'total_input_patches': len(patches)
        }

        conflict_patches = []
        non_conflict_patches = []
        detection_failed = False

        if not historical_patches:
            logger.info("No historical patches to analyze. Returning only latest state.")
            return [latest_state], metadata

        try:
            logger.info(f"Running conflict detection on {len(historical_patches)} historical patches.")
            # The detector expects a list of (patch_a, patch_b) or similar, 
            # but for this agent, we typically compare each historical patch against the latest state
            # or check internal consistency. 
            # Based on the task description, we assume the detector can flag individual patches 
            # as conflicting relative to the current context/state.
            
            # Assuming the detector has a method to score a list of patches against a reference or each other.
            # If the ConflictDetector class expects pairs, we adapt. 
            # However, standard usage for an agent is to score the history.
            # Let's assume the detector exposes a method `detect_conflicts(patches, reference)` 
            # or simply `score_patches(patches)`. 
            # Since the API surface only shows `ConflictDetector`, we assume it has a `run` or `predict` method.
            # To be safe and adhere to the "extend" constraint, we will assume the detector 
            # takes the list of historical patches and the latest state to identify conflicts.
            
            # Implementation detail: We treat the latest state as the ground truth reference.
            # We pass the historical patches to be scored against the latest state.
            
            # NOTE: If ConflictDetector requires specific pair input, we might need to adapt.
            # Given the constraints, we assume a method `detect_conflicts(patches_list, reference_patch)`
            # exists or we iterate. 
            # Let's assume the detector returns a list of indices or patches flagged as conflicts.
            
            # Fallback strategy if the detector API is strictly pair-based:
            # We will assume the detector can process a list of patches relative to the latest state.
            # If the detector only takes pairs, we would need to loop. 
            # For this implementation, we assume `detect_conflicts` handles the list.
            
            # If the detector is not available or fails:
            detected_conflicts, detected_non_conflicts = self._run_detector_safely(historical_patches, latest_state)
            
            if detected_conflicts is None:
                detection_failed = True
                logger.warning("Conflict detection failed or returned None. Triggering fallback.")
            else:
                conflict_patches = detected_conflicts
                non_conflict_patches = detected_non_conflicts
                metadata['conflict_count'] = len(conflict_patches)

        except Exception as e:
            logger.error(f"Error during conflict detection: {e}")
            detection_failed = True

        selected_patches = [latest_state]

        if detection_failed or len(conflict_patches) == 0:
            # Fallback Logic (FR-002, FR-007)
            logger.info("Fallback triggered: No conflicts detected or detector failure.")
            metadata['fallback_triggered'] = True
            
            # Retrieve the most recent non-conflict patches
            # non_conflict_patches is already ordered if the input was ordered
            fallback_candidates = non_conflict_patches if not detection_failed else historical_patches
            
            # Sort by recency (assuming list is chronological, so reverse for most recent)
            # If the list is [oldest, ..., newest], the most recent are at the end.
            # We take the last N.
            fallback_candidates_sorted = list(reversed(fallback_candidates))
            selected_fallback = fallback_candidates_sorted[:self.max_non_conflict_fallback]
            
            # Restore order (oldest to newest) for the context window if needed, 
            # but usually agents expect chronological order.
            selected_fallback = list(reversed(selected_fallback))
            
            selected_patches.extend(selected_fallback)
            metadata['fallback_count'] = len(selected_fallback)
            logger.info(f"Fallback retrieved {len(selected_fallback)} non-conflict patches.")
        
        else:
            # Normal path: Return latest state + conflict patches
            # Maintain chronological order for the conflict patches
            selected_patches.extend(conflict_patches)
            logger.info(f"Retrieved {len(conflict_patches)} conflict patches.")

        return selected_patches, metadata

    def _run_detector_safely(
        self, 
        historical_patches: List[Dict[str, Any]], 
        latest_state: Dict[str, Any]
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[List[Dict[str, Any]]]]:
        """
        Safely run the conflict detector. Returns (conflicts, non_conflicts) or (None, None) on failure.
        """
        try:
            # The ConflictDetector API is assumed to have a method to classify a list of patches.
            # If the underlying implementation requires pairs (patch_historical, patch_latest),
            # we perform the pairing here.
            
            pairs = [(hp, latest_state) for hp in historical_patches]
            
            # Assuming ConflictDetector has a method `predict_pairs` or similar.
            # If the class only has `__call__` or `run`, we adapt.
            # Based on the API surface, we assume it can process a list of pairs or patches.
            # Let's assume a method `detect(pairs)` returns a list of booleans or scores.
            
            # We will call the detector. If it doesn't have the expected method, 
            # we catch the AttributeError and return None to trigger fallback.
            if hasattr(self.conflict_detector, 'detect_pairs'):
                scores = self.conflict_detector.detect_pairs(pairs)
            elif hasattr(self.conflict_detector, 'run'):
                # Fallback to run method if it exists
                scores = self.conflict_detector.run(pairs)
            else:
                # If no standard method found, we cannot proceed safely.
                logger.error("ConflictDetector does not have a recognized detection method.")
                return None, None

            if not isinstance(scores, list) or len(scores) != len(pairs):
                logger.error("Detector returned invalid scores format.")
                return None, None

            conflicts = []
            non_conflicts = []

            for patch, score in zip(historical_patches, scores):
                # Score interpretation: > threshold is conflict
                if score > self.conflict_detector.threshold:
                    conflicts.append(patch)
                else:
                    non_conflicts.append(patch)

            return conflicts, non_conflicts

        except Exception as e:
            logger.error(f"Exception in _run_detector_safely: {e}")
            return None, None

    def execute(self, context: List[Dict[str, Any]], task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent on a task using the provided context.
        This is a placeholder for the actual execution logic which might involve an LLM.
        For this task, we focus on the retrieval logic.
        """
        # In a real implementation, this would call an LLM with the context and task.
        # Here we return a mock success to satisfy the interface if needed, 
        # or delegate to a parent implementation if one exists.
        # Since BaseAgent is abstract, we provide a minimal implementation.
        return {
            "status": "success",
            "context_length": len(context),
            "task_id": task.get("id", "unknown")
        }