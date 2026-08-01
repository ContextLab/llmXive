import os
import sys
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np

try:
    from statsmodels.stats.power import tt_ind_solve_power
except ImportError:
    print("ERROR: statsmodels is required for power analysis. Install via: pip install statsmodels")
    sys.exit(1)

def load_pilot_stats(pilot_path: str) -> float:
    """
    Load pilot data variance from marginal_counts.parquet or similar.
    Returns the variance estimate. If file is missing or empty, returns None.
    """
    if not os.path.exists(pilot_path):
        return None
    
    try:
        df = pd.read_parquet(pilot_path)
        if df.empty:
            return None
        
        # Look for a variance column or compute it from a numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return None
        
        # Use the first numeric column's variance (assuming it represents counts/frequencies)
        var_col = numeric_cols[0]
        variance = df[var_col].var()
        
        if pd.isna(variance) or variance == 0:
            return None
        
        return variance
    except Exception as e:
        print(f"Warning: Could not load pilot stats from {pilot_path}: {e}")
        return None

def calculate_sample_size(variance: float, effect_size: float = 0.1, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate unified sample size N_unified using t-test power analysis.
    Uses statsmodels.stats.power.tt_ind_solve_power.
    """
    # Standard deviation
    std_dev = math.sqrt(variance)
    
    # Cohen's d calculation: effect_size = delta / std_dev
    # We want to detect an effect of 'effect_size' units.
    # Cohen's d = effect_size / std_dev
    cohens_d = effect_size / std_dev
    
    # If Cohen's d is too small (close to 0), sample size will be huge.
    # Clamp to a reasonable minimum to avoid overflow, though this indicates a very hard effect to detect.
    if cohens_d < 1e-6:
        cohens_d = 1e-6
    
    # Calculate sample size per group
    n_per_group = tt_ind_solve_power(
        effect_size=cohens_d,
        alpha=alpha,
        power=power,
        ratio=1.0,  # equal group sizes
        alternative='two-sided'
    )
    
    # Total sample size
    n_total = int(math.ceil(n_per_group * 2))
    
    return max(n_total, 100)  # Minimum 100 samples to ensure stability

def main():
    """
    Main entry point for T008: Power Analysis.
    Reads pilot data variance, computes N_unified, and writes outputs.
    Falls back to hardcoded variance if pilot data is missing/insufficient.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    pilot_path = project_root / "data" / "raw" / "pilot_data.parquet"
    output_power_path = project_root / "data" / "power_analysis.json"
    output_split_config_path = project_root / "data" / "split_config.json"
    
    # Ensure output directory exists
    output_power_path.parent.mkdir(parents=True, exist_ok=True)
    
    variance = load_pilot_stats(str(pilot_path))
    is_fallback = False
    
    if variance is None:
        print("Pilot data missing or insufficient. Using fallback variance estimate.")
        variance = 1.0
        is_fallback = True
    
    # Calculate sample size
    n_unified = calculate_sample_size(variance)
    
    # Prepare output data
    power_analysis_data = {
        "N_unified": n_unified,
        "effect_size": 0.1,
        "power": 0.8,
        "alpha": 0.05,
        "variance_used": variance,
        "source": "pilot_data.parquet" if not is_fallback else "FALLBACK_CONSTANT",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Write power analysis JSON
    with open(output_power_path, 'w') as f:
        json.dump(power_analysis_data, f, indent=2)
    print(f"Power analysis written to {output_power_path}")
    
    # Prepare split config
    # Use N_unified as the total sample size for the split
    # Default 80/20 split
    train_size = int(n_unified * 0.8)
    test_size = n_unified - train_size
    
    split_config_data = {
        "N_unified": n_unified,
        "train_size": train_size,
        "test_size": test_size,
        "seed": 42,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Write split config JSON
    with open(output_split_config_path, 'w') as f:
        json.dump(split_config_data, f, indent=2)
    print(f"Split config written to {output_split_config_path}")

if __name__ == "__main__":
    main()
