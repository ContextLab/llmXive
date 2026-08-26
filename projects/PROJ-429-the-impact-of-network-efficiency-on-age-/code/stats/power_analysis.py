import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy.stats import pearsonr, ttest_1samp
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SIMULATION_SEED = 42
N_ITERATIONS = 1000
TARGET_EFFECT_SIZE = 0.3
POWER_THRESHOLD = 0.80

def calculate_power_for_correlation(
    sample_size: int,
    effect_size: float,
    n_iterations: int = N_ITERATIONS,
    seed: int = SIMULATION_SEED,
    alpha: float = 0.05
) -> Tuple[float, List[bool]]:
    """
    Perform Monte Carlo power analysis for Pearson correlation.
    
    Simulates datasets with a known effect size and calculates the proportion
    of significant results (power).
    
    Args:
        sample_size: Number of participants in the simulation.
        effect_size: Target population correlation coefficient (r).
        n_iterations: Number of Monte Carlo iterations.
        seed: Random seed for reproducibility.
        alpha: Significance level (alpha).
    
    Returns:
        Tuple of (estimated_power, list_of_p_values)
    """
    np.random.seed(seed)
    significant_count = 0
    p_values = []
    
    # Pre-calculate critical t-value for two-tailed test
    # t = r * sqrt((n-2) / (1-r^2))
    # We will compare simulated t-stats against the critical t-value
    # or simply use the p-value from pearsonr directly for accuracy.
    
    logger.info(f"Starting Monte Carlo simulation: n={sample_size}, r={effect_size}, iterations={n_iterations}")
    
    for i in range(n_iterations):
        # Generate two correlated variables
        # Method: Generate X ~ N(0,1), generate Y = r*X + sqrt(1-r^2)*Z
        # where Z ~ N(0,1) is independent noise.
        # This ensures Corr(X, Y) = r exactly in expectation.
        
        X = np.random.normal(0, 1, sample_size)
        Z = np.random.normal(0, 1, sample_size)
        Y = effect_size * X + np.sqrt(1 - effect_size**2) * Z
        
        # Calculate correlation and p-value
        try:
            corr, p_val = pearsonr(X, Y)
            p_values.append(p_val)
            if p_val < alpha:
                significant_count += 1
        except Exception as e:
            # Handle edge cases (e.g., constant values, though unlikely with normal dist)
            logger.warning(f"Iteration {i} failed: {e}")
            continue
    
    power = significant_count / n_iterations
    return power, p_values

def find_mdes(
    sample_size: int,
    n_iterations: int = N_ITERATIONS,
    seed: int = SIMULATION_SEED,
    alpha: float = 0.05,
    target_power: float = 0.80
) -> float:
    """
    Find the Minimum Detectable Effect Size (MDES) for a given sample size
    and target power.
    
    Uses a binary search approach to find the smallest |r| that yields
    power >= target_power.
    """
    low, high = 0.0, 0.99
    mdes = 0.0
    
    # Binary search for MDES
    for _ in range(20): # 20 iterations is enough for high precision
        mid = (low + high) / 2
        power, _ = calculate_power_for_correlation(
            sample_size, mid, n_iterations, seed, alpha
        )
        
        if power >= target_power:
            mdes = mid
            high = mid
        else:
            low = mid
        
        if high - low < 0.001:
            break
    
    return mdes

def run_power_analysis(
    n_samples: Optional[int] = None,
    output_path: Optional[Path] = None,
    effect_size: float = TARGET_EFFECT_SIZE,
    n_iterations: int = N_ITERATIONS,
    seed: int = SIMULATION_SEED
) -> Dict:
    """
    Run the full power analysis pipeline.
    
    If n_samples is None, attempts to load sample size from existing data
    (correlation_results.csv). If that fails, defaults to a placeholder
    or raises an error depending on context.
    """
    config = {
        "target_effect_size": effect_size,
        "n_iterations": n_iterations,
        "simulation_seed": seed,
        "alpha": 0.05,
        "power_threshold": POWER_THRESHOLD
    }
    
    # Determine sample size
    if n_samples is None:
        # Try to infer from existing correlation results
        metrics_path = Path("data/results/correlation_results.csv")
        if metrics_path.exists():
            try:
                df = pd.read_csv(metrics_path)
                # Get the maximum 'n' reported in the file
                if 'n' in df.columns:
                    n_samples = int(df['n'].max())
                    logger.info(f"Inferred sample size from correlation_results.csv: {n_samples}")
                else:
                    raise ValueError("Column 'n' not found in correlation_results.csv")
            except Exception as e:
                logger.warning(f"Could not infer sample size from data: {e}")
                logger.warning("Using a default sample size of 100 for simulation (adjust as needed).")
                n_samples = 100
        else:
            logger.warning("data/results/correlation_results.csv not found. Using default sample size of 100.")
            n_samples = 100
    
    config["sample_size"] = n_samples
    
    # Run simulation
    power, p_values = calculate_power_for_correlation(
        sample_size=n_samples,
        effect_size=effect_size,
        n_iterations=n_iterations,
        seed=seed
    )
    
    is_sufficient = power >= POWER_THRESHOLD
    
    # Calculate MDES for this sample size
    mdes = find_mdes(
        sample_size=n_samples,
        n_iterations=n_iterations,
        seed=seed
    )
    
    result = {
        "power_for_r03": round(power, 4),
        "is_sufficient": is_sufficient,
        "simulation_seed": seed,
        "sample_size": n_samples,
        "target_effect_size": effect_size,
        "minimum_detectable_effect_size": round(mdes, 4),
        "simulation_log_path": str(output_path) if output_path else "N/A",
        "configuration": config
    }
    
    # Save detailed log of p-values if needed (optional, but good for debugging)
    if output_path:
        log_data = {
            "power_result": result,
            "p_values_sample": p_values[:100]  # Store first 100 for log size management
        }
        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Update the main result path to point to this log
        result["simulation_log_path"] = str(output_path)
    
    return result

def main():
    """Entry point for the power analysis script."""
    logger.info("Starting Power Analysis (T027)")
    
    # Define output paths
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = results_dir / "power_analysis.json"
    log_file = results_dir / "power_simulation_log.json"
    
    try:
        result = run_power_analysis(
            output_path=log_file,
            effect_size=TARGET_EFFECT_SIZE,
            n_iterations=N_ITERATIONS,
            seed=SIMULATION_SEED
        )
        
        # Write final JSON output
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Power analysis complete. Results saved to {output_file}")
        logger.info(f"Power for r=0.3: {result['power_for_r03']:.4f}")
        logger.info(f"Is sufficient (>= {POWER_THRESHOLD}): {result['is_sufficient']}")
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
