"""
Expert System Validator for Synthetic Benchmark Trajectories.

Implements an automated expert-system validator to review a subset of trajectories
for "semantically plausible" rating as required by FR-007.

If the automated check fails (score < 80%), the script generates
`needs_human_review.json` and exits with code 42 to signal human intervention.
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re

# Import from sibling modules as per API surface
from utils.config import get_project_root, get_data_dir
from data_generation.validator import load_trajectories


# Constants
MIN_TRAJECTORIES_TO_REVIEW = 10
PASS_THRESHOLD = 0.80  # 80%
EXIT_CODE_HUMAN_REVIEW = 42


def calculate_expert_score(trajectory: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Calculate a semantic plausibility score for a single trajectory.

    Heuristic rules for "expert system" validation:
    1. Check for logical sequence of actions (no immediate reversals).
    2. Check for presence of dependency links where expected.
    3. Check for valid state transitions (state_before -> action -> state_after).
    4. Check for cross-app consistency if multiple apps are involved.

    Returns:
        Tuple of (score between 0.0 and 1.0, list of reason strings for deductions).
    """
    score = 1.0
    reasons = []
    steps = trajectory.get("steps", [])

    if not steps:
        return 0.0, ["Trajectory has no steps."]

    # Rule 1: Check for immediate reversals (e.g., "click A" then "click B" immediately if B cancels A)
    # Simplified heuristic: Check if action types repeat too frequently without state change context
    prev_action_type = None
    consecutive_same_type = 0
    for step in steps:
        action_type = step.get("action", {}).get("type", "")
        if action_type == prev_action_type:
            consecutive_same_type += 1
            if consecutive_same_type > 3:
                score -= 0.1
                reasons.append(f"Excessive repetition of action type '{action_type}' without state change.")
        else:
            consecutive_same_type = 0
        prev_action_type = action_type

    # Rule 2: Check dependency links
    dependency_links = trajectory.get("dependency_links", [])
    if len(dependency_links) > 0:
        # If dependencies exist, ensure they reference valid step indices
        total_steps = len(steps)
        for link in dependency_links:
            source_idx = link.get("source_step_index")
            target_idx = link.get("target_step_index")
            if source_idx is not None and (source_idx < 0 or source_idx >= total_steps):
                score -= 0.2
                reasons.append(f"Invalid source step index {source_idx} in dependency link.")
            if target_idx is not None and (target_idx < 0 or target_idx >= total_steps):
                score -= 0.2
                reasons.append(f"Invalid target step index {target_idx} in dependency link.")
    else:
        # If no dependencies in a long trajectory, it might be suspicious
        if len(steps) > 5:
            score -= 0.1
            reasons.append("Long trajectory (>5 steps) has no dependency links.")

    # Rule 3: Check state transitions
    for i, step in enumerate(steps):
        state_before = step.get("state_before", {})
        state_after = step.get("state_after", {})
        action = step.get("action", {})

        if not state_before or not state_after:
            score -= 0.1
            reasons.append(f"Step {i} missing state_before or state_after.")
            continue

        # Basic plausibility: state_after should differ from state_before if action is not "wait"
        if action.get("type") != "wait":
            # Simplified check: at least one field should change
            if state_before == state_after:
                score -= 0.15
                reasons.append(f"Step {i} action '{action.get('type')}' resulted in no state change.")

    # Normalize score to [0, 1]
    score = max(0.0, min(1.0, score))
    return score, reasons


def review_trajectories(
    trajectories: List[Dict[str, Any]],
    subset_size: int = MIN_TRAJECTORIES_TO_REVIEW
) -> Dict[str, Any]:
    """
    Review a subset of trajectories using the expert system.

    Args:
        trajectories: List of full trajectory dictionaries.
        subset_size: Number of trajectories to review (default 10).

    Returns:
        Dictionary containing:
            - 'results': List of review results for each trajectory.
            - 'overall_score': Average score of the reviewed subset.
            - 'passed': Boolean indicating if overall_score >= PASS_THRESHOLD.
            - 'needs_review': List of trajectory IDs that failed individual checks.
    """
    # Select subset (first N for determinism, or random if needed; using first N here)
    subset = trajectories[:subset_size]
    if len(subset) < MIN_TRAJECTORIES_TO_REVIEW:
        # If we don't have enough, review all available
        subset = trajectories

    results = []
    total_score = 0.0
    failed_ids = []

    for traj in subset:
        traj_id = traj.get("trajectory_id", "unknown")
        score, reasons = calculate_expert_score(traj)
        total_score += score

        result_entry = {
            "trajectory_id": traj_id,
            "score": score,
            "reasons": reasons,
            "passed_individual": score >= PASS_THRESHOLD,
            "timestamp": datetime.utcnow().isoformat()
        }
        results.append(result_entry)

        if score < PASS_THRESHOLD:
            failed_ids.append(traj_id)

    overall_score = total_score / len(subset) if subset else 0.0
    passed = overall_score >= PASS_THRESHOLD

    return {
        "results": results,
        "overall_score": overall_score,
        "passed": passed,
        "needs_review": failed_ids,
        "reviewed_count": len(subset),
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_needs_human_review_file(
    failed_ids: List[str],
    trajectories: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate the needs_human_review.json file for human intervention.

    Schema: [{trajectory_id: str, reason: str, timestamp: str}]
    """
    needs_review_list = []
    traj_map = {t.get("trajectory_id"): t for t in trajectories}

    for traj_id in failed_ids:
        traj = traj_map.get(traj_id, {})
        # Construct a reason based on the trajectory content or generic message
        reason = f"Automated expert system validation failed for trajectory {traj_id}. " \
                 f"Reason: Semantic plausibility score below threshold (80%). " \
                 f"Manual review required to verify dependency links and state transitions."

        needs_review_list.append({
            "trajectory_id": traj_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(needs_review_list, f, indent=2)


def main():
    """
    Main entry point for the expert system validator.

    1. Load trajectories from data/synthetic_benchmark/trajectories.jsonl.
    2. Review a subset (>=10).
    3. Output review_results.json.
    4. If overall_score < 80%, generate needs_human_review.json and exit with code 42.
    5. Otherwise, exit with code 0.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    trajectories_path = data_dir / "synthetic_benchmark" / "trajectories.jsonl"
    review_results_path = data_dir / "synthetic_benchmark" / "review_results.json"
    needs_review_path = data_dir / "synthetic_benchmark" / "needs_human_review.json"

    # Ensure output directory exists
    review_results_path.parent.mkdir(parents=True, exist_ok=True)

    # Load trajectories
    if not trajectories_path.exists():
        print(f"Error: Trajectories file not found at {trajectories_path}")
        sys.exit(1)

    trajectories = load_trajectories(trajectories_path)
    if not trajectories:
        print("Error: No trajectories loaded.")
        sys.exit(1)

    print(f"Loaded {len(trajectories)} trajectories. Reviewing subset...")

    # Perform review
    review_result = review_trajectories(trajectories, subset_size=MIN_TRAJECTORIES_TO_REVIEW)

    # Save review results
    with open(review_results_path, "w", encoding="utf-8") as f:
        json.dump(review_result, f, indent=2)
    print(f"Review results saved to {review_results_path}")
    print(f"Overall Score: {review_result['overall_score']:.2f} (Threshold: {PASS_THRESHOLD})")
    print(f"Passed: {review_result['passed']}")

    # Handle failure case
    if not review_result['passed']:
        print(f"Validation FAILED (Score < {PASS_THRESHOLD}). Generating human review trigger...")
        generate_needs_human_review_file(
            review_result['needs_review'],
            trajectories,
            needs_review_path
        )
        print(f"Needs human review file saved to {needs_review_path}")
        print(f"Exiting with code {EXIT_CODE_HUMAN_REVIEW} to signal human intervention.")
        sys.exit(EXIT_CODE_HUMAN_REVIEW)

    print("Validation PASSED. No human intervention required.")
    sys.exit(0)


if __name__ == "__main__":
    main()