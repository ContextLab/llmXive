import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from statsmodels.stats.power import GofChisquarePower, TTestIndPower
import numpy as np

# Ensure we can import from the project root if run as a script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import RANDOM_SEED

logger = get_logger(__name__)

# Constants defined in tasks.md for the experiment
SAMPLE_SIZE_N = 500
ALPHA = 0.05
TARGET_POWER = 0.80

# Expected effect sizes (Cohen's w for chi-square, d for t-test)
# Based on typical expectations in rule-engine vs baseline comparisons:
# Small: 0.1, Medium: 0.3, Large: 0.5
EFFECT_SIZES = {
    "small": 0.1,
    "medium": 0.3,
    "large": 0.5
}

def load_results_csv(results_path: str) -> list:
    """Load the merged results CSV to verify sample size and data integrity."""
    import csv
    rows = []
    with open(results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def calculate_power_chi_square(effect_size: float, n_obs: int, df: int = 1) -> float:
    """
    Calculate statistical power for a chi-square test of independence.
    Used for the interaction term in the regression (categorical vs categorical).
    """
    power_analysis = GofChisquarePower()
    try:
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=n_obs,
            alpha=ALPHA,
            power=None,
            df=df
        )
        return power if power is not None else 0.0
    except Exception as e:
        logger.warning(f"Power calculation failed for effect_size={effect_size}: {e}")
        return 0.0

def calculate_power_t_test(effect_size: float, n1: int, n2: int) -> float:
    """
    Calculate statistical power for an independent samples t-test.
    Used for time-to-pivot differences between groups.
    """
    power_analysis = TTestIndPower()
    try:
        power = power_analysis.solve_power(
            effect_size=effect_size,
            nobs1=n1,
            alpha=ALPHA,
            power=None,
            ratio=1.0  # Assuming equal group sizes for simplicity
        )
        return power if power is not None else 0.0
    except Exception as e:
        logger.warning(f"Power calculation failed for t-test effect_size={effect_size}: {e}")
        return 0.0

def run_power_analysis(results_path: str, output_path: str) -> Dict[str, Any]:
    """
    Perform statistical power analysis for the experiment.
    """
    log_stage_start(logger, "Power Analysis")

    # Verify input file exists
    if not os.path.exists(results_path):
        logger.error(f"Results file not found: {results_path}")
        raise FileNotFoundError(f"Results file not found: {results_path}")

    # Load data to confirm sample size
    results_data = load_results_csv(results_path)
    actual_n = len(results_data)
    logger.info(f"Loaded {actual_n} records from results file.")

    if actual_n == 0:
        logger.error("No data found in results file. Cannot perform power analysis.")
        raise ValueError("No data found in results file.")

    # We assume the regression model (mixed-effects) has similar power properties
    # to a chi-square test of independence for the interaction term (Method x FailureType).
    # Degrees of freedom for interaction: (rows-1)*(cols-1)
    # FailureType has 5 categories, Method has 2 -> df = 4 * 1 = 4
    df_interaction = 4

    power_results = {
        "sample_size_used": actual_n,
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "analysis_type": "Mixed-Effects Logistic Regression (Interaction Term)",
        "degrees_of_freedom": df_interaction,
        "power_by_effect_size": {},
        "low_power_warning": False,
        "recommendation": ""
    }

    logger.info("Calculating power for various effect sizes...")

    for label, es in EFFECT_SIZES.items():
        power = calculate_power_chi_square(es, actual_n, df=df_interaction)
        power_results["power_by_effect_size"][label] = {
            "effect_size": es,
            "calculated_power": round(power, 4),
            "sufficient": power >= TARGET_POWER
        }
        logger.info(f"  Effect Size ({label}): {es:.2f} -> Power: {power:.4f}")

    # Determine if we have low power for the most likely scenario (medium effect)
    medium_power = power_results["power_by_effect_size"]["medium"]["calculated_power"]
    if medium_power < TARGET_POWER:
        power_results["low_power_warning"] = True
        power_results["recommendation"] = (
            f"WARNING: Statistical power for a medium effect size ({medium_power:.2f}) "
            f"is below the target of {TARGET_POWER}. "
            f"Consider increasing the sample size from {actual_n} to at least "
            f"{int(actual_n * (TARGET_POWER / medium_power))} to achieve sufficient power."
        )
    else:
        power_results["recommendation"] = (
            f"Statistical power for a medium effect size ({medium_power:.2f}) "
            f"exceeds the target of {TARGET_POWER}. The sample size of {actual_n} is sufficient."
        )

    # Save results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(power_results, f, indent=2)

    logger.info(f"Power analysis report saved to {output_path}")
    log_stage_end(logger, "Power Analysis")

    return power_results

def main():
    """Main entry point for the power analysis script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    results_path = project_root / "data" / "derived" / "results.csv"
    output_path = project_root / "data" / "derived" / "power_analysis_report.json"

    try:
        run_power_analysis(str(results_path), str(output_path))
        print(f"Success: Power analysis complete. Report saved to {output_path}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
