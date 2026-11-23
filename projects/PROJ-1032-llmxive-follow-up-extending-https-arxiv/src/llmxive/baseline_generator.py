"""Generate baseline statistics for seed stability verification."""
import json
import os
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

def compute_baseline_statistics(rewards: List[float], grad_norms: List[float]) -> Dict[str, float]:
    """Compute mean and variance for rewards and gradient norms."""
    if not rewards or not grad_norms:
        raise ValueError("Cannot compute statistics from empty lists")
    
    mean_reward = sum(rewards) / len(rewards)
    mean_grad = sum(grad_norms) / len(grad_norms)
    
    var_reward = sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)
    var_grad = sum((g - mean_grad) ** 2 for g in grad_norms) / len(grad_norms)
    
    return {
        "mean_reward": mean_reward,
        "variance_reward": var_reward,
        "std_reward": var_reward ** 0.5,
        "mean_grad_norm": mean_grad,
        "variance_grad_norm": var_grad,
        "std_grad_norm": var_grad ** 0.5
    }

def verify_seed_stability(stats: Dict[str, float], threshold_pct: float = 5.0) -> bool:
    """Verify if seed is stable (variance < threshold% of mean)."""
    if stats["mean_reward"] == 0:
        return False
    
    cv_reward = (stats["std_reward"] / abs(stats["mean_reward"])) * 100
    cv_grad = (stats["std_grad_norm"] / abs(stats["mean_grad_norm"])) * 100 if stats["mean_grad_norm"] != 0 else 0
    
    return cv_reward < threshold_pct and cv_grad < threshold_pct

def get_valid_seed_for_model(model_id: str, seed_pool: List[int]) -> int:
    """Select a seed from the pool for the given model."""
    # Simple deterministic selection based on model hash
    model_hash = hash(model_id) % len(seed_pool)
    return seed_pool[model_hash]

def generate_baseline_manifest(
    model_id: str,
    seed: int,
    stats: Dict[str, float],
    is_stable: bool
) -> Dict[str, Any]:
    """Generate a baseline manifest dictionary."""
    return {
        "model_id": model_id,
        "seed_id": seed,
        "mean_reward": stats["mean_reward"],
        "mean_grad_norm": stats["mean_grad_norm"],
        "variance_reward": stats["variance_reward"],
        "variance_grad_norm": stats["variance_grad_norm"],
        "status": "STABLE" if is_stable else "UNSTABLE",
        "steps_analyzed": 50
    }

def main():
    """Main entry point for baseline generation (stub for CLI)."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Baseline generator module loaded")
