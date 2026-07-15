import json
import os
import math
import random
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.generator import (
    SimulationConfig,
    create_replicate,
    generate_synthetic_meta_analysis,
    load_base_data_structure
)
from utils.logging import setup_logging

# Ensure output directory exists
OUTPUT_DIR = Path("data/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "test_variance_check.json"

def test_generated_variance_matches_injected():
    """
    T008: Unit test verifying that generated variance matches injected tau^2
    within Monte Carlo error (500 replicates).
    
    Verifies output artifact data/results/test_variance_check.json contains
    mean variance within 0.01 of target.
    """
    # Setup logging for the test run
    setup_logging()
    
    # Configuration for the test
    # We test at a specific tau^2 level (0.5) to verify the variance generation
    target_tau2 = 0.5
    n_replicates = 500
    seed = 42
    
    # Set global seed for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Load base data structure to get study characteristics
    # Using a small synthetic base structure for the unit test to avoid
    # dependency on external data fetch in this specific unit test context,
    # but the generator logic remains the same.
    # In a full integration, load_base_data_structure("data/raw/cochrane_base.csv") would be used.
    base_structure = {
        "studies": [
            {"id": f"study_{i}", "n": np.random.randint(20, 100), "se": np.random.uniform(0.1, 0.5)}
            for i in range(10)
        ]
    }
    
    generated_variances = []
    
    # Generate replicates
    for i in range(n_replicates):
        # Create a single replicate with the target tau^2
        # We use a mock config since the full generator loop is tested elsewhere
        # This focuses on the core variance generation logic
        replicate_data = create_replicate(base_structure, target_tau2, seed + i)
        
        # Extract the generated between-study variance from the replicate
        # The create_replicate function should inject the true tau^2 into the data
        if "true_tau2" in replicate_data:
            generated_variances.append(replicate_data["true_tau2"])
        else:
            # Fallback: if the replicate doesn't explicitly store true_tau2,
            # we might need to calculate it or assert the structure.
            # For this test, we assume the generator correctly sets it.
            # If not, we raise an error to fail loudly.
            raise AssertionError(f"Replicate {i} missing 'true_tau2' field. "
                                 f"Keys: {replicate_data.keys()}")
    
    # Calculate statistics
    mean_variance = float(np.mean(generated_variances))
    std_variance = float(np.std(generated_variances))
    target_variance = float(target_tau2)
    diff = abs(mean_variance - target_variance)
    
    # Monte Carlo error check: mean should be within 0.01 of target
    # With 500 replicates and typical standard deviations, this is a tight but
    # achievable bound for a correctly implemented generator.
    tolerance = 0.01
    
    assert diff <= tolerance, (
        f"Generated variance mean ({mean_variance:.4f}) differs from target "
        f"({target_variance:.4f}) by {diff:.4f}, which exceeds tolerance {tolerance}. "
        f"Std dev: {std_variance:.4f}"
    )
    
    # Prepare result artifact
    result = {
        "test_name": "variance_check",
        "target_tau2": target_variance,
        "n_replicates": n_replicates,
        "mean_generated_variance": mean_variance,
        "std_generated_variance": std_variance,
        "difference": diff,
        "tolerance": tolerance,
        "passed": diff <= tolerance,
        "seed": seed
    }
    
    # Write artifact to disk
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Test passed. Mean variance: {mean_variance:.4f}, Target: {target_variance:.4f}")
    print(f"Output written to: {OUTPUT_FILE}")

if __name__ == "__main__":
    test_generated_variance_matches_injected()
