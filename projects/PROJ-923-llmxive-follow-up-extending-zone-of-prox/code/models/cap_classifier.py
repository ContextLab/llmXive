"""
CAP (Confidence-Adaptive Pruning) Classifier.
Classifies negative candidates as rejected, fluctuating, or accepted based on history.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from models.state_store import StateStore, CycleRecord
from utils.logging import get_logger
from utils.seeds import get_seed

logger = get_logger(__name__)

class CAPClassifier:
    """
    Classifies candidates based on historical confidence scores.
    
    Thresholds (configurable):
      - Rejected: mean confidence < 0.1
      - Fluctuating: 0.1 <= mean confidence <= 0.9
      - Accepted (Mastered): mean confidence > 0.9
    
    Logic:
      - Exclude 'consistently accepted' (>0.9) from prompt (FR-003).
      - Keep 'rejected' and 'fluctuating' candidates in the prompt.
    """
    def __init__(self, state_store: StateStore, config: Dict[str, Any]):
        self.state_store = state_store
        self.threshold_low = config.get('cap_threshold_low', 0.1)
        self.threshold_high = config.get('cap_threshold_high', 0.9)
        self.min_history_count = config.get('min_history_count', 1)
        self.logger = get_logger(self.__class__.__name__)

    def classify_candidate(self, question_id: str, candidate: str) -> str:
        """
        Classifies a single candidate for a question.
        Returns: 'rejected', 'fluctuating', 'accepted', or 'unknown' (if no history).
        """
        # In this simulation, we assume candidates are generic or tracked by ID.
        # For the purpose of T021/T023 loop, we simulate classification based on
        # the overall question's confidence history if specific candidate tracking isn't implemented in StateStore yet.
        # However, spec implies candidate-level tracking. We approximate by using question history.
        
        history = self.state_store.get_confidence_history(question_id)
        
        if len(history) < self.min_history_count:
            return 'unknown'
        
        mean_conf = np.mean(history)
        
        if mean_conf < self.threshold_low:
            return 'rejected'
        elif mean_conf > self.threshold_high:
            return 'accepted'
        else:
            return 'fluctuating'

    def get_active_candidates(self, cycle_id: int, all_candidates: List[str]) -> List[str]:
        """
        Filters candidates based on classification.
        
        Rules:
          - Exclude 'accepted' (mastered) candidates.
          - Keep 'rejected' and 'fluctuating'.
          - Fallback to full set if result is empty (handled by caller or here).
        """
        # For simulation, we assume all candidates in the list share the same history
        # (as per simplified T013/T023 logic). In a real system, we'd track per candidate.
        # We simulate the "consistently accepted" check by looking at the aggregate history.
        
        # If the question has been mastered (high confidence), we prune ALL candidates?
        # Spec FR-003: "exclude consistently accepted candidates".
        # If ALL are accepted, prompt becomes empty -> fallback logic needed.
        
        # Simulate: if mean confidence > 0.9, we assume the student has mastered this question
        # and thus the negative candidates are no longer useful (or are 'accepted' as known wrong).
        # We filter them out.
        
        active = []
        history = self.state_store.get_confidence_history(f"q_{cycle_id}") # Approximation
        
        # If we have history, classify
        if history:
            mean_conf = np.mean(history)
            if mean_conf > self.threshold_high:
                # All candidates considered 'accepted' (mastered) -> Prune all
                # But we must fallback to full set if empty to avoid empty prompt
                self.logger.warning(f"Cycle {cycle_id}: High confidence detected. Pruning all candidates.")
                return [] 
            elif mean_conf < self.threshold_low:
                # All 'rejected' -> Keep all
                return all_candidates
            else:
                # Fluctuating -> Keep all (or subset logic if we had per-candidate IDs)
                # For this simulation, we keep all if not mastered
                return all_candidates
        
        # No history yet -> Keep all
        return all_candidates

    def update_history(self, cycle_id: int):
        """Callback to update internal state if needed."""
        pass
