import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import glm

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_analysis_config(config_path: Path) -> Dict[str, Any]:
    """Load and validate the analysis configuration file."""
    if not config_path.exists():
        print(f"ERROR: Analysis config file not found at {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_keys = [
            "min_samples_per_bin",
            "splines_df_candidates",
            "p_value_threshold",
        ]
        for key in required_keys:
            if key not in config:
                print(f"ERROR: Missing required key '{key}' in analysis config.")
                sys.exit(1)

        return config
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in analysis config: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load analysis config: {e}")
        sys.exit(1)


def load_simulation_data(csv_path: Path) -> pd.DataFrame:
    """
    Load simulation logs from CSV.
    Exits with Data Flow Violation if file is missing or empty.
    """
    if not csv_path.exists():
        print("Data Flow Violation: Simulation logs not complete")
        sys.exit(1)

    if csv_path.stat().st_size == 0:
        print("Data Flow Violation: Simulation logs file is empty")
        sys.exit(1)

    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            print("Data Flow Violation: Simulation logs file contains no data rows")
            sys.exit(1)

        # Verify required columns exist
        required_cols = ["density_value", "requested_horizon", "success"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Data Flow Violation: Missing required columns: {missing_cols}")
            sys.exit(1)

        return df
    except Exception as e:
        print(f"ERROR: Failed to load simulation data: {e}")
        sys.exit(1)


def validate_sample_size(df: pd.DataFrame, min_samples: int) -> None:
    """
    Validate that every (density, horizon) bin has at least min_samples.
    Exits with error if not.
    """
    grouped = df.groupby(["density_value", "requested_horizon"])
    bin_counts = grouped.size()
    invalid_bins = bin_counts[bin_counts < min_samples]

    if not invalid_bins.empty:
        print("ERROR: Insufficient sample size in the following bins:")
        for (density, horizon), count in invalid_bins.items():
            print(
                f"  Bin (density={density}, horizon={horizon}): {count} samples (min required: {min_samples})"
            )
        sys.exit(1)


def build_formula_with_splines(df: pd.DataFrame, candidates: List[int]) -> Tuple[str, int, Any]:
    """
    Select the optimal degrees of freedom (df) for B‑splines on 'requested_horizon'
    by minimizing AIC among candidates.
    Returns (formula_string, selected_df, fitted_model).
    """
    best_df = None
    best_aic = float("inf")
    best_model = None

    for df_val in candidates:
        try:
            # Use B‑splines (bs) as a stand‑in for natural splines.
            formula = f"success ~ density_value * bs(requested_horizon, df={df_val}, degree=3)"
            model = glm(formula, data=df, family=sm.families.Binomial()).fit()
            if model.aic < best_aic:
                best_aic = model.aic
                best_df = df_val
                best_model = model
        except Exception as e:
            print(f"Warning: Failed to fit model with df={df_val}: {e}")
            continue

    if best_model is None:
        print("ERROR: No spline model converged.")
        sys.exit(1)

    formula = f"success ~ density_value * bs(requested_horizon, df={best_df}, degree=3)"
    print(f"Selected optimal spline df={best_df} with AIC={best_aic:.4f}")
    return formula, best_df, best_model


def run_logistic_regression(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fit the GLM and return a dictionary that conforms to the regression_output schema.
    """
    formula, selected_df, model = build_formula_with_splines(
        df, config["splines_df_candidates"]
    )

    # Model summary components
    model_summary = {
        "formula": formula,
        "n_observations": int(model.nobs),
        "pseudo_r_squared": float(model.prsquared),
    }

    # Coefficients list
    coefficients = []
    for term in model.params.index:
        coefficients.append(
            {
                "term": term,
                "estimate": float(model.params[term]),
                "std_error": float(model.bse[term]),
                "z_value": float(model.tvalues[term]),
                "p_value": float(model.pvalues[term]),
            }
        )

    # Interaction term significance (first interaction term)
    interaction_terms = [
        term
        for term in model.pvalues.index
        if "density_value" in term and "bs" in term
    ]
    if interaction_terms:
        interaction_p = float(model.pvalues[interaction_terms[0]])
    else:
        interaction_p = None

    interaction_significance = {
        "p_value": interaction_p,
        "supported_hypothesis": (
            interaction_p is not None and interaction_p < config["p_value_threshold"]
        ),
    }

    # Assemble final results
    results = {
        "model_summary": model_summary,
        "coefficients": coefficients,
        "interaction_significance": interaction_significance,
        # Plot path will be filled later by the visualization step; placeholder for now
        "plot_path": "",
    }

    return results


def write_summary(results: Dict[str, Any], output_path: Path) -> None:
    """Write regression summary JSON conforming to the schema."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Regression summary written to {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to write regression summary: {e}")
        sys.exit(1)


def write_hypothesis_summary(results: Dict[str, Any], output_path: Path) -> None:
    """Write a human‑readable markdown summary of the hypothesis test."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Hypothesis Summary\\n\\n")
            f.write("## Regression Model\\n\\n")
            f.write(f"- **Formula**: {results['model_summary']['formula']}\\n")
            f.write(
                f"- **Observations**: {results['model_summary']['n_observations']}\\n"
            )
            f.write(
                f"- **McFadden's pseudo‑R²**: {results['model_summary']['pseudo_r_squared']:.4f}\\n\\n"
            )

            f.write("## Interaction Term Significance\\n\\n")
            p_val = results["interaction_significance"]["p_value"]
            supported = results["interaction_significance"]["supported_hypothesis"]
            if p_val is not None:
                f.write(f"- **Interaction p‑value**: {p_val:.6f}\\n")
                f.write(
                    f"- **Hypothesis supported (p < {0.05})**: {supported}\\n\\n"
                )
            else:
                f.write("- **Interaction p‑value**: Not available\\n")
                f.write("- **Hypothesis supported**: False\\n\\n")

            if supported:
                f.write("### Conclusion\\n\\n")
                f.write(
                    "The interaction between density and horizon is statistically significant (p < 0.05).\\n"
                )
                f.write(
                    "This supports the hypothesis that masking stale observations helps search agents until it doesn't.\\n"
                )
            else:
                f.write("### Conclusion\\n\\n")
                f.write(
                    "The interaction between density and horizon is not statistically significant (p ≥ 0.05).\\n"
                )
                f.write(
                    "This does not support the hypothesis that masking stale observations helps search agents until it doesn't.\\n"
                )
        print(f"Hypothesis summary written to {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to write hypothesis summary: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze simulation results using logistic regression with splines."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/logs/simulation_results.csv",
        help="Path to the CSV file containing simulation results.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory where regression_summary.json and hypothesis_summary.md will be written.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (if needed).",
    )
    args = parser.parse_args()

    if args.seed is not None:
        import random
        import numpy as np

        random.seed(args.seed)
        np.random.seed(args.seed)

    # Resolve paths
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    analysis_config_path = Path(__file__).parent / "config" / "analysis_config.json"
    config = load_analysis_config(analysis_config_path)

    # Load data
    df = load_simulation_data(input_path)

    # Validate sample size per bin
    validate_sample_size(df, config["min_samples_per_bin"])

    # Run regression
    results = run_logistic_regression(df, config)

    # Write outputs
    regression_json_path = output_dir / "regression_summary.json"
    hypothesis_md_path = output_dir / "hypothesis_summary.md"

    write_summary(results, regression_json_path)
    write_hypothesis_summary(results, hypothesis_md_path)

    print("Analysis complete.")


if __name__ == "__main__":
    main()
