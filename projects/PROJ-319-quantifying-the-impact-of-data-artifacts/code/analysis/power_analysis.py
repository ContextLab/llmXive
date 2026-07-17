import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy import stats
from code.config import get_project_root

logger = logging.getLogger(__name__)

def load_observed_effect_size() -> Optional[float]:
    """
    Load observed effect size from validation report or calculate from data.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    report_path = processed_dir / "validation_report.json"
    if report_path.exists():
        with open(report_path, "r") as f:
            report = json.load(f)
            # We can estimate effect size from mean/std if available
            # Cohen's d = mean / std
            mean_r = report.get("mean_residual", 0)
            std_r = report.get("std_residual", 1)
            if std_r > 0:
                return abs(mean_r / std_r)
    return None

def calculate_power(effect_size: float, n: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a given effect size and sample size.
    Uses a two-sample t-test approximation.
    """
    # Using non-central t-distribution approximation
    # Power = 1 - beta
    # For simplicity, we use a standard formula
    # z_beta = z_alpha - effect_size * sqrt(n/2)
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = z_alpha - effect_size * np.sqrt(n/2)
    power = 1 - stats.norm.cdf(z_beta)
    return power

def calculate_mdes(power: float = 0.8, n: int = 50, alpha: float = 0.05) -> float:
    """
    Calculate Minimum Detectable Effect Size (MDES) given power and sample size.
    """
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_power = stats.norm.ppf(power)
    # MDES = (z_alpha + z_power) / sqrt(n/2)
    mdes = (z_alpha + z_power) / np.sqrt(n/2)
    return mdes

def generate_power_report():
    """
    Generate a power analysis report including MDES.
    Produces data/validation/power_analysis_report.md.
    """
    root = get_project_root()
    validation_dir = root / "data" / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    n = 50 # Fixed sample size
    alpha = 0.05
    target_power = 0.8
    
    observed_effect = load_observed_effect_size()
    if observed_effect is None:
        observed_effect = 0.5 # Default assumption if not found
    
    power = calculate_power(observed_effect, n, alpha)
    mdes = calculate_mdes(target_power, n, alpha)
    
    conclusion = "Study is adequately powered" if power >= target_power else "Study may be underpowered"
    
    report_content = f"""
    # Power Analysis Report

    ## Parameters
    - Sample Size (n): {n}
    - Alpha (α): {alpha}
    - Target Power: {target_power}

    ## Results
    - Observed Effect Size (Cohen's d): {observed_effect:.4f}
    - Calculated Power: {power:.4f}
    - Minimum Detectable Effect Size (MDES): {mdes:.4f}

    ## Conclusion
    {conclusion}.
    - If power < 0.80, the study may not detect subtle biases (< {mdes:.4f}).
    - Limitations: n=50 constrains the ability to detect small effect sizes.

    ## Cross-Validation Results
    - (To be filled by T045 cross-validation logic)
    """
    
    report_path = validation_dir / "power_analysis_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)
    
    logger.info(f"Power analysis report saved to {report_path}")
    return report_content

def main():
    generate_power_report()
