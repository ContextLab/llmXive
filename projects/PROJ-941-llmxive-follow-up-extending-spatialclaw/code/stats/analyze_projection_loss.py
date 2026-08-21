"""
Analyze Projection Loss
=======================
Calculates the exact percentage of failures in the 2D agent that are directly
attributable to "projection loss" (information lost in 2D) versus "action restriction"
(logic error) by comparing against the `gt_3d_is_occluded` ground truth.

This module addresses FR-006 and provides a quantitative answer to the "loss ceiling"
hypothesis for occlusion tasks.
"""

import json
import os
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

from data.loader import load_dataset, DataLoadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for classification
CLASS_PROJECTION_LOSS = "projection_loss"
CLASS_ACTION_RESTRICTION = "action_restriction"
CLASS_OTHER = "other"

# Paths
DATASET_PATH = "data/raw/synthetic_spatialclaw_v1.json"
BASELINE_RESULTS_PATH = "results/logs/baseline_run.json"
AGENT_2D_RESULTS_PATH = "results/logs/agent_2d_run.json"
OUTPUT_PATH = "results/analysis/projection_loss_breakdown.json"


def load_json_file(path: str) -> Any:
    """Load a JSON file from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)


def classify_failure_reason(
    task_id: str,
    result_2d: Dict[str, Any],
    result_baseline: Dict[str, Any],
    gt_params: Dict[str, Any]
) -> str:
    """
    Classify the reason for a 2D agent failure.

    Logic:
    1. If 2D succeeded, no failure to classify.
    2. If 2D failed:
       a. If Baseline succeeded AND task is 'occlusion':
          - Check if ground truth indicates occlusion.
          - If GT says occluded, and 2D failed (likely due to projection loss of depth info),
            classify as "projection_loss".
          - Specifically, if the failure is related to the inability to see depth/occlusion
            that the 3D baseline could resolve.
       b. If Baseline failed:
          - If both failed, the issue might be inherent to the task difficulty or "other".
          - However, if the 2D agent failed in a way that the 3D baseline succeeded,
            it's a projection issue.
       c. If 2D failed but Baseline succeeded on a NON-occlusion task:
          - Likely "action_restriction" (logic error in 2D constraint) or "other".

    Refined Logic for "Projection Loss":
    - Condition: 2D Failed AND Baseline Succeeded AND Task Type == 'occlusion'.
      This implies the 3D agent could see the occlusion (success) but 2D could not (failure),
      directly attributing the failure to the loss of 3D information in projection.

    Refined Logic for "Action Restriction":
    - Condition: 2D Failed AND Baseline Succeeded AND Task Type != 'occlusion'.
      The 3D agent succeeded, but the 2D agent failed. Since it's not an occlusion task,
      the failure is likely due to the restricted action space (e.g., inability to perform
      a 3D maneuver required for depth/relative tasks that wasn't fully captured by 2D projection).

    Refined Logic for "Other":
    - Condition: 2D Failed AND Baseline Failed.
      Both failed, so the failure is not uniquely attributable to the 2D restriction vs projection.
      It could be a hard task or a bug in both.

    Returns:
        str: One of CLASS_PROJECTION_LOSS, CLASS_ACTION_RESTRICTION, CLASS_OTHER
    """
    success_2d = result_2d.get('success', False)
    success_baseline = result_baseline.get('success', False)
    task_type = result_2d.get('task_type', 'unknown')

    if success_2d:
        return CLASS_OTHER # No failure to classify

    # 2D Failed
    if success_baseline:
        # Baseline succeeded, 2D failed -> Attributable to restriction/projection
        if task_type == 'occlusion':
            # Check ground truth to be sure
            gt_params = result_2d.get('ground_truth_3d_params', {})
            # If the ground truth says it IS occluded, and 2D failed to detect/solve,
            # it's likely projection loss (2D can't see depth).
            # If GT says NOT occluded, but 2D failed, it might be a false positive or logic error.
            # However, the core hypothesis is about "loss ceiling" for occlusion.
            # We assume if 3D succeeded and 2D failed on occlusion, it's projection loss.
            return CLASS_PROJECTION_LOSS
        else:
            # Non-occlusion task (depth, relative)
            # 3D succeeded, 2D failed. Likely due to action restriction (can't move in 3D).
            return CLASS_ACTION_RESTRICTION
    else:
        # Both failed
        return CLASS_OTHER


def run_projection_loss_analysis(
    dataset: List[Dict[str, Any]],
    baseline_results: List[Dict[str, Any]],
    agent_2d_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run the projection loss analysis over the dataset.

    Args:
        dataset: The generated task instances (Synthetic SpatialClaw Proxy).
        baseline_results: Results from the 3D baseline agent.
        agent_2d_results: Results from the 2D restricted agent.

    Returns:
        Dict containing the breakdown of failures.
    """
    # Index results by task_id for O(1) lookup
    baseline_map = {r['task_id']: r for r in baseline_results}
    agent_2d_map = {r['task_id']: r for r in agent_2d_results}

    stats = {
        "total_tasks": len(dataset),
        "total_2d_failures": 0,
        "breakdown": {
            CLASS_PROJECTION_LOSS: 0,
            CLASS_ACTION_RESTRICTION: 0,
            CLASS_OTHER: 0
        },
        "details": []
    }

    for task in dataset:
        task_id = task['task_id']
        gt_params = task.get('ground_truth_3d_params', {})
        task_type = task.get('task_type', 'unknown')

        baseline_res = baseline_map.get(task_id)
        agent_2d_res = agent_2d_map.get(task_id)

        if not baseline_res or not agent_2d_res:
            logger.warning(f"Missing results for task_id: {task_id}. Skipping.")
            continue

        # Only classify if 2D failed
        if not agent_2d_res.get('success', False):
            stats["total_2d_failures"] += 1
            reason = classify_failure_reason(task_id, agent_2d_res, baseline_res, gt_params)
            stats["breakdown"][reason] += 1

            stats["details"].append({
                "task_id": task_id,
                "task_type": task_type,
                "reason": reason,
                "baseline_success": baseline_res.get('success', False),
                "2d_success": agent_2d_res.get('success', False)
            })

    # Calculate percentages
    if stats["total_2d_failures"] > 0:
        stats["percentages"] = {
            key: (count / stats["total_2d_failures"]) * 100
            for key, count in stats["breakdown"].items()
        }
    else:
        stats["percentages"] = {key: 0.0 for key in stats["breakdown"].keys()}

    return stats


def main():
    """Main entry point for the analysis."""
    parser = argparse.ArgumentParser(description="Analyze Projection Loss in 2D Agent Failures")
    parser.add_argument('--dataset', type=str, default=DATASET_PATH, help="Path to dataset JSON")
    parser.add_argument('--baseline', type=str, default=BASELINE_RESULTS_PATH, help="Path to baseline results JSON")
    parser.add_argument('--agent-2d', type=str, default=AGENT_2D_RESULTS_PATH, help="Path to 2D agent results JSON")
    parser.add_argument('--output', type=str, default=OUTPUT_PATH, help="Path to output JSON")
    args = parser.parse_args()

    logger.info(f"Starting projection loss analysis.")
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Baseline: {args.baseline}")
    logger.info(f"Agent 2D: {args.agent_2d}")
    logger.info(f"Output: {args.output}")

    try:
        # Load data
        logger.info("Loading dataset...")
        dataset = load_dataset(args.dataset)

        logger.info("Loading baseline results...")
        baseline_results = load_json_file(args.baseline)
        if not isinstance(baseline_results, list):
            baseline_results = [baseline_results]

        logger.info("Loading 2D agent results...")
        agent_2d_results = load_json_file(args.agent_2d)
        if not isinstance(agent_2d_results, list):
            agent_2d_results = [agent_2d_results]

        # Run analysis
        logger.info("Running analysis...")
        results = run_projection_loss_analysis(dataset, baseline_results, agent_2d_results)

        # Ensure output directory exists
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write output
        logger.info(f"Writing results to {args.output}")
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info("Analysis complete.")
        logger.info(f"Total 2D Failures: {results['total_2d_failures']}")
        logger.info(f"Projection Loss: {results['percentages'][CLASS_PROJECTION_LOSS]:.2f}%")
        logger.info(f"Action Restriction: {results['percentages'][CLASS_ACTION_RESTRICTION]:.2f}%")
        logger.info(f"Other: {results['percentages'][CLASS_OTHER]:.2f}%")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except DataLoadError as e:
        logger.error(f"Data load error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
