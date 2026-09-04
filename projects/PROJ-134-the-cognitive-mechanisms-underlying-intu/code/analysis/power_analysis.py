"""
Power analysis module for T045.
Calculates MDES and writes the report to state/mdes_report.yaml.
"""
import os
import sys
import math
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from code.config import get_path, ensure_directories
from code.utils.logging import get_logger, log_operation

logger = get_logger("power_analysis")

def calculate_standard_error(n: int, sd: float) -> float:
    """
    Calculate the standard error of the mean.
    SE = SD / sqrt(N)
    """
    if n <= 0:
        raise ValueError("N must be positive")
    return sd / math.sqrt(n)

def calculate_mdes(n: int, sd: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES).
    Approximation for two-sample t-test (equal variance):
    MDES = (Z_alpha/2 + Z_beta) * SE * sqrt(2)
    
    Where:
    - Z_alpha/2 is the critical value for significance level alpha (two-tailed)
    - Z_beta is the critical value for power (1 - beta)
    - SE is the standard error
    """
    if n <= 0 or sd <= 0:
        raise ValueError("N and SD must be positive")
    
    # Approximate Z values (using simple lookup for common values)
    # Z for alpha=0.05 (two-tailed) -> 1.96
    # Z for power=0.80 -> 0.84
    z_alpha = 1.96
    z_beta = 0.84
    
    se = calculate_standard_error(n, sd)
    mdes = (z_alpha + z_beta) * se * math.sqrt(2)
    
    return mdes

def validate_ground_truth_effect(effect: float, mdes: float) -> bool:
    """
    Validate that the ground truth effect is greater than the MDES.
    """
    return effect > mdes

def load_ground_truth_effect() -> float:
    """
    Load the ground truth effect from research.md or a config file.
    For now, we use a default value based on typical effect sizes in moral psychology.
    TODO: Read from research.md or config if available.
    """
    # Default effect size (Cohen's d) often cited in similar studies is ~0.5
    return 0.5

def load_mdes_report() -> Dict[str, Any]:
    """
    Load the MDES report from state/mdes_report.yaml.
    """
    report_path = get_path("state", "mdes_report.yaml")
    if not os.path.exists(report_path):
        raise FileNotFoundError(
            f"MDES report not found at {report_path}. "
            "Ensure T045 (power_analysis) has completed successfully."
        )
    
    import yaml
    with open(report_path, 'r') as f:
        return yaml.safe_load(f)

def run_power_analysis(n: int, sd: float) -> Dict[str, Any]:
    """
    Run the power analysis calculation.
    """
    log_operation("POWER_ANALYSIS_START", n=n, sd=sd)
    
    mdes = calculate_mdes(n, sd)
    ground_truth = load_ground_truth_effect()
    is_valid = validate_ground_truth_effect(ground_truth, mdes)
    
    result = {
        "n_participants": n,
        "standard_deviation": sd,
        "mdes_value": mdes,
        "ground_truth_effect": ground_truth,
        "is_valid": is_valid,
        "status": "success"
    }
    
    log_operation("POWER_ANALYSIS_END", result=json.dumps(result))
    return result

def generate_report(result: Dict[str, Any]) -> None:
    """
    Write the MDES report to state/mdes_report.yaml.
    """
    output_path = get_path("state", "mdes_report.yaml")
    import yaml
    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False)
    logger.info(f"MDES report written to {output_path}")

def main():
    """
    Entry point for T045.
    Reads N from code/config.py (static value for simulation mode).
    """
    ensure_directories()
    
    # Read N from config if available, otherwise use default
    # In simulation mode, N is defined in config.py
    try:
        from code.config import CONFIG
        n = CONFIG.get('N_SIMULATION', 200)
    except ImportError:
        n = 200
    
    # Default SD based on Gervais norms (approx 1.0 for normalized scores)
    sd = 1.0
    
    result = run_power_analysis(n, sd)
    generate_report(result)
    
    if not result['is_valid']:
        logger.warning(f"Ground truth effect ({result['ground_truth_effect']}) is smaller than MDES ({result['mdes_value']}).")
    
    logger.info("T045 Power Analysis completed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
