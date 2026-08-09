"""
Confidence-Adaptive Pruning (CAP) Classifier.

Implements the logic to classify negative candidates based on historical
confidence scores, filtering out 'consistently rejected' and 'consistently accepted'
candidates to retain only 'fluctuating' ones in the prompt.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger, debug, warning

logger = get_logger(__name__)

# Thresholds defined in spec
THRESHOLD_REJECTED = 0.1
THRESHOLD_ACCEPTED = 0.9

class CAPClassifier:
    """
    Classifies negative candidates based on student confidence history.

    Classification logic:
    - Rejected: Mean confidence < 0.1
    - Accepted: Mean confidence > 0.9
    - Fluctuating: 0.1 <= Mean confidence <= 0.9

    According to FR-003 and Constitution Principle VI:
    - 'Consistently rejected' (<0.1) are excluded (student already knows they are wrong).
    - 'Consistently accepted' (>0.9) are excluded (student already knows they are right).
    - Only 'fluctuating' candidates are retained for the NCQ prompt.

    Fallback (FR-007): If the resulting set of fluctuating candidates is empty,
    the classifier returns the full set of candidates to avoid empty prompts.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CAP classifier.

        Args:
            config: Optional configuration dictionary. Overrides default thresholds if present.
        """
        self.threshold_rejected = THRESHOLD_REJECTED
        self.threshold_accepted = THRESHOLD_ACCEPTED

        if config:
            if 'threshold_rejected' in config:
                self.threshold_rejected = config['threshold_rejected']
            if 'threshold_accepted' in config:
                self.threshold_accepted = config['threshold_accepted']

        debug(f"CAPClassifier initialized: rejected < {self.threshold_rejected}, accepted > {self.threshold_accepted}")

    def classify_candidates(
        self,
        candidates: List[Dict[str, Any]],
        confidence_history: Dict[str, List[float]]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Classify candidates into rejected, accepted, and fluctuating groups.

        Args:
            candidates: List of candidate dictionaries. Each must contain an 'id' or 'candidate_id' key.
            confidence_history: Dict mapping candidate_id -> list of historical confidence scores.

        Returns:
            Tuple of (rejected_ids, accepted_ids, fluctuating_ids).
        """
        rejected_ids = []
        accepted_ids = []
        fluctuating_ids = []

        for candidate in candidates:
            # Identify candidate ID
            cand_id = candidate.get('id') or candidate.get('candidate_id')
            if cand_id is None:
                warning(f"Candidate missing 'id' or 'candidate_id': {candidate}")
                continue

            scores = confidence_history.get(cand_id, [])

            if not scores:
                # No history: treat as fluctuating (neutral) to be safe, or reject?
                # Spec implies we classify based on history. If no history, we can't say it's consistent.
                # Default to fluctuating to include it in the prompt for evaluation.
                fluctuating_ids.append(cand_id)
                continue

            mean_conf = float(np.mean(scores))
            var_conf = float(np.var(scores))

            debug(f"Candidate {cand_id}: mean_conf={mean_conf:.3f}, var={var_conf:.3f}")

            if mean_conf < self.threshold_rejected:
                rejected_ids.append(cand_id)
            elif mean_conf > self.threshold_accepted:
                accepted_ids.append(cand_id)
            else:
                fluctuating_ids.append(cand_id)

        debug(f"Classification counts: Rejected={len(rejected_ids)}, Accepted={len(accepted_ids)}, Fluctuating={len(fluctuating_ids)}")
        return rejected_ids, accepted_ids, fluctuating_ids

    def get_pruned_candidates(
        self,
        candidates: List[Dict[str, Any]],
        confidence_history: Dict[str, List[float]],
        full_candidate_ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Determine the final list of candidates to include in the NCQ prompt.

        Logic:
        1. Classify candidates into rejected, accepted, and fluctuating.
        2. Retain only 'fluctuating' candidates.
        3. If the fluctuating set is empty, apply FR-007 fallback:
           - Return the full set of candidates (or full_candidate_ids if provided).

        Args:
            candidates: List of candidate dictionaries.
            confidence_history: Dict mapping candidate_id -> list of scores.
            full_candidate_ids: Optional list of all available candidate IDs.
                                Used for fallback if the filtered list is empty.
                                If None, uses IDs from the input `candidates` list.

        Returns:
            List of candidate IDs to include in the prompt.
        """
        # If no history is provided, return all candidates (no pruning possible)
        if not confidence_history:
            return [c.get('id') or c.get('candidate_id') for c in candidates if c.get('id') or c.get('candidate_id')]

        rejected_ids, accepted_ids, fluctuating_ids = self.classify_candidates(
            candidates, confidence_history
        )

        if not fluctuating_ids:
            # Fallback per FR-007: If all candidates are pruned (either consistently rejected or accepted),
            # we must not present an empty prompt. Return the full set.
            warning("All candidates pruned (consistently rejected or accepted). Fallback to full set (FR-007).")

            if full_candidate_ids:
                return full_candidate_ids

            # Fallback to IDs found in the input candidates list
            return [c.get('id') or c.get('candidate_id') for c in candidates if c.get('id') or c.get('candidate_id')]

        return fluctuating_ids

def classify_confidence(
    confidence_scores: List[float],
    threshold_low: float = THRESHOLD_REJECTED,
    threshold_high: float = THRESHOLD_ACCEPTED
) -> str:
    """
    Helper function to classify a single candidate's history of confidence scores.

    Args:
        confidence_scores: List of float confidence scores.
        threshold_low: Lower bound for 'fluctuating' (below is 'rejected').
        threshold_high: Upper bound for 'fluctuating' (above is 'accepted').

    Returns:
        One of: 'rejected', 'accepted', 'fluctuating'.
    """
    if not confidence_scores:
        return 'fluctuating' # Default to include if no data

    mean_conf = float(np.mean(confidence_scores))

    if mean_conf < threshold_low:
        return 'rejected'
    elif mean_conf > threshold_high:
        return 'accepted'
    else:
        return 'fluctuating'