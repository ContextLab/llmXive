import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrix


def load_simulation_data(input_path: str) -> pd.DataFrame:
    """Load simulation results from CSV or JSON."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation data not found at {input_path}")

    suffix = path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix == '.json':
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def validate_sample_size(df: pd.DataFrame, min_size: int = 30) -> bool:
    """Check if sample size meets minimum requirement for statistical power."""
    if len(df) < min_size:
        return False
    return True


def build_formula_with_splines(df: pd.DataFrame, df_horizon: int = 3) -> str:
    """
    Build Patsy formula with natural splines for horizon and interaction with density.
    Returns a formula string suitable for statsmodels.
    """
    # Create natural spline basis for 'horizon'
    # We use 'ns' (natural spline) from patsy
    # Formula: success ~ density * ns(horizon, df)
    formula = f"success ~ density * ns(horizon, df={df_horizon})"
    return formula


def run_logistic_regression(df: pd.DataFrame, df_horizon: int = 3) -> Dict[str, Any]:
    """
    Run logistic regression with natural splines on horizon and interaction with density.
    Returns regression results and interaction p-values.
    """
    formula = build_formula_with_splines(df, df_horizon)

    # Create design matrix
    y, X = dmatrix(formula, data=df, return_type="dataframe")

    # Remove intercept if present (dmatrix adds it by default)
    # statsmodels Logit expects no intercept if we want to handle it explicitly,
    # but dmatrix includes it. We'll let statsmodels handle it.

    model = sm.Logit(y, X)
    result = model.fit(disp=False)

    # Extract interaction terms
    # Interaction terms are those containing 'density' and 'ns(horizon'
    interaction_terms = []
    interaction_pvalues = []
    interaction_names = []

    for param_name, pval in zip(result.params.index, result.pvalues):
        if 'density' in param_name and 'ns(horizon' in param_name:
            interaction_terms.append({
                'name': param_name,
                'coefficient': float(result.params[param_name]),
                'p_value': float(pval),
                'significant': pval < 0.05
            })
            interaction_names.append(param_name)
            interaction_pvalues.append(pval)

    # Overall model summary
    summary = {
        'n_samples': len(df),
        'n_parameters': len(result.params),
        'log_likelihood': float(result.llf),
        'aic': float(result.aic),
        'bic': float(result.bic),
        'interaction_terms': interaction_terms,
        'any_interaction_significant': any(t['significant'] for t in interaction_terms),
        'all_pvalues': {str(k): float(v) for k, v in zip(result.params.index, result.pvalues)}
    }

    return summary


def write_summary(summary: Dict[str, Any], output_path: str) -> None:
    """Write regression summary to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(summary, f, indent=2)


def write_hypothesis_summary(summary: Dict[str, Any], output_path: str) -> None:
    """Write human-readable hypothesis summary based on regression results."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Determine if hypothesis is supported
    # Hypothesis: positive correlation between density and optimal horizon
    # This means the interaction term should be significant
    any_sig = summary.get('any_interaction_significant', False)
    interaction_terms = summary.get('interaction_terms', [])

    # Check if any interaction term is significant and positive
    supported = False
    reasoning = []

    if any_sig:
        positive_interactions = [t for t in interaction_terms if t['coefficient'] > 0 and t['significant']]
        if positive_interactions:
            supported = True
            reasoning.append(f"Found {len(positive_interactions)} significant positive interaction term(s).")
        else:
            reasoning.append("Interaction terms are significant but not all positive.")
    else:
        reasoning.append("No significant interaction terms found (p >= 0.05).")

    with open(path, 'w') as f:
        f.write("Hypothesis Summary\n")
        f.write("==================\n\n")
        f.write(f"Hypothesis: Positive correlation between semantic density and optimal masking horizon.\n\n")
        f.write(f"Result: {'SUPPORTED' if supported else 'NOT SUPPORTED'}\n\n")
        f.write("Reasoning:\n")
        for r in reasoning:
            f.write(f"  - {r}\n")
        f.write("\n")
        f.write(f"Total samples analyzed: {summary['n_samples']}\n")
        f.write(f"Number of interaction terms tested: {len(interaction_terms)}\n")

        if interaction_terms:
            f.write("\nInteraction Terms:\n")
            for term in interaction_terms:
                f.write(f"  - {term['name']}: coeff={term['coefficient']:.4f}, p={term['p_value']:.4f}, sig={term['significant']}\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze simulation results with logistic regression")
    parser.add_argument("--input", type=str, required=True, help="Path to simulation results (CSV or JSON)")
    parser.add_argument("--output-summary", type=str, default="output/regression_summary.json",
                        help="Path to output regression summary JSON")
    parser.add_argument("--output-hypothesis", type=str, default="output/hypothesis_summary.txt",
                        help="Path to output hypothesis summary text")
    parser.add_argument("--df", type=int, default=3, help="Degrees of freedom for natural splines")
    parser.add_argument("--min-sample", type=int, default=30, help="Minimum sample size for validation")

    args = parser.parse_args()

    # Load data
    df = load_simulation_data(args.input)

    # Validate sample size
    if not validate_sample_size(df, args.min_sample):
        print(f"Error: Sample size {len(df)} is below minimum {args.min_sample}")
        sys.exit(1)

    # Run regression
    summary = run_logistic_regression(df, args.df)

    # Write outputs
    write_summary(summary, args.output_summary)
    write_hypothesis_summary(summary, args.output_hypothesis)

    print(f"Regression summary written to: {args.output_summary}")
    print(f"Hypothesis summary written to: {args.output_hypothesis}")


if __name__ == "__main__":
    main()