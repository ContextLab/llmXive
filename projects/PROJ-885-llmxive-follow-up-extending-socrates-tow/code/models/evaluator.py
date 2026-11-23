"""
T033: Topic-localized evaluator to calculate "consensus gap" scores.
Includes helper for T020b to retrieve ideal resolution templates.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models.entities import ConflictTrajectory, SocioCognitiveStateType

@dataclass
class EvaluationResult:
    trajectory_id: str
    consensus_gap_score: float
    ideal_resolution_used: str
    details: Dict[str, Any]

# Define the "ideal resolution" templates used for evaluation.
# These are distinct from the socio-cognitive state labels.
# They represent the target state of the dialogue (resolution).
IDEAL_RESOLUTION_TEMPLATES = [
    "We have reached a mutual understanding and agreed on a path forward.",
    "Both parties feel heard and validated, and a compromise has been found.",
    "The conflict has been resolved with a solution that respects both viewpoints.",
    "We have de-escalated the tension and are now focusing on constructive dialogue.",
    "A consensus has been reached that addresses the core concerns of both sides."
]

def get_ideal_resolution_templates() -> List[str]:
    """
    Returns the list of ideal resolution templates used by the evaluator.
    Exposed for T020b audit to verify feature independence.
    """
    return IDEAL_RESOLUTION_TEMPLATES

class ConsensusGapEvaluator:
    """
    Evaluates the consensus gap between the current dialogue state and the ideal resolution.
    """
    def __init__(self):
        self.templates = get_ideal_resolution_templates()
        self.logger = logging.getLogger(__name__)

    def calculate_gap(self, dialogue_turns: List[str], current_state: SocioCognitiveStateType) -> float:
        """
        Calculates the consensus gap score.
        Higher score = larger gap (further from resolution).
        Lower score = smaller gap (closer to resolution).
        
        For this implementation, we use a simple heuristic based on keyword matching
        and state severity, as a full semantic model would require heavy resources.
        """
        # Combine turns for analysis
        full_text = " ".join(dialogue_turns).lower()
        
        # Check for resolution keywords
        resolution_keywords = ["agreed", "understand", "compromise", "resolved", "consensus", "peace", "accept"]
        found_keywords = [kw for kw in resolution_keywords if kw in full_text]
        
        # Base score: 1.0 (max gap)
        gap_score = 1.0
        
        # Reduce gap based on found keywords
        if len(found_keywords) > 0:
            gap_score -= 0.2 * len(found_keywords)
        
        # Adjust based on state severity
        state_severity_map = {
            SocioCognitiveStateType.HIGH_REACTIVITY: 0.3,
            SocioCognitiveStateType.CULTURAL_FRICTION: 0.2,
            SocioCognitiveStateType.NEUTRAL: 0.0,
            SocioCognitiveStateType.LOW_REACTIVITY: -0.1
        }
        
        severity_penalty = state_severity_map.get(current_state, 0.0)
        gap_score += severity_penalty
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, gap_score))

def calculate_consensus_gap_scores(trajectories: List[ConflictTrajectory]) -> List[EvaluationResult]:
    """
    Calculates consensus gap scores for a list of trajectories.
    """
    evaluator = ConsensusGapEvaluator()
    results = []
    
    for traj in trajectories:
        turns = [turn.text for turn in traj.turns]
        # Assume the last state is the current state for evaluation
        current_state = traj.final_state if traj.final_state else SocioCognitiveStateType.NEUTRAL
        
        gap = evaluator.calculate_gap(turns, current_state)
        
        results.append(EvaluationResult(
            trajectory_id=traj.trajectory_id,
            consensus_gap_score=gap,
            ideal_resolution_used=evaluator.templates[0], # Default template for reference
            details={"turn_count": len(turns), "state": current_state.value}
        ))
        
    return results

def main():
    """Entry point for the evaluator module (for testing/debugging)."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Evaluator module loaded. Use calculate_consensus_gap_scores to evaluate trajectories.")

if __name__ == "__main__":
    main()
