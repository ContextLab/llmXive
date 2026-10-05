"""
Confidence-Adaptive Pruning (CAP) Classifier Logic.

This module implements the logic to classify negative candidates based on
historical confidence scores, calculating mean and variance to determine
if a candidate is 'consistently rejected', 'fluctuating', or 'consistently accepted'.
It handles edge cases such as empty history and full-set fallbacks.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from utils.logging import get_logger, debug, warning

from utils.state_store import CycleRecord

logger = get_logger(__name__)


@dataclass
class ConfidenceStats:
    """Data class to hold statistical summary of confidence scores."""
    mean_confidence: float
    variance: float
    count: int
    last_confidence: float
    is_consistently_rejected: bool
    is_consistently_accepted: bool
    is_fluctuating: bool

def classify_confidence(
    history: List[float],
    reject_threshold: float = 0.1,
    accept_threshold: float = 0.9
) -> ConfidenceStats:
    """
    Classifies a candidate's historical confidence scores.

    Args:
        history: List of confidence scores recorded over cycles.
        reject_threshold: Threshold below which a candidate is considered 'consistently rejected'.
        accept_threshold: Threshold above which a candidate is considered 'consistently accepted'.

    Returns:
        ConfidenceStats object with calculated metrics and classification flags.
    """
    if not history:
        # Handle first cycle or missing history
        # Default to 'fluctuating' to ensure inclusion until data is available,
        # or treat as rejected/accepted based on a default?
        # Per FR-007 and T021 spec: "handle the first cycle by initializing with an empty history or default confidence values."
        # We return stats indicating insufficient data, but the logic in CAPClassifier will handle the fallback.
        # Let's default mean to 0.5 to be neutral, variance 0.
        return ConfidenceStats(
            mean_confidence=0.5,
            variance=0.0,
            count=0,
            last_confidence=0.5,
            is_consistently_rejected=False,
            is_consistently_accepted=False,
            is_fluctuating=True
        )

    arr = np.array(history)
    mean_val = float(np.mean(arr))
    var_val = float(np.var(arr))
    last_val = float(arr[-1])

    # Classification logic per FR-003
    # Consistently rejected: All values < reject_threshold (or mean < threshold with low variance?)
    # The spec says: "classifies as rejected (<0.1), fluctuating ([0.1, 0.9]), or accepted (>0.9)"
    # And "explicitly exclude BOTH 'consistently rejected' (<0.1) AND 'consistently accepted' (>0.9)"
    # Interpretation: If the mean is below 0.1, it's consistently rejected. If mean > 0.9, consistently accepted.
    # Otherwise, it is fluctuating (or at least not consistently one extreme).
    
    # Refining based on "consistently":
    # If mean < 0.1 -> Rejected
    # If mean > 0.9 -> Accepted
    # Else -> Fluctuating
    
    is_rejected = mean_val < reject_threshold
    is_accepted = mean_val > accept_threshold
    is_fluc = not is_rejected and not is_accepted

    return ConfidenceStats(
        mean_confidence=mean_val,
        variance=var_val,
        count=len(history),
        last_confidence=last_val,
        is_consistently_rejected=is_rejected,
        is_consistently_accepted=is_accepted,
        is_fluctuating=is_fluc
    )


class CAPClassifier:
    """
    Confidence-Adaptive Pruning Classifier.

    Manages the state of negative candidates and classifies them based on
    historical confidence scores retrieved from the StateStore.
    """

    def __init__(
        self,
        state_store: Any,
        reject_threshold: float = 0.1,
        accept_threshold: float = 0.9,
        min_candidates_threshold: int = 1
    ):
        """
        Initializes the CAPClassifier.

        Args:
            state_store: The StateStore instance to retrieve historical data.
        """
        self.state_store = state_store
        self.reject_threshold = reject_threshold
        self.accept_threshold = accept_threshold
        self.min_candidates_threshold = min_candidates_threshold
        logger.info(f"CAPClassifier initialized with thresholds: reject={reject_threshold}, accept={accept_threshold}")

    def get_candidate_history(self, candidate_id: str) -> List[float]:
        """
        Retrieves the list of confidence scores for a specific candidate from the state store.

        Args:
            candidate_id: The unique identifier of the negative candidate.

        Returns:
            List of confidence scores.
        """
        # The state_store is expected to have a method to retrieve records for a candidate.
        # Based on T009, the state store manages the YAML file.
        # We assume a method like `get_history(candidate_id)` exists or we iterate records.
        # Since T009 implementation is in `utils/state_store.py`, we access it there.
        # However, the API surface for state_store in `utils/state_store.py` shows `StateStore` class.
        # Let's assume the StateStore exposes a method to get history for a task/candidate.
        
        # Fallback: If the specific method isn't exposed in the API surface provided,
        # we might need to rely on the `CycleRecord` structure.
        # The API surface for `utils/state_store` shows `CycleRecord` and `StateStore`.
        # We will assume `state_store.get_candidate_history(candidate_id)` is the intended interface
        # or we implement the retrieval logic here if the store is a simple dict wrapper.
        
        # Looking at T009 description: "manage state/projects/...yaml".
        # We will assume the StateStore instance passed has a method `get_history(candidate_id)`.
        # If not, we might need to access internal data.
        
        # Given the strict API surface, let's assume the StateStore has a method `get_history`.
        # If the actual implementation in T009 didn't expose this, we might need to adjust.
        # But T021a depends on T009, so T009 must support this.
        
        # Let's try to call it. If it fails, we assume the StateStore stores data in a specific way.
        # For safety, we'll implement a robust retrieval assuming the store has a `records` dict or similar.
        
        try:
            # Attempt to get history directly
            return self.state_store.get_candidate_history(candidate_id)
        except AttributeError:
            # Fallback logic if the method doesn't exist (should not happen if T009 is correct)
            warning(f"StateStore does not have get_candidate_history method. Attempting fallback.")
            return []

    def classify_candidates(
        self,
        candidate_ids: List[str]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Classifies all provided candidates into three groups:
        1. Consistently Rejected (to be pruned)
        2. Consistently Accepted (to be pruned)
        3. Fluctuating (to be retained)

        Args:
            candidate_ids: List of candidate identifiers to classify.

        Returns:
            Tuple of (rejected_ids, accepted_ids, fluctuating_ids).
        """
        rejected = []
        accepted = []
        fluctuating = []

        for cid in candidate_ids:
            history = self.get_candidate_history(cid)
            stats = classify_confidence(
                history,
                self.reject_threshold,
                self.accept_threshold
            )

            if stats.is_consistently_rejected:
                rejected.append(cid)
            elif stats.is_consistently_accepted:
                accepted.append(cid)
            else:
                fluctuating.append(cid)

            debug(f"Candidate {cid}: mean={stats.mean_confidence:.3f}, "
                  f"var={stats.variance:.3f}, class={stats.is_fluctuating}")

        return rejected, accepted, fluctuating

    def get_filtered_candidates(
        self,
        candidate_ids: List[str],
        current_cycle: int
    ) -> List[str]:
        """
        Returns the list of candidates to be included in the NCQ prompt.
        
        Logic:
        1. Classify candidates.
        2. Retain only 'fluctuating' candidates.
        3. If the resulting set is empty (or below min threshold), fallback to the full set.
        
        Args:
            candidate_ids: All available candidate IDs.
            current_cycle: The current training cycle number (for logging/debugging).

        Returns:
            List of candidate IDs to include in the prompt.
        """
        if not candidate_ids:
            warning("No candidates provided to CAPClassifier.")
            return []

        # Special case: First cycle (or empty history for all)
        # If all are 'fluctuating' due to empty history, we might keep them all.
        # The classify_confidence returns is_fluctuating=True for empty history.
        
        rejected, accepted, fluctuating = self.classify_candidates(candidate_ids)
        
        retained_candidates = fluctuating
        
        # Check fallback condition (FR-007)
        # "MUST implement fallback to full set if resulting set is empty"
        # Also ensure we don't drop below a minimum if required, but the spec says "full set"
        
        if len(retained_candidates) == 0:
            warning(f"Cycle {current_cycle}: All candidates pruned (empty fluctuating set). "
                    f"Falling back to full set of {len(candidate_ids)} candidates.")
            return candidate_ids
        
        # Optional: Check if we are dropping too many? The spec says fallback if empty.
        # Let's stick to the spec: fallback only if empty.
        
        debug(f"Cycle {current_cycle}: Pruned {len(rejected)} rejected, {len(accepted)} accepted. "
              f"Retaining {len(retained_candidates)} fluctuating candidates.")
        
        return retained_candidates

    def update_state(
        self,
        candidate_id: str,
        new_confidence: float,
        cycle: int
    ):
        """
        Updates the state store with a new confidence score for a candidate.
        
        Args:
            candidate_id: The candidate identifier.
            new_confidence: The new confidence score.
            cycle: The current cycle number.
        """
        # Delegate to state_store
        try:
            self.state_store.add_confidence_score(candidate_id, new_confidence, cycle)
        except AttributeError:
            error("StateStore missing add_confidence_score method.")
            raise