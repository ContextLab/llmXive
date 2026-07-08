import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
from statsmodels.stats.power import FTestAnovaPower
from config import get_processed_dir, get_project_root

logger = logging.getLogger(__name__)

def calculate_anova_power(effect_size: float = 0.25, alpha: float = 0.05, power: float = 0.80) -> Dict[str, Any]:
    """
    Calculate required sample size for repeated measures ANOVA.
    
    Args:
        effect_size: Cohen's f effect size (default 0.25 for medium)
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        
    Returns:
        Dictionary containing sample size calculation results
    """
    try:
        power_analysis = FTestAnovaPower()
        # For repeated measures ANOVA, we need to estimate groups (k)
        # Assuming 3 conditions: baseline, enhanced, reduced
        k = 3 
        n = power_analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, k_groups=k)
        
        result = {
            "effect_size": effect_size,
            "alpha": alpha,
            "target_power": power,
            "groups": k,
            "required_sample_size_per_group": int(np.ceil(n)),
            "total_required_participants": int(np.ceil(n * k)),
            "notes": "Calculated for repeated measures ANOVA with 3 conditions"
        }
        logger.info(f"Power analysis complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

def save_power_analysis(result: Dict[str, Any], filename: str = "power_analysis.json"):
    """Save power analysis results to JSON file."""
    output_path = get_processed_dir() / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Power analysis saved to {output_path}")

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
    output_path = get_processed_dir() / filename
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
    result = calculate_anova_power()
    save_power_analysis(result)
    print(f"Power analysis complete. Required N: {result['total_required_participants']}")

if __name__ == "__main__":
    main()