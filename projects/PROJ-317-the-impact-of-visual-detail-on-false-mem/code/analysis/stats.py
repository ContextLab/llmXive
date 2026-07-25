import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower
from config import get_project_root, get_data_dir

logger = logging.getLogger(__name__)

def calculate_anova_power(effect_size: float = 0.25, alpha: float = 0.05, power: float = 0.80) -> Dict[str, Any]:
    """
    Calculate required sample size for repeated measures ANOVA.
    
    Args:
        effect_size: Cohen's f effect size (default 0.25 for medium)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        
    Returns:
        Dictionary containing sample size calculation results with required keys:
        n_per_group, total_n, effect_size, power, alpha
    """
    try:
        power_analysis = FTestAnovaPower()
        # For repeated measures ANOVA with 3 conditions (baseline, enhanced, reduced)
        k_groups = 3 
        # solve_power for F-test in statsmodels expects nobs (total sample size for fixed effects)
        # However, for ANOVA F-test (fixed effects), the default interpretation is total N.
        # To be precise for repeated measures, we calculate total N required.
        # The standard FTestAnovaPower in statsmodels solves for nobs (total sample size).
        # We will solve for total N directly.
        total_n = power_analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, k_groups=k_groups)
        
        # Round up to ensure sufficient power
        total_n_ceil = int(np.ceil(total_n))
        n_per_group_ceil = int(np.ceil(total_n_ceil / k_groups))
        # Recalculate total based on per-group rounding to ensure k_groups * n_per_group >= total_n_ceil
        total_n_final = n_per_group_ceil * k_groups
        
        result = {
            "n_per_group": n_per_group_ceil,
            "total_n": total_n_final,
            "effect_size": effect_size,
            "power": power,
            "alpha": alpha,
            "groups": k_groups,
            "notes": "Calculated for repeated measures ANOVA with 3 conditions (baseline, enhanced, reduced)"
        }
        logger.info(f"Power analysis complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

def save_power_analysis(result: Dict[str, Any], filename: str = "power_report.json"):
    """Save power analysis results to JSON file in data/analysis/ directory."""
    # Ensure output path is under data/analysis/
    project_root = get_project_root()
    output_dir = project_root / "data" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis saved to {output_path}")
    return output_path

def run_repeated_measures_anova(data: np.ndarray) -> Dict[str, Any]:
    """
    Run repeated measures ANOVA on data.
    
    Args:
        data: 2D array where rows are subjects and columns are conditions
        
    Returns:
        Dictionary with ANOVA results
    """
    # Use scipy.stats.f_oneway as a simplified version
    # For true repeated measures, would need statsmodels or pingouin
    f_stat, p_val = stats.f_oneway(*data.T)
    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "degrees_of_freedom": None  # Would need full calculation
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """Apply Bonferroni correction to p-values."""
    return [min(p * num_tests, 1.0) for p in p_values]

def save_bonferroni_results(results: Dict[str, Any], filename: str = "bonferroni_results.json"):
    """Save Bonferroni correction results."""
    project_root = get_project_root()
    output_dir = project_root / "data" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def check_dataset_fit(data: np.ndarray, target_dist: str = "normal") -> Dict[str, Any]:
    """Check if dataset fits expected distribution."""
    if target_dist == "normal":
        stat, p_val = stats.normaltest(data.flatten())
        return {
            "test": "normality",
            "statistic": float(stat),
            "p_value": float(p_val),
            "is_normal": p_val > 0.05
        }
    return {}

def main():
    """Main entry point for power analysis."""
    # Calculate power analysis
    result = calculate_anova_power()
    
    # Constraint: If calculated total_n < 50, raise SystemExit with specific message
    if result['total_n'] < 50:
        error_msg = "Pipeline Halted: Insufficient Power (N < 50). Check power_report.json."
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # Save results to data/analysis/power_report.json
    save_power_analysis(result)
    print(f"Power analysis complete. Required N per group: {result['n_per_group']}, Total N: {result['total_n']}")

if __name__ == "__main__":
    main()
