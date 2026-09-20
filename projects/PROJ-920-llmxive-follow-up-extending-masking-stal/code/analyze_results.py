import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrix

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------
def load_simulation_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation results from a JSONL or JSON file.
    Expected columns: 'horizon', 'density', 'success' (0 or 1).
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation data not found at {input_path}")

    if path.suffix == '.jsonl':
        df = pd.read_json(path, lines=True)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
            # Handle if it's a list of records or a dict with a key
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'results' in data:
                df = pd.DataFrame(data['results'])
            else:
                df = pd.DataFrame([data])
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    required_cols = {'horizon', 'density', 'success'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in simulation data: {missing}")

    return df

# -----------------------------------------------------------------------------
# Statistical Validation
# -----------------------------------------------------------------------------
def validate_sample_size(df: pd.DataFrame, min_rows: int = 50) -> bool:
    """
    Check if the dataset has enough rows for statistical power.
    """
    if len(df) < min_rows:
        raise ValueError(f"Sample size ({len(df)}) is too small for reliable regression. Minimum required: {min_rows}")
    return True

# -----------------------------------------------------------------------------
# Model Building
# -----------------------------------------------------------------------------
def build_formula_with_splines(density_col: str = 'density',
                               horizon_col: str = 'horizon',
                               df_spline: int = 3) -> str:
    """
    Construct the Patsy formula with natural splines for the horizon variable
    and an interaction term between density and the spline basis.
    """
    # Natural splines using patsy's bs (B-spline) with constraints for natural
    # boundary conditions. 'df' determines the number of basis functions.
    spline_basis = f"bs({horizon_col}, df={df_spline}, degree=3, include_intercept=False)"
    # Interaction: density * spline_basis
    formula = f"success ~ {density_col} * {spline_basis}"
    return formula

def run_logistic_regression(df: pd.DataFrame,
                            formula: str,
                            df_spline: int = 3) -> Dict[str, Any]:
    """
    Fit a logistic regression model with splines and interaction.
    Returns coefficients, p-values, and model summary stats.
    """
    # Ensure numeric types
    df = df.copy()
    df['success'] = df['success'].astype(int)
    df['density'] = pd.to_numeric(df['density'], errors='coerce')
    df['horizon'] = pd.to_numeric(df['horizon'], errors='coerce')
    df = df.dropna(subset=['density', 'horizon', 'success'])

    if len(df) == 0:
        raise ValueError("Dataset empty after dropping NaNs.")

    # Fit model
    try:
        model = smf.glm(formula=formula, data=df, family=sm.families.Binomial()).fit()
    except Exception as e:
        raise RuntimeError(f"Logistic regression failed: {e}")

    # Extract results
    results = {
        "coefficients": model.params.to_dict(),
        "pvalues": model.pvalues.to_dict(),
        "log_likelihood": model.llf,
        "aic": model.aic,
        "bic": model.bic,
        "nobs": model.nobs
    }

    return results

# -----------------------------------------------------------------------------
# Output Writers
# -----------------------------------------------------------------------------
def write_summary(summary_data: Dict[str, Any], output_path: str) -> None:
    """
    Write regression summary to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(summary_data, f, indent=2)

def write_hypothesis_summary(regression_results: Dict[str, Any],
                             output_path: str) -> None:
    """
    Generate the hypothesis summary markdown file.
    Logic:
    - The hypothesis is: "positive correlation between density and optimal horizon".
    - In the model: success ~ density * bs(horizon).
    - We look for the interaction term(s) between density and the spline basis.
    - If the interaction coefficients are positive and significant (p < 0.05),
      it suggests that as density increases, the effect of horizon on success changes
      in a way that supports the hypothesis (typically shifting the optimal horizon).
    - We check if ANY interaction term involving 'density' is positive and significant.
      If so, hypothesis_supported = True.
    """
    pvalues = regression_results.get("pvalues", {})
    coeffs = regression_results.get("coefficients", {})

    # Identify interaction terms: they contain 'density' and 'bs' (or the horizon variable name)
    # The formula was: success ~ density * bs(horizon, ...)
    # Terms will look like: density, bs(horizon, ...)[I.bs(...)], density:bs(horizon, ...)[I.bs(...)]
    interaction_terms = [k for k in pvalues.keys() if 'density' in k and 'bs' in k]

    hypothesis_supported = False
    significant_positive_interactions = []

    for term in interaction_terms:
        p_val = pvalues.get(term, 1.0)
        coef = coeffs.get(term, 0.0)
        if p_val < 0.05 and coef > 0:
            hypothesis_supported = True
            significant_positive_interactions.append({
                "term": term,
                "coefficient": float(coef),
                "p_value": float(p_val)
            })

    # If no specific interaction terms found or none are significant, check main effect logic?
    # Strictly, the hypothesis is about the INTERACTION. If no significant positive interaction,
    # we cannot support the hypothesis based on this model structure.
    if not significant_positive_interactions:
        hypothesis_supported = False

    summary_content = {
        "hypothesis": "Positive correlation between density and optimal horizon",
        "hypothesis_supported": hypothesis_supported,
        "methodology": "Logistic regression with natural splines for horizon and density interaction",
        "interaction_terms_analyzed": interaction_terms,
        "significant_positive_interactions": significant_positive_interactions,
        "regression_details": {
            "log_likelihood": regression_results.get("log_likelihood"),
            "aic": regression_results.get("aic"),
            "bic": regression_results.get("bic"),
            "n_obs": regression_results.get("nobs")
        }
    }

    # Format as Markdown
    md_lines = [
        "# Hypothesis Summary",
        "",
        f"**Hypothesis**: {summary_content['hypothesis']}",
        f"**Supported**: {summary_content['hypothesis_supported']}",
        "",
        "## Methodology",
        f"{summary_content['methodology']}",
        "",
        "## Regression Details",
        f"- Log-Likelihood: {summary_content['regression_details']['log_likelihood']:.4f}",
        f"- AIC: {summary_content['regression_details']['aic']:.4f}",
        f"- BIC: {summary_content['regression_details']['bic']:.4f}",
        f"- Observations: {summary_content['regression_details']['n_obs']}",
        "",
        "## Interaction Analysis"
    ]

    if significant_positive_interactions:
        md_lines.append("The following interaction terms were **positive and significant** (p < 0.05):")
        md_lines.append("")
        md_lines.append("| Term | Coefficient | P-Value |")
        md_lines.append("|------|-------------|---------|")
        for item in significant_positive_interactions:
            md_lines.append(f"| {item['term']} | {item['coefficient']:.4f} | {item['p_value']:.4f} |")
    else:
        md_lines.append("No interaction terms between density and horizon splines were found to be both positive and statistically significant (p < 0.05).")
        if interaction_terms:
            md_lines.append("Analyzed interaction terms:")
            for t in interaction_terms:
                md_lines.append(f"- {t}: coeff={coeffs.get(t, 0):.4f}, p={pvalues.get(t, 1.0):.4f}")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("*Generated automatically by analyze_results.py*")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write("\n".join(md_lines))

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Analyze simulation results and test hypothesis.")
    parser.add_argument("--input", type=str, required=True, help="Path to simulation results (JSON/JSONL)")
    parser.add_argument("--output-summary", type=str, default="output/regression_summary.json",
                        help="Path for JSON regression summary")
    parser.add_argument("--output-hypothesis", type=str, default="output/hypothesis_summary.md",
                        help="Path for hypothesis summary markdown")
    parser.add_argument("--df", type=int, default=3, help="Degrees of freedom for spline basis")
    parser.add_argument("--min-sample", type=int, default=50, help="Minimum sample size for validation")

    args = parser.parse_args()

    try:
        # 1. Load Data
        df = load_simulation_data(args.input)

        # 2. Validate Sample Size
        validate_sample_size(df, min_rows=args.min_sample)

        # 3. Build Formula
        formula = build_formula_with_splines(df_spline=args.df)

        # 4. Run Regression
        results = run_logistic_regression(df, formula, df_spline=args.df)

        # 5. Write JSON Summary
        write_summary(results, args.output_summary)

        # 6. Write Hypothesis Summary (Markdown)
        write_hypothesis_summary(results, args.output_hypothesis)

        print(f"Analysis complete. Summary written to {args.output_summary}")
        print(f"Hypothesis summary written to {args.output_hypothesis}")

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()