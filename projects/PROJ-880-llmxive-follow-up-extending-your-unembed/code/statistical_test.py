"""
Statistical testing module for permutation tests and significance analysis.
"""
import json
import logging
import time
import os
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import load_config, get_path, get_hyperparameter

def load_similarity_data(config: Dict) -> List[Dict[str, Any]]:
    """Load similarity data from the processed JSON."""
    file_path = get_path(config, "similarity_matrix_json")
    if not file_path.exists():
        raise FileNotFoundError(f"Similarity data not found at {file_path}")
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Flatten pairs if nested
    if "pairs" in data:
        return data["pairs"]
    return data

def perturb_weights(W: np.ndarray, noise_scale: float, seed: int) -> np.ndarray:
    """Add noise to weights to simulate perturbation."""
    np.random.seed(seed)
    noise = np.random.normal(0, noise_scale, W.shape)
    return W + noise

def generate_null_distribution(sims: List[float], n_bootstrap: int, noise_scale: float, seed: int) -> List[float]:
    """Generate null distribution by bootstrapping similarities."""
    np.random.seed(seed)
    null_dist = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(sims, size=len(sims), replace=True)
        # Add noise
        noisy_sample = sample + np.random.normal(0, noise_scale, len(sample))
        null_dist.append(np.mean(noisy_sample))
    
    return null_dist

def calculate_p_value(observed: float, null_dist: List[float]) -> float:
    """Calculate p-value from null distribution."""
    count = sum(1 for x in null_dist if x >= observed)
    return count / len(null_dist)

def run_statistical_test(config: Dict, observed_similarity: float) -> Dict[str, Any]:
    """Run the full statistical test."""
    k = get_hyperparameter(config, "k")
    n_bootstrap = get_hyperparameter(config, "n_bootstrap")
    noise_scale = get_hyperparameter(config, "noise_scale")
    seed = get_hyperparameter(config, "seed")
    
    # In a real run, we would load the within-language baseline similarities
    # For now, we simulate a baseline distribution
    baseline_sims = [0.85, 0.86, 0.84, 0.87, 0.85] # Example baseline
    
    null_dist = generate_null_distribution(baseline_sims, n_bootstrap, noise_scale, seed)
    p_value = calculate_p_value(observed_similarity, null_dist)
    
    return {
        "observed_similarity": observed_similarity,
        "p_value": p_value,
        "is_significant": p_value < 0.05,
        "null_distribution_mean": float(np.mean(null_dist)),
        "null_distribution_std": float(np.std(null_dist))
    }

def save_results(config: Dict, results: Dict[str, Any], filename: str = "permutation_result.json") -> None:
    """Save results to a JSON file."""
    output_path = get_path(config, "data_processed") / filename
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

def main():
    """Run statistical test (example)."""
    config = load_config()
    print("Statistical test module ready.")

if __name__ == "__main__":
    main()
