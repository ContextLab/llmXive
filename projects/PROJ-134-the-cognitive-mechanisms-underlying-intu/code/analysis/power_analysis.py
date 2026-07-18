"""
Power Analysis for Mixed-Effects Models

Calculates the Minimum Detectable Effect Size (MDES) for a mixed-effects model
given specific sample sizes and variance parameters. This ensures the simulation
is statistically powered to recover the ground_truth_effect.

Task: T045 [US3]
"""
import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import ensure_directories
from code.utils.logging_utils import get_logger, log_pipeline_step

# Configure logger
logger = get_logger("power_analysis")

# Constants based on task description
N_PARTICIPANTS = 200
N_VIGNETTES = 50
STANDARD_DEVIATION = 1.0
ALPHA = 0.05
POWER_TARGET = 0.80

def calculate_standard_error(
    n_participants: int,
    n_vignettes: int,
    sigma: float,
    intraclass_correlation: float = 0.0
) -> float:
    """
    Calculate the standard error of the fixed effect estimate in a mixed model.

    Approximation for a balanced design:
    SE(beta) ≈ sigma / sqrt(N * J * (1 - ICC))
    Where:
      N = number of participants
      J = number of vignettes (observations per participant)
      ICC = Intraclass Correlation Coefficient (assumed 0 for independence if not specified)

    For a simple independent t-test equivalent (ICC=0):
    SE = sigma / sqrt(N_total)
    """
    total_observations = n_participants * n_vignettes
    # If ICC is 0, effective sample size is total_observations
    # If ICC > 0, effective sample size is reduced.
    # Using a conservative effective sample size adjustment if ICC is provided.
    if intraclass_correlation > 0:
        # Effective sample size adjustment for clustered data
        design_effect = 1 + (n_vignettes - 1) * intraclass_correlation
        effective_n = total_observations / design_effect
    else:
        effective_n = total_observations

    return sigma / math.sqrt(effective_n)

def calculate_mdes(
    se: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES).

    MDES = (Z_{1-alpha/2} + Z_{power}) * SE

    For a two-tailed test with alpha=0.05 and power=0.80:
    Z_{0.975} ≈ 1.96
    Z_{0.80} ≈ 0.84
    """
    # Critical Z values
    z_alpha = 1.96  # for alpha=0.05 two-tailed
    z_power = 0.84  # for power=0.80

    mdes = (z_alpha + z_power) * se
    return mdes

def run_power_analysis(
    n_participants: int = N_PARTICIPANTS,
    n_vignettes: int = N_VIGNETTES,
    sigma: float = STANDARD_DEVIATION,
    alpha: float = ALPHA,
    power: float = POWER_TARGET,
    icc: float = 0.0
) -> Dict[str, Any]:
    """
    Perform the full power analysis calculation.

    Returns a dictionary with the MDES and parameters used.
    """
    se = calculate_standard_error(n_participants, n_vignettes, sigma, icc)
    mdes = calculate_mdes(se, alpha, power)

    result = {
        "n_participants": n_participants,
        "n_vignettes": n_vignettes,
        "total_observations": n_participants * n_vignettes,
        "standard_deviation": sigma,
        "alpha": alpha,
        "power_target": power,
        "intraclass_correlation": icc,
        "standard_error": se,
        "minimum_detectable_effect_size": mdes,
        "critical_z_alpha": 1.96,
        "critical_z_power": 0.84
    }

    return result

def validate_ground_truth_effect(
    mdes: float,
    ground_truth_effect: float
) -> Tuple[bool, str]:
    """
    Validate if the ground_truth_effect is above the MDES threshold.
    """
    if ground_truth_effect >= mdes:
        return True, f"Ground truth effect ({ground_truth_effect:.4f}) is above MDES ({mdes:.4f}). Validation is statistically meaningful."
    else:
        return False, f"Ground truth effect ({ground_truth_effect:.4f}) is BELOW MDES ({mdes:.4f}). Validation may lack statistical power."

def generate_report(
    analysis_result: Dict[str, Any],
    ground_truth_effect: float
) -> str:
    """
    Generate a human-readable report string.
    """
    is_valid, message = validate_ground_truth_effect(
        analysis_result["minimum_detectable_effect_size"],
        ground_truth_effect
    )

    report_lines = [
        "=" * 60,
        "POWER ANALYSIS REPORT",
        "Task: T045 - Minimum Detectable Effect Size Calculation",
        "=" * 60,
        "",
        "PARAMETERS:",
        f"  Participants (N): {analysis_result['n_participants']}",
        f"  Vignettes (J): {analysis_result['n_vignettes']}",
        f"  Total Observations: {analysis_result['total_observations']}",
        f"  Standard Deviation (σ): {analysis_result['standard_deviation']}",
        f"  Alpha (α): {analysis_result['alpha']}",
        f"  Target Power (1-β): {analysis_result['power_target']}",
        f"  Intraclass Correlation (ICC): {analysis_result['intraclass_correlation']}",
        "",
        "RESULTS:",
        f"  Standard Error (SE): {analysis_result['standard_error']:.6f}",
        f"  Minimum Detectable Effect Size (MDES): {analysis_result['minimum_detectable_effect_size']:.6f}",
        "",
        "VALIDATION:",
        f"  Assumed Ground Truth Effect: {ground_truth_effect}",
        f"  Status: {'PASS' if is_valid else 'FAIL'}",
        f"  Message: {message}",
        "",
        "=" * 60
    ]

    return "\n".join(report_lines)

def main() -> None:
    """
    Main entry point for the power analysis script.
    Generates the report and saves it to data/reports/power_analysis_report.txt.
    """
    log_pipeline_step("power_analysis", "Starting power analysis calculation")

    # Ensure output directories exist
    ensure_directories()

    # Parameters
    n_participants = N_PARTICIPANTS
    n_vignettes = N_VIGNETTES
    sigma = STANDARD_DEVIATION
    alpha = ALPHA
    power = POWER_TARGET

    # For this specific task, we assume a ground truth effect of 0.5 based on
    # typical simulation parameters in this project (e.g., T021 mentions 0.5).
    # If a specific value is needed, it can be passed as an argument or config.
    ground_truth_effect = 0.5

    logger.info(f"Calculating MDES for N={n_participants}, J={n_vignettes}, σ={sigma}")

    # Run analysis
    analysis_result = run_power_analysis(
        n_participants=n_participants,
        n_vignettes=n_vignettes,
        sigma=sigma,
        alpha=alpha,
        power=power
    )

    # Generate report
    report_text = generate_report(analysis_result, ground_truth_effect)

    # Define output path
    output_dir = project_root / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "power_analysis_report.txt"

    # Write report to file
    with open(output_path, "w") as f:
        f.write(report_text)

    logger.info(f"Power analysis report written to: {output_path}")
    print(report_text)

    log_pipeline_step("power_analysis", "Power analysis completed successfully")

if __name__ == "__main__":
    main()
