"""
Analysis module for llmXive follow-up study.
Performs logistic regression with natural splines to quantify the interaction
between semantic density and retention horizon on agent success.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

# Third-party dependencies required for analysis
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix

# Constants
DEFAULT_DATA_PATH = "data/processed/simulation_results.jsonl"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_DF = 3  # Degrees of freedom for natural splines


def load_simulation_data(file_path: str) -> pd.DataFrame:
    """
    Load simulation results from a JSONL file.

    Args:
        file_path: Path to the JSONL file containing simulation logs.

    Returns:
        pandas DataFrame with columns: 'horizon', 'density', 'success'.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation data file not found: {file_path}")

    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Expecting specific keys based on simulate_agent.py output
                records.append({
                    'horizon': data.get('horizon'),
                    'density': data.get('density'),
                    'success': data.get('success', 0)
                })
            except json.JSONDecodeError:
                continue

    if not records:
        raise ValueError("No valid records found in simulation data file.")

    df = pd.DataFrame(records)
    return df


def validate_sample_size(df: pd.DataFrame, min_samples: int = 50) -> bool:
    """
    Validate that the dataset has sufficient sample size for statistical power.

    Args:
        df: DataFrame containing the data.
        min_samples: Minimum number of samples required.

    Returns:
        True if sample size is sufficient, False otherwise.
    """
    total_samples = len(df)
    if total_samples < min_samples:
        raise ValueError(
            f"Insufficient sample size: {total_samples} < {min_samples}. "
            "Cannot perform reliable logistic regression."
        )
    return True


def build_formula_with_splines(df: pd.DataFrame, df_horizon: int = DEFAULT_DF) -> str:
    """
    Construct the Patsy formula for logistic regression with natural splines.

    The formula models:
        logit(P(success)) = f(horizon) + density + f(horizon)*density

    where f(horizon) is a natural spline with specified degrees of freedom.

    Args:
        df: DataFrame (used to infer column names).
        df_horizon: Degrees of freedom for the natural spline on 'horizon'.

    Returns:
        String formula ready for statsmodels.
    """
    # Natural spline term for horizon
    ns_horizon = f"ns(horizon, df={df_horizon})"

    # Main effects and interaction
    # Note: We treat density as linear for simplicity, but it could also be splined.
    # The interaction term allows the effect of density to vary non-linearly with horizon.
    formula = f"success ~ {ns_horizon} + density + {ns_horizon}:density"

    return formula


def run_logistic_regression(df: pd.DataFrame, formula: str) -> smGLMResultsWrapper:
    """
    Fit a logistic regression model using statsmodels.

    Args:
        df: DataFrame with the data.
        formula: Patsy formula string.

    Returns:
        Fitted GLM results object.
    """
    y = df['success']
    X = dmatrix(formula, df, return_type="dataframe")

    # Add constant if not automatically added by formula (dmatrix usually does for intercept)
    # statsmodels GLM requires explicit constant if not in formula, but dmatrix adds intercept by default.
    # However, to be safe and explicit:
    if 'Intercept' not in X.columns:
        X = sm.add_constant(X)

    model = sm.GLM(y, X, family=sm.families.Binomial())
    results = model.fit()

    return results


def write_summary(results: smGLMResultsWrapper, output_path: str) -> None:
    """
    Write regression summary statistics to a JSON file.

    Args:
        results: Fitted GLM results object.
        output_path: Path to the output JSON file.
    """
    summary_dict = {
        "log_likelihood": float(results.llf),
        "aic": float(results.aic),
        "bic": float(results.bic),
        "params": results.params.astype(float).to_dict(),
        "pvalues": results.pvalues.astype(float).to_dict(),
        "converged": bool(results.converged)
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_dict, f, indent=2)


def write_hypothesis_summary(results: smGLMResultsWrapper, output_path: str) -> None:
    """
    Generate a human-readable text summary of the hypothesis test.

    Checks if the interaction term (density * horizon spline) is statistically significant.

    Args:
        results: Fitted GLM results object.
        output_path: Path to the output text file.
    """
    pvalues = results.pvalues
    params = results.params

    # Identify interaction terms (they contain ':')
    interaction_terms = [term for term in pvalues.index if ':' in term]

    significant_interactions = []
    for term in interaction_terms:
        if pvalues[term] < 0.05:
            significant_interactions.append((term, pvalues[term], params[term]))

    hypothesis_supported = len(significant_interactions) > 0

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Hypothesis Summary: Masking Stale Observations & Semantic Density\n")
        f.write("=" * 70 + "\n\n")
        f.write("Hypothesis: There is a positive correlation between semantic density\n")
        f.write("and the optimal retention horizon (i.e., an interaction effect).\n\n")

        if hypothesis_supported:
            f.write("RESULT: SUPPORTED\n\n")
            f.write("The analysis found statistically significant (p < 0.05) interaction\n")
            f.write("terms between semantic density and the retention horizon spline:\n\n")
            for term, p_val, coef in significant_interactions:
                f.write(f"  - {term}: p={p_val:.4f}, coefficient={coef:.4f}\n")
        else:
            f.write("RESULT: NOT SUPPORTED\n\n")
            f.write("No statistically significant interaction terms were found.\n")
            f.write("This suggests that the effect of semantic density on success does not\n")
            f.write("significantly vary with the retention horizon in this dataset.\n")

        f.write("\n--- Full Model Statistics ---\n")
        f.write(f"Log-Likelihood: {results.llf:.4f}\n")
        f.write(f"AIC: {results.aic:.4f}\n")
        f.write(f"BIC: {results.bic:.4f}\n")
        f.write(f"Converged: {results.converged}\n")


def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Analyze simulation results with logistic regression and natural splines."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=DEFAULT_DATA_PATH,
        help="Path to the simulation results JSONL file."
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write analysis outputs."
    )
    parser.add_argument(
        "--df",
        type=int,
        default=DEFAULT_DF,
        help="Degrees of freedom for the natural spline on horizon."
    )

    args = parser.parse_args()

    try:
        # 1. Load Data
        print(f"Loading data from {args.input}...")
        df = load_simulation_data(args.input)
        print(f"Loaded {len(df)} records.")

        # 2. Validate Sample Size
        print("Validating sample size...")
        validate_sample_size(df)

        # 3. Build Formula
        formula = build_formula_with_splines(df, df_horizon=args.df)
        print(f"Using formula: {formula}")

        # 4. Run Regression
        print("Running logistic regression...")
        results = run_logistic_regression(df, formula)

        # 5. Write Outputs
        summary_path = Path(args.output_dir) / "regression_summary.json"
        hypothesis_path = Path(args.output_dir) / "hypothesis_summary.txt"

        print(f"Writing regression summary to {summary_path}...")
        write_summary(results, str(summary_path))

        print(f"Writing hypothesis summary to {hypothesis_path}...")
        write_hypothesis_summary(results, str(hypothesis_path))

        print("Analysis complete.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Data Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()