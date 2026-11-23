"""
Power Analysis for GLMM on AdaPlanBench Extension.

This script calculates the achieved power for the planned GLMM analysis given
the actual sample size of the filtered dataset. It serves as a pre-experiment
check (FR-011) to confirm statistical sufficiency.

Dependencies:
    - statsmodels
    - pandas
"""

import os
import sys
import json
import argparse
from pathlib import Path

import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Paths, PowerInsufficientError

# Constants for the analysis
ALPHA = 0.05
EFFECT_SIZE_F2 = 0.15  # Cohen's f² target (small-to-medium)
GROUPS = 2             # Monolithic vs Dual-Track

class PowerInsufficientError(Exception):
    """Raised when the calculated power is below the required threshold (0.80)."""
    pass

def load_filtered_tasks(input_path: str) -> pd.DataFrame:
    """
    Load the filtered tasks dataset.

    Args:
        input_path: Path to the CSV file containing filtered tasks.

    Returns:
        DataFrame with the filtered tasks.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {input_path}")

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError(f"Filtered tasks file is empty: {input_path}")

    if 'task_id' not in df.columns:
        raise ValueError(f"Filtered tasks file missing required column 'task_id': {input_path}")

    return df

def calculate_achieved_power(n_observations: int, effect_size: float, alpha: float, groups: int) -> float:
    """
    Calculate the achieved power for a GLMM (approximated via F-test for fixed effects).

    This uses the `statsmodels.stats.power.FTestAnovaPower` as a proxy for the
    fixed effect power in a GLMM context, given the constraints of the environment.
    For a more precise GLMM power analysis, simulation-based approaches are preferred,
    but this provides a robust analytical estimate for the fixed effect of 'architecture'.

    Args:
        n_observations: Total number of observations (tasks).
        effect_size: Cohen's f².
        alpha: Significance level.
        groups: Number of groups (levels of the categorical predictor).

    Returns:
        Calculated power (float between 0 and 1).
    """
    try:
        from statsmodels.stats.power import FTestAnovaPower

        # Degrees of freedom for the numerator (effect)
        # For a categorical predictor with k groups, df1 = k - 1
        df_num = groups - 1

        # Degrees of freedom for the denominator (error)
        # Approximation: N - k - (other fixed effects) - 1
        # Assuming a simple model: Architecture + Constraints + Interaction
        # df_denom = N - (number of fixed effect parameters)
        # Let's conservatively estimate fixed effect parameters:
        # Intercept (1) + Architecture (groups-1) + Constraints (1) + Interaction (groups-1)
        # Total params = 1 + 1 + 1 + 1 = 4 (for groups=2)
        # A safer, more conservative approximation for df_denom is N - groups - 1
        df_denom = n_observations - groups - 1

        if df_denom <= 0:
            # Not enough data to estimate error
            return 0.0

        power_analyzer = FTestAnovaPower()
        power = power_analyzer.solve_power(
            effect_size=effect_size,
            nobs1=n_observations, # Total N
            alpha=alpha,
            power=None,
            ratio=1.0, # Ratio of nobs in group 1 to group 2 (assuming balanced for approximation)
            alternative='larger'
        )

        # FTestAnovaPower.solve_power sometimes returns NaN if inputs are out of range
        if power is None or (isinstance(power, float) and (power != power)): # Check for NaN
            return 0.0

        return float(power)

    except ImportError:
        raise RuntimeError("statsmodels is required for power analysis. Install it via pip install statsmodels.")
    except Exception as e:
        # Log the specific error for debugging but return 0.0 to trigger failure
        print(f"Warning: Error during power calculation: {e}", file=sys.stderr)
        return 0.0

def run_power_analysis(input_path: str, output_path: str) -> dict:
    """
    Run the power analysis and write the report.

    Args:
        input_path: Path to the filtered tasks CSV.
        output_path: Path to write the JSON report.

    Returns:
        Dictionary containing the power analysis results.

    Raises:
        PowerInsufficientError: If calculated power < 0.80.
    """
    print(f"Loading filtered tasks from {input_path}...")
    df = load_filtered_tasks(input_path)

    n_observations = len(df)
    print(f"Sample size (n_observations): {n_observations}")

    print(f"Calculating achieved power for GLMM...")
    print(f"  - Groups: {GROUPS}")
    print(f"  - Alpha: {ALPHA}")
    print(f"  - Effect Size (f²): {EFFECT_SIZE_F2}")

    calculated_power = calculate_achieved_power(
        n_observations=n_observations,
        effect_size=EFFECT_SIZE_F2,
        alpha=ALPHA,
        groups=GROUPS
    )

    print(f"Calculated Power: {calculated_power:.4f}")

    sufficient = calculated_power >= 0.80

    report = {
        "calculated_power": calculated_power,
        "effect_size": EFFECT_SIZE_F2,
        "sample_size": n_observations,
        "groups": GROUPS,
        "sufficient": sufficient
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"Writing power report to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    if not sufficient:
        raise PowerInsufficientError(
            f"Power analysis failed: Calculated power ({calculated_power:.4f}) "
            f"is below the required threshold (0.80). "
            f"Sample size ({n_observations}) is insufficient for the target effect size ({EFFECT_SIZE_F2})."
        )

    print("Power analysis passed. Sample size is sufficient.")
    return report

def main():
    parser = argparse.ArgumentParser(description="Perform power analysis on the filtered dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default=str(Paths.DATA_PROCESSED / "filtered_tasks.csv"),
        help="Path to the filtered tasks CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Paths.DATA_PROCESSED / "power_report.json"),
        help="Path to write the power analysis JSON report."
    )

    args = parser.parse_args()

    try:
        run_power_analysis(args.input, args.output)
        print("Power analysis completed successfully.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PowerInsufficientError as e:
        print(f"CRITICAL: {e}", file=sys.stderr)
        # Exit with non-zero to indicate failure in the pipeline
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()