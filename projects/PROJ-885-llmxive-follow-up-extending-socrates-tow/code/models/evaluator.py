"""
Topic-localized evaluator for calculating 'consensus gap' scores.

This module implements the evaluation logic required for User Story 3.
It calculates the 'consensus gap' between LLM outputs and an ideal resolution,
independent of socio-cognitive state labels.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config import ensure_directories

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single turn or trajectory."""
    trajectory_id: str
    turn_index: int
    consensus_gap_score: float  # 0.0 (perfect consensus) to 1.0 (max divergence)
    ideal_resolution: str
    llm_output: str
    topic: str
    is_valid: bool
    error_message: Optional[str] = None


class ConsensusGapEvaluator:
    """
    Topic-localized evaluator to calculate 'consensus gap' scores.

    The consensus gap measures the divergence between an LLM's response
    and an idealized resolution for a specific conflict topic.
    Lower scores indicate better alignment with consensus/resolution.
    """

    # Ideal resolution templates for common conflict topics
    # In a real system, these might be learned or retrieved from a knowledge base
    IDEAL_RESOLUTIONS = {
        "resource_allocation": "Both parties agree on a fair distribution of resources based on established criteria.",
        "communication_breakdown": "Both parties actively listen, validate each other's perspectives, and agree on a communication protocol.",
        "goal_conflict": "Parties identify shared higher-order goals and negotiate a path that satisfies both sets of objectives.",
        "value_clash": "Parties acknowledge differing values, find common ground on mutual respect, and agree to coexist without imposing values.",
        "misunderstanding": "Clarification is achieved, both parties confirm understanding of the other's position, and the conflict is resolved.",
        "default": "Parties reach a mutually acceptable agreement that addresses the core concerns of all involved."
    }

    # Keywords indicating resolution/consensus (positive)
    RESOLUTION_KEYWORDS = [
        "agree", "agreement", "accept", "understand", "clarify", "resolve",
        "solution", "compromise", "mutual", "shared", "consensus", "collaborate",
        "acknowledge", "validate", "respect", "cooperate", "satisfy", "fair",
        "equitable", "balanced", "win-win", "accommodate", "harmonize"
    ]

    # Keywords indicating escalation/divergence (negative)
    ESCALATION_KEYWORDS = [
        "refuse", "reject", "deny", "ignore", "disagree", "conflict", "fight",
        "angry", "hostile", "aggressive", "threat", "demand", "insist", "impose",
        "blame", "accuse", "attack", "defend", "retaliate", "escalate", "worsen",
        "breakdown", "stalemate", "impasse", "deadlock"
    ]

    def __init__(self, use_simple_heuristic: bool = True):
        """
        Initialize the evaluator.

        Args:
            use_simple_heuristic: If True, uses a keyword-based heuristic.
                                  If False, would use a more complex model (placeholder).
        """
        self.use_simple_heuristic = use_simple_heuristic
        logger.info(f"ConsensusGapEvaluator initialized with heuristic={use_simple_heuristic}")

    def _extract_topic(self, text: str) -> str:
        """
        Heuristic to extract the conflict topic from text.
        In a production system, this would use NLP or a classifier.
        """
        text_lower = text.lower()

        if any(word in text_lower for word in ["resource", "budget", "money", "fund", "allocate"]):
            return "resource_allocation"
        elif any(word in text_lower for word in ["communicate", "speak", "listen", "talk", "misunderstand"]):
            return "communication_breakdown"
        elif any(word in text_lower for word in ["goal", "objective", "target", "aim", "purpose"]):
            return "goal_conflict"
        elif any(word in text_lower for word in ["value", "belief", "principle", "culture", "religion"]):
            return "value_clash"
        else:
            return "default"

    def _calculate_keyword_score(self, text: str) -> float:
        """
        Calculate a score based on presence of resolution vs escalation keywords.
        Returns a value between 0.0 (high divergence) and 1.0 (high consensus).
        """
        text_lower = text.lower()
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        words = set(text_clean.split())

        resolution_count = len(words.intersection(set(self.RESOLUTION_KEYWORDS)))
        escalation_count = len(words.intersection(set(self.ESCALATION_KEYWORDS)))

        total = resolution_count + escalation_count

        if total == 0:
            # Neutral: no strong signals, assume moderate gap
            return 0.5

        # Normalize: higher resolution count -> lower gap (higher score)
        # Score = resolution_count / total
        # Then map to gap: gap = 1 - score
        # But we want the final output to be the "gap score" (0=good, 1=bad)
        # So: gap_score = escalation_count / total

        gap_score = escalation_count / total
        return gap_score

    def _get_ideal_resolution(self, topic: str) -> str:
        """Retrieve the ideal resolution for a given topic."""
        return self.IDEAL_RESOLUTIONS.get(topic, self.IDEAL_RESOLUTIONS["default"])

    def evaluate_turn(self, trajectory_id: str, turn_index: int,
                      turn_text: str, topic: Optional[str] = None) -> EvaluationResult:
        """
        Evaluate a single turn of dialogue against an ideal resolution.

        Args:
            trajectory_id: ID of the trajectory this turn belongs to.
            turn_index: Index of the turn within the trajectory.
            turn_text: The text of the turn to evaluate.
            topic: Optional specific topic. If None, inferred from text.

        Returns:
            EvaluationResult object with the calculated consensus gap score.
        """
        try:
            if not turn_text or not isinstance(turn_text, str):
                return EvaluationResult(
                    trajectory_id=trajectory_id,
                    turn_index=turn_index,
                    consensus_gap_score=1.0,
                    ideal_resolution="",
                    llm_output=turn_text,
                    topic="unknown",
                    is_valid=False,
                    error_message="Invalid or empty turn text"
                )

            detected_topic = topic if topic else self._extract_topic(turn_text)
            ideal_resolution = self._get_ideal_resolution(detected_topic)

            if self.use_simple_heuristic:
                gap_score = self._calculate_keyword_score(turn_text)
            else:
                # Placeholder for future model-based evaluation
                # Would use a transformer to compute semantic similarity to ideal_resolution
                gap_score = 0.5  # Default neutral

            return EvaluationResult(
                trajectory_id=trajectory_id,
                turn_index=turn_index,
                consensus_gap_score=gap_score,
                ideal_resolution=ideal_resolution,
                llm_output=turn_text,
                topic=detected_topic,
                is_valid=True
            )

        except Exception as e:
            logger.error(f"Error evaluating turn {turn_index} in trajectory {trajectory_id}: {e}")
            return EvaluationResult(
                trajectory_id=trajectory_id,
                turn_index=turn_index,
                consensus_gap_score=1.0,
                ideal_resolution="",
                llm_output=turn_text,
                topic="unknown",
                is_valid=False,
                error_message=str(e)
            )

    def evaluate_trajectory(self, trajectory_data: Dict[str, Any]) -> List[EvaluationResult]:
        """
        Evaluate all turns in a trajectory.

        Args:
            trajectory_data: Dictionary containing trajectory data with a 'turns' list.

        Returns:
            List of EvaluationResult objects for each turn.
        """
        trajectory_id = trajectory_data.get("trajectory_id", "unknown")
        turns = trajectory_data.get("turns", [])

        if not turns:
            logger.warning(f"No turns found in trajectory {trajectory_id}")
            return []

        results = []
        for idx, turn in enumerate(turns):
            turn_text = turn.get("text", "")
            topic = turn.get("topic")  # Optional explicit topic

            result = self.evaluate_turn(trajectory_id, idx, turn_text, topic)
            results.append(result)

        return results

    def calculate_trajectory_aggregate(self, results: List[EvaluationResult]) -> float:
        """
        Calculate the aggregate consensus gap score for a trajectory.

        Args:
            results: List of EvaluationResult objects for the trajectory.

        Returns:
            Average consensus gap score (lower is better).
        """
        if not results:
            return 1.0  # Max gap if no data

        valid_scores = [r.consensus_gap_score for r in results if r.is_valid]

        if not valid_scores:
            return 1.0

        return np.mean(valid_scores)


def calculate_consensus_gap_scores(experiment_logs_path: str,
                                   output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to calculate consensus gap scores for all trajectories in experiment logs.

    Args:
        experiment_logs_path: Path to the experiment_logs.json file.
        output_path: Optional path to save the results. If None, results are not saved.

    Returns:
        Dictionary containing the evaluation results and summary statistics.
    """
    logger.info(f"Starting consensus gap evaluation for {experiment_logs_path}")

    # Load experiment logs
    logs_path = Path(experiment_logs_path)
    if not logs_path.exists():
        raise FileNotFoundError(f"Experiment logs not found at {experiment_logs_path}")

    with open(logs_path, 'r', encoding='utf-8') as f:
        experiment_logs = json.load(f)

    evaluator = ConsensusGapEvaluator()
    all_results = []
    trajectory_scores = {}

    # Process each log entry (assuming logs are grouped by trajectory or condition)
    # The structure of experiment_logs is expected to be a list of trajectory evaluations
    # or a dictionary with trajectory_ids as keys.
    # We handle both cases.

    if isinstance(experiment_logs, list):
        entries = experiment_logs
    elif isinstance(experiment_logs, dict):
        # If it's a dict, we might have trajectory_ids as keys
        # or it might be a single trajectory. We'll try to extract turns.
        if "trajectories" in experiment_logs:
            entries = experiment_logs["trajectories"]
        elif "turns" in experiment_logs:
            # Single trajectory case
            entries = [experiment_logs]
        else:
            # Assume keys are trajectory IDs
            entries = list(experiment_logs.values())
    else:
        raise ValueError(f"Unexpected format for experiment logs: {type(experiment_logs)}")

    for entry in entries:
        trajectory_id = entry.get("trajectory_id")
        if not trajectory_id:
            logger.warning("Skipping entry without trajectory_id")
            continue

        turns = entry.get("turns", [])
        if not turns:
            # Try to find turns in a different structure
            if "condition" in entry and "outputs" in entry:
                # Maybe it's a summary of a condition run
                # We need turn-level data to evaluate gap
                logger.warning(f"Trajectory {trajectory_id} has no turn-level data, skipping")
                continue
            continue

        # Convert to expected format if necessary
        if isinstance(turns[0], dict) and "text" in turns[0]:
            trajectory_data = {"trajectory_id": trajectory_id, "turns": turns}
        elif isinstance(turns[0], str):
            # List of strings
            trajectory_data = {
                "trajectory_id": trajectory_id,
                "turns": [{"text": t, "index": i} for i, t in enumerate(turns)]
            }
        else:
            logger.warning(f"Unexpected turn format for trajectory {trajectory_id}")
            continue

        results = evaluator.evaluate_trajectory(trajectory_data)
        all_results.extend(results)

        if results:
            avg_score = evaluator.calculate_trajectory_aggregate(results)
            trajectory_scores[trajectory_id] = avg_score

    # Calculate summary statistics
    if trajectory_scores:
        scores = list(trajectory_scores.values())
        summary = {
            "total_trajectories": len(trajectory_scores),
            "mean_gap_score": float(np.mean(scores)),
            "std_gap_score": float(np.std(scores)),
            "min_gap_score": float(np.min(scores)),
            "max_gap_score": float(np.max(scores)),
            "trajectory_scores": trajectory_scores
        }
    else:
        summary = {
            "total_trajectories": 0,
            "mean_gap_score": None,
            "std_gap_score": None,
            "min_gap_score": None,
            "max_gap_score": None,
            "trajectory_scores": {}
        }

    final_output = {
        "evaluation_timestamp": str(datetime.now()),
        "summary": summary,
        "details": [
            {
                "trajectory_id": r.trajectory_id,
                "turn_index": r.turn_index,
                "consensus_gap_score": r.consensus_gap_score,
                "topic": r.topic,
                "is_valid": r.is_valid,
                "error_message": r.error_message
            }
            for r in all_results
        ]
    }

    if output_path:
        ensure_directories(Path(output_path))
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2)
        logger.info(f"Consensus gap results saved to {output_path}")

    return final_output


def main():
    """Entry point for running the evaluator from command line."""
    import argparse
    from config import get_config_summary

    parser = argparse.ArgumentParser(description="Calculate consensus gap scores for experiment logs.")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to experiment_logs.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/consensus_gap_scores.json",
        help="Path to save the results JSON"
    )

    args = parser.parse_args()

    setup_logging()
    logger.info("Starting Consensus Gap Evaluator")

    try:
        results = calculate_consensus_gap_scores(args.input, args.output)
        print(json.dumps(results["summary"], indent=2))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    main()
