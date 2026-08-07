"""
T025: Generate correlations.csv and non_linear_comparison.json.

This script aggregates the results from the Bonferroni-corrected correlation analysis
(T021) and the non-linear model comparison (T024) into the final output files required
for the project.

Dependencies:
- code/09_apply_bonferroni.py (produces data/processed/correlations_corrected.csv)
- code/12_nonlinear_analysis.py (produces data/processed/nonlinear_results.json)

Outputs:
- data/processed/correlations.csv (Final aggregated correlation table)
- data/processed/non_linear_comparison.json (Final model comparison results)
"""
import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_path


def load_bonferroni_results():
    """Load the Bonferroni-corrected correlation results."""
    input_path = get_path("correlations_corrected_csv")
    if not os.path.exists(input_path):
        # Fallback to common naming if config path is not set exactly
        fallback_path = Path(project_root) / "data" / "processed" / "correlations_corrected.csv"
        if fallback_path.exists():
            input_path = str(fallback_path)
        else:
            raise FileNotFoundError(
                f"Bonferroni results not found at {input_path} or {fallback_path}. "
                "Ensure T021 (code/09_apply_bonferroni.py) has completed successfully."
            )
    
    return pd.read_csv(input_path)


def load_nonlinear_results():
    """Load the non-linear analysis results."""
    input_path = get_path("nonlinear_results_json")
    if not os.path.exists(input_path):
        # Fallback to common naming
        fallback_path = Path(project_root) / "data" / "processed" / "nonlinear_results.json"
        if fallback_path.exists():
            input_path = str(fallback_path)
        else:
            raise FileNotFoundError(
                f"Non-linear results not found at {input_path} or {fallback_path}. "
                "Ensure T024 (code/12_nonlinear_analysis.py) has completed successfully."
            )
    
    with open(input_path, 'r') as f:
        return json.load(f)


def save_correlations(df, output_path):
    """Save the final correlations dataframe."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved correlations to {output_path}")


def save_nonlinear_comparison(results, output_path):
    """Save the final non-linear comparison JSON."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved non-linear comparison to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate final correlation and non-linear comparison outputs (T025).")
    parser.add_argument("--output-dir", type=str, default=None, help="Override default output directory.")
    args = parser.parse_args()

    base_dir = Path(project_root) / "data" / "processed"
    if args.output_dir:
        base_dir = Path(args.output_dir)

    corr_output = base_dir / "correlations.csv"
    nl_output = base_dir / "non_linear_comparison.json"

    print("Loading Bonferroni-corrected correlations...")
    try:
        corr_df = load_bonferroni_results()
        # Validate expected columns exist
        required_cols = ['band', 'correlation', 'p_value', 'bonferroni_p', 'significant']
        missing = [c for c in required_cols if c not in corr_df.columns]
        if missing:
            raise ValueError(f"Correlation file missing required columns: {missing}")
    except Exception as e:
        print(f"Error loading correlations: {e}")
        sys.exit(1)

    print("Loading non-linear analysis results...")
    try:
        nl_results = load_nonlinear_results()
        # Basic validation of structure
        if not isinstance(nl_results, dict):
            raise ValueError("Non-linear results must be a dictionary.")
    except Exception as e:
        print(f"Error loading non-linear results: {e}")
        sys.exit(1)

    print("Saving final outputs...")
    save_correlations(corr_df, str(corr_output))
    save_nonlinear_comparison(nl_results, str(nl_output))

    print("T025 completed successfully.")


if __name__ == "__main__":
    main()