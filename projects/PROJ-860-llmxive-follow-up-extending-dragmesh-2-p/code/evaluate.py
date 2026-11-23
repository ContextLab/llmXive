"""
Evaluation script for llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation.

Runs inference on novel objects using BOTH adaptive and static policies,
logging success rates with explicit 'object_id' and 'policy_type' fields
to preserve pairing structure for FR-005.
"""

import os
import sys
import json
import logging
import argparse
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Local imports based on project API surface
from environment import PhysicsEnvironment, create_cpu_environment
from estimator import VirtualTactileEstimator
from scheduler import AdaptiveRewardScheduler
from baseline_runner import StaticBaselinePolicy, run_baseline_episode
from seed_config import set_seeds, get_seed
from logging_config import setup_evaluation_logger

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
EVAL_LOG_PATH = DATA_RESULTS_DIR / "eval_logs.csv"
TRIALS_PER_OBJECT = 50
MAX_EPISODE_STEPS = 1000
SUCCESS_THRESHOLD = 0.95  # Example threshold for task completion

def ensure_dirs():
    """Ensure output directories exist."""
    DATA_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_generated_objects() -> List[Dict[str, Any]]:
    """
    Pre-flight check: Explicitly check for the existence of data/generated/ artifacts.
    Raises FileNotFoundError if the novel object set is missing.
    """
    if not DATA_GENERATED_DIR.exists():
        raise FileNotFoundError(
            f"Data directory {DATA_GENERATED_DIR} does not exist. "
            "Please run T013a (generator.py) to generate novel objects first."
        )

    object_files = list(DATA_GENERATED_DIR.glob("*.xml"))
    if not object_files:
        raise FileNotFoundError(
            f"No XML files found in {DATA_GENERATED_DIR}. "
            "Please run T013a (generator.py) to generate novel objects first."
        )

    objects = []
    for file_path in object_files:
        # Extract object_id from filename (e.g., "obj_001.xml" -> "obj_001")
        obj_id = file_path.stem
        objects.append({
            "object_id": obj_id,
            "file_path": str(file_path),
            "friction": float(file_path.stem.split("_")[-1]) if "_" in file_path.stem else 0.5
        })
    
    return objects

def run_adaptive_episode(
    env: PhysicsEnvironment,
    object_config: Dict[str, Any],
    estimator: VirtualTactileEstimator,
    scheduler: AdaptiveRewardScheduler,
    trials: int = 1
) -> Tuple[int, int, List[float]]:
    """
    Run a single episode with the adaptive policy.
    Returns (successes, total_trials, list_of_ks).
    """
    successes = 0
    k_estimates = []

    # Load object into environment
    env.reset()
    env.load_object(object_config["file_path"])

    # Reset estimator for new episode
    estimator.reset()

    for t in range(MAX_EPISODE_STEPS):
        # Get current state
        state = env.get_state()
        
        # Estimate virtual tactile stiffness
        k_est = estimator.estimate(state["torque"], state["velocity"])
        k_estimates.append(k_est)

        # Get adaptive reward weights
        weights = scheduler.get_weights(k_est)

        # Compute action based on adaptive policy (simplified for this task)
        # In a full implementation, this would involve a policy network
        # For now, we simulate the adaptive behavior by adjusting action magnitude
        base_action = env.compute_base_action(state)
        adaptive_action = base_action * weights.get("action_scale", 1.0)

        # Apply action
        success = env.step(adaptive_action)

        if success:
            successes += 1
            break

    return successes, trials, k_estimates

def run_static_episode(
    env: PhysicsEnvironment,
    object_config: Dict[str, Any],
    trials: int = 1
) -> Tuple[int, int, List[float]]:
    """
    Run a single episode with the static baseline policy.
    Returns (successes, total_trials, list_of_ks).
    """
    successes = 0
    k_estimates = []

    # Load object into environment
    env.reset()
    env.load_object(object_config["file_path"])

    for t in range(MAX_EPISODE_STEPS):
        state = env.get_state()
        
        # Static policy: use fixed weights
        # Simulate baseline behavior
        base_action = env.compute_base_action(state)
        static_action = base_action * 0.8  # Example static scaling

        success = env.step(static_action)

        if success:
            successes += 1
            break

    return successes, trials, k_estimates

def evaluate_policy_pair(
    object_config: Dict[str, Any],
    trials: int = TRIALS_PER_OBJECT,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Evaluate both adaptive and static policies on a single object.
    Returns a dictionary with results for logging.
    """
    if seed is not None:
        set_seeds(seed)

    env = create_cpu_environment()
    estimator = VirtualTactileEstimator(window_size=5, epsilon=1e-4)
    scheduler = AdaptiveRewardScheduler()

    # Run adaptive policy
    adaptive_successes, _, _ = run_adaptive_episode(
        env, object_config, estimator, scheduler, trials=trials
    )

    # Reset environment for static policy
    env.reset()
    env.load_object(object_config["file_path"])

    # Run static policy
    static_successes, _, _ = run_static_episode(
        env, object_config, trials=trials
    )

    env.close()

    return {
        "object_id": object_config["object_id"],
        "friction": object_config.get("friction", 0.5),
        "adaptive_successes": adaptive_successes,
        "adaptive_total": trials,
        "adaptive_rate": adaptive_successes / trials if trials > 0 else 0.0,
        "static_successes": static_successes,
        "static_total": trials,
        "static_rate": static_successes / trials if trials > 0 else 0.0,
        "improvement": (adaptive_successes - static_successes) / trials if trials > 0 else 0.0
    }

def write_results_to_csv(results: List[Dict[str, Any]], output_path: Path):
    """
    Write evaluation results to CSV in append mode (streaming).
    This ensures we don't accumulate all results in memory.
    """
    fieldnames = [
        "object_id", "friction", "adaptive_successes", "adaptive_total",
        "adaptive_rate", "static_successes", "static_total", "static_rate",
        "improvement", "timestamp"
    ]

    file_exists = output_path.exists()

    with open(output_path, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for result in results:
            result["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(result)

def main():
    """Main entry point for evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate adaptive vs static policies")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--trials", type=int, default=TRIALS_PER_OBJECT, help="Number of trials per object")
    parser.add_argument("--objects", type=str, default=None, help="Specific object IDs to evaluate (comma-separated)")
    args = parser.parse_args()

    # Setup logging
    logger = setup_evaluation_logger()
    logger.info("Starting evaluation pipeline...")

    # Ensure directories exist
    ensure_dirs()

    # Load generated objects
    try:
        objects = load_generated_objects()
        logger.info(f"Loaded {len(objects)} novel objects from {DATA_GENERATED_DIR}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Filter objects if specified
    if args.objects:
        object_ids = [oid.strip() for oid in args.objects.split(",")]
        objects = [obj for obj in objects if obj["object_id"] in object_ids]
        logger.info(f"Filtered to {len(objects)} specific objects")

    if not objects:
        logger.error("No objects found to evaluate.")
        sys.exit(1)

    # Evaluate each object
    all_results = []
    for idx, obj_config in enumerate(objects):
        logger.info(f"Evaluating object {idx+1}/{len(objects)}: {obj_config['object_id']}")
        
        try:
            result = evaluate_policy_pair(
                obj_config, 
                trials=args.trials,
                seed=args.seed + idx if args.seed else None
            )
            all_results.append(result)
            
            # Write results incrementally (streaming)
            write_results_to_csv([result], EVAL_LOG_PATH)
            
            logger.info(
                f"  Adaptive: {result['adaptive_rate']:.2f}, "
                f"Static: {result['static_rate']:.2f}, "
                f"Improvement: {result['improvement']:.2f}"
            )
        except Exception as e:
            logger.error(f"Error evaluating object {obj_config['object_id']}: {str(e)}")
            continue

    # Summary
    if all_results:
        avg_adaptive = sum(r["adaptive_rate"] for r in all_results) / len(all_results)
        avg_static = sum(r["static_rate"] for r in all_results) / len(all_results)
        avg_improvement = sum(r["improvement"] for r in all_results) / len(all_results)
        
        logger.info("=" * 50)
        logger.info("EVALUATION SUMMARY")
        logger.info(f"Total objects evaluated: {len(all_results)}")
        logger.info(f"Average Adaptive Success Rate: {avg_adaptive:.4f}")
        logger.info(f"Average Static Success Rate: {avg_static:.4f}")
        logger.info(f"Average Improvement: {avg_improvement:.4f}")
        logger.info(f"Results saved to: {EVAL_LOG_PATH}")
        logger.info("=" * 50)
    else:
        logger.warning("No results were generated.")

if __name__ == "__main__":
    main()