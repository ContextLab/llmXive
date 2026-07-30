"""
Power Analysis & Sample Size Determination (Task T008)

Estimates required sample size to detect effect size >= 0.1 using statsmodels.
Input: data/raw/marginal_counts.parquet (T013b) to estimate variance.
Output: data/power_analysis.json with N_unified.

DEFINITION FIX: If variance estimation fails or is unavailable, default N_unified
to a conservative estimate (15000) sufficient for logistic regression stability.
"""
import os
import sys
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.stats.power import tt_ind_solve_power

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.memory_monitor import check_memory_limit

def load_pilot_stats(input_path: str) -> dict:
    """
    Load marginal counts and compute variance estimates for power analysis.
    
    Args:
        input_path: Path to data/raw/marginal_counts.parquet
        
    Returns:
        Dictionary with variance estimates and sample stats
    """
    check_memory_limit(limit_mb=7168)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
        
        # Ensure we have the necessary columns
        if 'frequency' not in df.columns:
            # Try to infer from available columns
            freq_col = [c for c in df.columns if 'freq' in c.lower() or 'count' in c.lower()]
            if freq_col:
                freq_col = freq_col[0]
            else:
                raise ValueError("No frequency or count column found in marginal_counts.parquet")
        else:
            freq_col = 'frequency'
        
        # Compute variance of frequencies
        frequencies = df[freq_col].dropna()
        
        if len(frequencies) == 0:
            raise ValueError("No valid frequency data found")
        
        variance = frequencies.var()
        mean_freq = frequencies.mean()
        n_samples = len(frequencies)
        
        return {
            'variance': variance,
            'mean_frequency': mean_freq,
            'n_samples': n_samples,
            'std_dev': math.sqrt(variance)
        }
    except Exception as e:
        raise RuntimeError(f"Failed to load pilot stats: {str(e)}")

def calculate_sample_size(variance: float, effect_size: float = 0.1, 
                          power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate required sample size using t-test power analysis.
    
    Args:
        variance: Variance estimate from pilot data
        effect_size: Minimum effect size to detect (default 0.1)
        power: Desired statistical power (default 0.8)
        alpha: Significance level (default 0.05)
        
    Returns:
        Required sample size per group
    """
    if variance <= 0:
        raise ValueError("Variance must be positive")
    
    # Standard deviation
    std_dev = math.sqrt(variance)
    
    # Cohen's d = effect_size / std_dev
    # We want to detect an effect of 'effect_size' units
    # So Cohen's d = effect_size / std_dev
    cohens_d = effect_size / std_dev if std_dev > 0 else 0.1
    
    # Prevent extremely small effect sizes that would require infinite samples
    if abs(cohens_d) < 0.01:
        cohens_d = 0.01
    
    try:
        # Solve for sample size
        n_per_group = tt_ind_solve_power(
            effect_size=abs(cohens_d),
            alpha=alpha,
            power=power,
            ratio=1.0,  # Equal group sizes
            alternative='two-sided'
        )
        
        return int(math.ceil(n_per_group * 2))  # Total sample size
    except Exception as e:
        # If calculation fails, return conservative estimate
        print(f"Warning: Power calculation failed ({e}), using conservative estimate")
        return 15000

def main():
    """Main entry point for power analysis task."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "raw" / "marginal_counts.parquet"
    output_path = project_root / "data" / "power_analysis.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Default parameters
    effect_size = 0.1
    power = 0.8
    alpha = 0.05
    n_unified = 15000  # Conservative default
    
    try:
        # Load pilot statistics
        print("Loading pilot statistics...")
        stats = load_pilot_stats(str(input_path))
        
        # Calculate sample size
        print("Calculating required sample size...")
        n_unified = calculate_sample_size(
            variance=stats['variance'],
            effect_size=effect_size,
            power=power,
            alpha=alpha
        )
        
        # Ensure minimum reasonable sample size
        n_unified = max(n_unified, 1000)
        
        print(f"Calculated sample size: {n_unified}")
        
    except FileNotFoundError as e:
        print(f"Warning: {e}")
        print("Using conservative sample size estimate")
    except Exception as e:
        print(f"Warning: Power analysis failed ({e})")
        print("Using conservative sample size estimate")
    
    # Prepare output
    result = {
        "N_unified": n_unified,
        "effect_size": effect_size,
        "power": power,
        "alpha": alpha,
        "method": "tt_ind_solve_power",
        "status": "COMPLETED" if n_unified != 15000 else "DEFAULTED",
        "notes": "Conservative estimate used if variance unavailable"
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Power analysis complete. Results written to {output_path}")
    return result

if __name__ == "__main__":
    main()