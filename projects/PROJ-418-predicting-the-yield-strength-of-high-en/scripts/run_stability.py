"""
Stability assessment script for T117.

Runs the full training and evaluation pipeline three times with distinct random seeds
(42, 43, 44) and records the top-5 feature rankings for each run in output/stability_rankings.json.

This satisfies FR-021 and T144 requirements.
"""
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
import random
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, set_seeds
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline
from models.metrics_writer import write_metrics_json

logger = get_logger(__name__)

def run_single_stability_run(seed: int):
    """Run a single stability assessment run with the given seed."""
    logger.info(f"Running stability assessment with seed={seed}")
    
    # Set seeds for this run
    set_seeds(seed)
    
    # Run training
    train_success = run_training_pipeline()
    if not train_success:
        logger.error(f"Training failed for seed={seed}")
        return None

    # Run evaluation
    eval_success = run_evaluation_pipeline()
    if not eval_success:
        logger.error(f"E evaluation failed for seed={seed}")
        return None

    # Extract feature rankings from permutation importance
    # This assumes permutation_results.json exists from T044/T211
    output_dir = Path(__file__).parent.parent / "output"
    perm_path = output_dir / "permutation_results.json"
    
    if not perm_path.exists():
        logger.warning("Permutation results not found, cannot extract rankings")
        return None

    with open(perm_path, "r") as f:
        perm_data = json.load(f)
    
    # Get top-5 features by importance
    features = perm_data.get("importance_scores", {})
    sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
    top_5 = [f[0] for f in sorted_features[:5]]
    
    return {
        "seed": seed,
        "top_5_rankings": top_5,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Execute stability assessment across three runs."""
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seeds = [42, 43, 44]
    results = []
    
    logger.info("Starting stability assessment (T144)")
    
    for seed in seeds:
        result = run_single_stability_run(seed)
        if result:
            results.append(result)
            logger.info(f"Completed run for seed={seed}")
        else:
            logger.error(f"Failed run for seed={seed}")
            return False

    # Calculate rank differences
    if len(results) == 3:
        # Check if top-5 rankings are consistent across runs
        first_rankings = results[0]["top_5_rankings"]
        max_rank_diff = 0
        
        for i in range(1, 3):
            current_rankings = results[i]["top_5_rankings"]
            for j, feature in enumerate(first_rankings):
                if feature in current_rankings:
                    diff = abs(j - current_rankings.index(feature))
                    max_rank_diff = max(max_rank_diff, diff)
        
        logger.info(f"Maximum rank difference: {max_rank_diff}")
    else:
        logger.warning("Not enough runs completed, cannot calculate rank difference")
        max_rank_diff = float("inf")

    # Write stability rankings
    stability_data = {
        "runs": results,
        "max_rank_difference": max_rank_diff,
        "stability_status": "pass" if max_rank_diff <= 1 else "fail",
        "timestamp": datetime.now().isoformat()
    }
    
    stability_path = output_dir / "stability_rankings.json"
    with open(stability_path, "w") as f:
        json.dump(stability_data, f, indent=2)
    
    logger.info(f"Stability rankings written to {stability_path}")
    
    # Verify stability criterion
    if max_rank_diff <= 1:
        logger.info("Stability criterion met (rank-difference <= 1)")
        return True
    else:
        logger.warning(f"Stability criterion NOT met (rank-difference={max_rank_diff})")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
