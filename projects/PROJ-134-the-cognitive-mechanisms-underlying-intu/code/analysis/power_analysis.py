"""
Power Analysis for Mixed-Effects Models.

Calculates the Minimum Detectable Effect Size (MDES) for a mixed-effects model
given specific parameters (N participants, vignettes, SD, alpha, power).

This module implements T045: Power Analysis to ensure downstream tasks (T013)
have valid MDES data before simulation begins.
"""
import os
import sys
import math
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from project config to handle paths correctly
try:
    from code.config import get_path
except ImportError:
    # Fallback for direct execution or different import context
    from config import get_path

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def calculate_standard_error(n_participants: int, n_vignettes: int) -> float:
    """
    Calculate the standard error for the effect size estimate in a mixed-effects model.

    Formula approximation for cross-sectional design:
    SE = SD / sqrt(N * n_vignettes) * sqrt(1 + (n_vignettes - 1) * ICC)
    Assuming ICC (Intra-class Correlation) is negligible or 0 for this calculation,
    or simplified to SE = SD / sqrt(N * n_vignettes) for the effective sample size.

    For a more robust approximation without specific ICC, we use the effective sample size:
    N_effective = N_participants * n_vignettes
    SE = SD / sqrt(N_effective)

    Args:
        n_participants: Number of unique participants (N).
        n_vignettes: Number of vignettes per participant.

    Returns:
        float: The calculated standard error.
    """
    effective_n = n_participants * n_vignettes
    if effective_n <= 0:
        raise ValueError("Effective sample size must be positive.")
    
    # Standard Error of the mean difference (simplified for balanced design)
    # SE = sigma / sqrt(N * n_vignettes)
    # We assume sigma (SD) is passed or handled in the MDES function
    return 1.0 / math.sqrt(effective_n)


def calculate_mdes(
    n_participants: int,
    n_vignettes: int,
    sd: float,
    alpha: float,
    power: float
) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES).

    MDES is the smallest effect size that can be detected with a given power
    and significance level.

    Formula: MDES = (Z_alpha/2 + Z_beta) * SE
    Where:
      - Z_alpha/2 is the critical value for the significance level (two-tailed).
      - Z_beta is the critical value for the desired power (1 - beta).
      - SE is the standard error of the effect size estimate.

    Args:
        n_participants: Number of participants (N).
        n_vignettes: Number of vignettes per participant.
        sd: Standard deviation of the outcome variable.
        alpha: Significance level (e.g., 0.05).
        power: Desired statistical power (e.g., 0.80).

    Returns:
        float: The Minimum Detectable Effect Size.
    """
    if sd <= 0:
        raise ValueError("Standard deviation must be positive.")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1.")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1.")

    # Calculate Z-scores
    # For two-tailed test: Z_alpha/2
    # We use the inverse cumulative distribution function for the standard normal.
    # Approximation using math.erfcinv is not directly available in standard math,
    # so we use a standard approximation or scipy if available.
    # To avoid hard dependency on scipy for this specific utility, we use a robust approximation.
    
    def norm_ppf(p: float) -> float:
        """Approximation of the inverse normal CDF (probit function)."""
        if p <= 0 or p >= 1:
            raise ValueError("Probability must be between 0 and 1.")
        # Rational approximation for the inverse normal distribution
        # Based on Peter J. Acklam's algorithm
        a = [-3.969683028665376e+01, 2.209460984245205e+02,
             -2.759285104469687e+02, 1.383577518672690e+02,
             -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02,
             -1.556989798598866e+02, 6.680131188771972e+01,
             -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01,
             -2.400758277161838e+00, -2.549732539343734e+00,
             4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01,
             2.445134137142996e+00, 3.754408661907416e+00]

        p_low = 0.02425
        p_high = 1 - p_low

        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                   ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
                   (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                    ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    z_alpha_2 = norm_ppf(1 - alpha / 2)
    z_beta = norm_ppf(power)

    # Standard Error calculation
    # SE = SD / sqrt(N * n_vignettes)
    se = sd / math.sqrt(n_participants * n_vignettes)

    mdes = (z_alpha_2 + z_beta) * se
    return mdes


def validate_ground_truth_effect(mdes: float, ground_truth_effect: float) -> None:
    """
    Validate that the calculated MDES is strictly less than the ground truth effect.

    This ensures that the study is statistically powered to detect the effect
    we intend to simulate.

    Args:
        mdes: The calculated Minimum Detectable Effect Size.
        ground_truth_effect: The effect size used in the simulation.

    Raises:
        ValueError: If MDES >= ground_truth_effect.
    """
    if mdes >= ground_truth_effect:
        raise ValueError(
            f"Statistical Power Constraint Violated: "
            f"MDES ({mdes:.4f}) is not strictly less than the "
            f"ground_truth_effect ({ground_truth_effect}). "
            f"The study is underpowered to detect the intended effect."
        )


def load_ground_truth_effect() -> float:
    """
    Load the ground truth effect from the configuration or a derived source.
    
    In this pipeline, the ground truth effect is typically defined in config.py
    or derived from the MDES report itself if it was previously calculated.
    For T045, we assume the ground truth effect is defined in `code/config.py`.
    
    Returns:
        float: The ground truth effect value.
    """
    # Attempt to import from config
    try:
        # Try to get from config if it exists there
        from code.config import GROUND_TRUTH_EFFECT
        return GROUND_TRUTH_EFFECT
    except ImportError:
        # Fallback: If not in config, we might need to read from a default or raise
        # For T045, the constraint is that MDES < ground_truth_effect.
        # If the config doesn't define it yet, we might need to assume a standard value
        # or raise an error if the task requires it to be defined elsewhere.
        # Based on T013 description, it reads from config.
        # Let's assume a default if not found, but T013 will fail if not set.
        # However, T045 must run BEFORE T013.
        # The task description says: "The calculated MDES must be strictly less than the 
        # ground_truth_effect used in the simulation".
        # If ground_truth_effect is not yet defined, we cannot validate.
        # We will assume a standard value for the simulation (e.g., 0.5) if not found,
        # but this is a placeholder for the actual value which should be in config.
        # Let's try to read from state/mdes_report.yaml if it exists from a previous run?
        # No, this is the first run.
        # We will assume a default of 0.5 for the simulation as per common practice in T013.
        # But strictly, it should come from config.
        # Let's check if GROUND_TRUTH_EFFECT is defined in config.py.
        # If not, we raise an error.
        raise RuntimeError(
            "GROUND_TRUTH_EFFECT must be defined in code/config.py to validate MDES."
        )


def load_mdes_report() -> Optional[Dict[str, Any]]:
    """
    Load the existing MDES report if it exists.
    
    Returns:
        Optional[Dict]: The report data or None if not found.
    """
    report_path = get_path("state", "mdes_report.yaml")
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            import yaml
            return yaml.safe_load(f)
    return None


def run_power_analysis(
    n_participants: int = 200,
    n_vignettes: int = 50,
    sd: float = 1.0,
    alpha: float = 0.05,
    power: float = 0.80
) -> Dict[str, Any]:
    """
    Run the full power analysis pipeline.
    
    Args:
        n_participants: Number of participants.
        n_vignettes: Number of vignettes per participant.
        sd: Standard deviation.
        alpha: Significance level.
        power: Desired power.
        
    Returns:
        Dict containing the results.
    """
    logger.info(f"Calculating MDES for N={n_participants}, Vignettes={n_vignettes}, "
                f"SD={sd}, Alpha={alpha}, Power={power}")
    
    mdes = calculate_mdes(n_participants, n_vignettes, sd, alpha, power)
    logger.info(f"Calculated MDES: {mdes:.6f}")
    
    # Load ground truth effect for validation
    try:
        gte = load_ground_truth_effect()
        logger.info(f"Ground Truth Effect: {gte}")
        validate_ground_truth_effect(mdes, gte)
        logger.info("Validation passed: MDES < Ground Truth Effect")
    except RuntimeError as e:
        logger.warning(f"Could not validate against ground truth: {e}")
        # If we can't validate, we still return the MDES but flag it.
        validation_status = "skipped"
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise e
    else:
        validation_status = "passed"
    
    return {
        "n_participants": n_participants,
        "n_vignettes": n_vignettes,
        "sd": sd,
        "alpha": alpha,
        "power": power,
        "mdes_value": mdes,
        "validation_status": validation_status
    }


def generate_report(results: Dict[str, Any]) -> None:
    """
    Write the MDES report to state/mdes_report.yaml.
    
    Args:
        results: The dictionary of results from run_power_analysis.
    """
    output_path = get_path("state", "mdes_report.yaml")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        import yaml
        yaml.dump(results, f, default_flow_style=False)
    
    logger.info(f"MDES report written to {output_path}")


def main() -> None:
    """Main entry point for T045."""
    logger.info("Starting Power Analysis (T045)...")
    
    # Parameters as defined in tasks.md and plan.md
    N = 200
    VIGNETTES = 50
    SD = 1.0
    ALPHA = 0.05
    POWER = 0.80
    
    try:
        results = run_power_analysis(
            n_participants=N,
            n_vignettes=VIGNETTES,
            sd=SD,
            alpha=ALPHA,
            power=POWER
        )
        generate_report(results)
        logger.info("Power Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Power Analysis failed: {e}")
        raise e


if __name__ == "__main__":
    main()
