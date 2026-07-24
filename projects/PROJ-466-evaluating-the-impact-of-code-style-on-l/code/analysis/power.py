"""
Power Analysis Calculation Module.

Calculates the required sample size for Kruskal-Wallis tests using statsmodels.
Implements robust error handling for missing effect size data, defaulting to
the documented N=164 assumption with explicit logging.
"""

import logging
import os
from pathlib import Path
from datetime import datetime

# Try to import statsmodels, handle gracefully if missing
try:
    from statsmodels.stats.power import KruskalPowerAnalysis
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning("statsmodels not installed. Power analysis will use fallback assumptions.")

# Constants
DEFAULT_EFFECT_SIZE = 0.25  # Medium effect size (Cohen's f)
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.8
DEFAULT_N_SAMPLES = 164  # Documented dataset size
LOG_FILE = Path("data/logs/power_analysis.log")

def log_power_analysis(message: str, level: int = logging.INFO):
    """Log message to both console and file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.log(level, message)
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

def calculate_required_sample_size(effect_size: float = DEFAULT_EFFECT_SIZE,
                                   alpha: float = DEFAULT_ALPHA,
                                   power: float = DEFAULT_POWER,
                                   k_groups: int = 3) -> dict:
    """
    Calculate required sample size for Kruskal-Wallis test.

    Args:
        effect_size: Expected effect size (Cohen's f). Defaults to 0.25 (medium).
        alpha: Significance level. Defaults to 0.05.
        power: Desired statistical power. Defaults to 0.8.
        k_groups: Number of groups being compared. Defaults to 3 (neutral, pep8, minified).

    Returns:
        Dictionary with calculation results.
    """
    result = {
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power,
        "k_groups": k_groups,
        "status": "success",
        "required_n_per_group": None,
        "total_required_n": None,
        "actual_n": DEFAULT_N_SAMPLES,
        "note": ""
    }

    if not HAS_STATSMODELS:
        result["status"] = "fallback"
        result["note"] = (
            "statsmodels not available. Using documented N=164 assumption. "
            f"Assumed effect_size={effect_size}, alpha={alpha}, power={power}."
        )
        log_power_analysis(
            f"WARNING: statsmodels not installed. Using fallback assumption: "
            f"N={DEFAULT_N_SAMPLES}, effect_size={effect_size}. "
            "No actual power calculation performed."
        )
        result["required_n_per_group"] = DEFAULT_N_SAMPLES // k_groups
        result["total_required_n"] = DEFAULT_N_SAMPLES
        return result

    try:
        analysis = KruskalPowerAnalysis()
        # Calculate sample size per group
        n_per_group = analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ngroups=k_groups
        )

        if n_per_group is None or n_per_group <= 0:
            raise ValueError("Invalid sample size calculation result")

        result["required_n_per_group"] = int(n_per_group)
        result["total_required_n"] = int(n_per_group * k_groups)
        result["note"] = (
            f"Calculated required sample size: {int(n_per_group)} per group "
            f"({int(n_per_group * k_groups)} total) for effect_size={effect_size}, "
            f"alpha={alpha}, power={power}."
        )

        # Check if actual N meets requirement
        if DEFAULT_N_SAMPLES >= result["total_required_n"]:
            result["sufficiency"] = "sufficient"
            result["note"] += f" Actual N={DEFAULT_N_SAMPLES} is sufficient."
        else:
            result["sufficiency"] = "insufficient"
            result["note"] += f" WARNING: Actual N={DEFAULT_N_SAMPLES} is insufficient."

        log_power_analysis(f"Power analysis successful: {result['note']}")
        return result

    except Exception as e:
        # Handle any calculation errors (missing effect size, invalid params, etc.)
        result["status"] = "error"
        result["note"] = (
            f"Power calculation failed: {str(e)}. "
            f"Defaulting to documented N={DEFAULT_N_SAMPLES} assumption. "
            f"Effect size: {effect_size}, Alpha: {alpha}, Power: {power}."
        )
        log_power_analysis(
            f"ERROR: Power calculation failed ({str(e)}). "
            f"Using fallback: N={DEFAULT_N_SAMPLES}, effect_size={effect_size}. "
            "No actual power calculation performed."
        )
        result["required_n_per_group"] = DEFAULT_N_SAMPLES // k_groups
        result["total_required_n"] = DEFAULT_N_SAMPLES
        return result

def run_power_analysis_pipeline():
    """
    Execute the full power analysis pipeline.

    Calculates required sample size, logs results, and writes to log file.
    """
    log_power_analysis("=" * 60)
    log_power_analysis("POWER ANALYSIS PIPELINE STARTED")
    log_power_analysis("=" * 60)

    # Run calculation with default parameters
    result = calculate_required_sample_size(
        effect_size=DEFAULT_EFFECT_SIZE,
        alpha=DEFAULT_ALPHA,
        power=DEFAULT_POWER,
        k_groups=3  # neutral, pep8, minified
    )

    # Log detailed results
    log_power_analysis(f"Status: {result['status']}")
    log_power_analysis(f"Effect Size: {result['effect_size']}")
    log_power_analysis(f"Alpha: {result['alpha']}")
    log_power_analysis(f"Power: {result['power']}")
    log_power_analysis(f"Groups: {result['k_groups']}")
    log_power_analysis(f"Required N per Group: {result['required_n_per_group']}")
    log_power_analysis(f"Total Required N: {result['total_required_n']}")
    log_power_analysis(f"Actual N: {result['actual_n']}")
    log_power_analysis(f"Note: {result['note']}")

    if result.get("sufficiency"):
        log_power_analysis(f"Sufficiency: {result['sufficiency']}")

    log_power_analysis("=" * 60)
    log_power_analysis("POWER ANALYSIS PIPELINE COMPLETED")
    log_power_analysis("=" * 60)

    return result

if __name__ == "__main__":
    # Ensure log directory exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, mode='a')
        ]
    )

    run_power_analysis_pipeline()