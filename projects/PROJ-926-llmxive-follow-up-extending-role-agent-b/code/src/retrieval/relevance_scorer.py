"""
Relevance Scorer for Degraded and Intervention Trajectories.

Calculates retrieval relevance scores for trajectories based on the
similarity between the failure signal (or abstracted signal) and
the task definitions in the Frozen Task Bank.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from src.config.config import DATA_PATH, SEED
from src.retrieval.task_bank import get_task_definition


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lower, strip, remove punctuation."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return ' '.join(text.split())


def _tokenize(text: str) -> List[str]:
    """Simple whitespace tokenization."""
    return _normalize_text(text).split()


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets of tokens."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def _calculate_relevance_score(failure_signal: str, task_id: str) -> float:
    """
    Calculate retrieval relevance score between a failure signal and a task definition.

    Args:
        failure_signal: The string describing the failure (raw or abstracted).
        task_id: The ID of the task definition to compare against.

    Returns:
        A float score between 0.0 and 1.0 representing relevance.
    """
    # Get task definition from the frozen task bank
    task_def = get_task_definition(task_id)
    if not task_def:
        # If task not found, return 0.0 relevance
        return 0.0

    # Extract relevant text from task definition
    task_text = task_def.get("description", "")
    task_text += " " + task_def.get("goal", "")
    task_text += " " + " ".join(task_def.get("objects", []))

    # Normalize and tokenize both texts
    failure_tokens = set(_tokenize(failure_signal))
    task_tokens = set(_tokenize(task_text))

    # Calculate Jaccard similarity
    return _jaccard_similarity(failure_tokens, task_tokens)


def score_trajectory_relevance(trajectory: Dict[str, Any]) -> float:
    """
    Calculate retrieval relevance score for a single trajectory.

    Args:
        trajectory: A dictionary containing trajectory data including
                   'task_id' and 'failure_signal' (or 'failure_reason').

    Returns:
        A float score representing the relevance of the failure to the task.
    """
    task_id = trajectory.get("task_id")
    if not task_id:
        raise ValueError("Trajectory missing 'task_id'")

    # Try to get failure signal from multiple possible keys
    failure_signal = trajectory.get("failure_signal") or trajectory.get("failure_reason") or trajectory.get("abstracted_signal")
    if not failure_signal:
        # If no failure signal, return 0.0
        return 0.0

    return _calculate_relevance_score(failure_signal, task_id)


def calculate_relevance_scores_for_cohort(
    trajectories: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Calculate retrieval relevance scores for a cohort of trajectories.

    Args:
        trajectories: List of trajectory dictionaries.
        output_path: Optional path to save the scored trajectories.

    Returns:
        List of trajectory dictionaries with added 'relevance_score' field.
    """
    scored_trajectories = []

    for traj in trajectories:
        try:
            score = score_trajectory_relevance(traj)
            scored_traj = traj.copy()
            scored_traj["relevance_score"] = score
            scored_trajectories.append(scored_traj)
        except Exception as e:
            # Log error but continue processing
            print(f"Error scoring trajectory {traj.get('id', 'unknown')}: {e}")
            # Add trajectory with 0.0 score and error marker
            scored_traj = traj.copy()
            scored_traj["relevance_score"] = 0.0
            scored_traj["scoring_error"] = str(e)
            scored_trajectories.append(scored_traj)

    # Save to output file if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scored_trajectories, f, indent=2, ensure_ascii=False)

    return scored_trajectories


def run(
    input_path: str,
    output_path: str,
    cohort_name: str = "degraded"
) -> Dict[str, Any]:
    """
    Main entry point for running relevance scoring on a cohort.

    Args:
        input_path: Path to the input JSON file containing trajectories.
        output_path: Path to save the scored trajectories.
        cohort_name: Name of the cohort (for logging purposes).

    Returns:
        Dictionary containing summary statistics of the scoring run.
    """
    # Load input trajectories
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        trajectories = json.load(f)

    if not isinstance(trajectories, list):
        raise ValueError(f"Expected list of trajectories in {input_path}, got {type(trajectories)}")

    print(f"Processing {len(trajectories)} trajectories for {cohort_name} cohort...")

    # Calculate relevance scores
    scored_trajectories = calculate_relevance_scores_for_cohort(
        trajectories,
        output_path=output_path
    )

    # Calculate summary statistics
    scores = [t["relevance_score"] for t in scored_trajectories if "relevance_score" in t]
    stats = {
        "cohort": cohort_name,
        "input_file": input_path,
        "output_file": output_path,
        "num_trajectories": len(trajectories),
        "num_successfully_scored": len(scores),
        "mean_relevance_score": sum(scores) / len(scores) if scores else 0.0,
        "min_relevance_score": min(scores) if scores else 0.0,
        "max_relevance_score": max(scores) if scores else 0.0,
        "median_relevance_score": sorted(scores)[len(scores) // 2] if scores else 0.0
    }

    print(f"Relevance scoring complete for {cohort_name} cohort.")
    print(f"Mean relevance score: {stats['mean_relevance_score']:.4f}")
    print(f"Output saved to: {output_path}")

    return stats
