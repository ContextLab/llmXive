"""
GLM Result Extraction Module for PROJ-710.

This module extracts p-values and coefficients from the GLM analysis
performed in glm_analysis.py and saves them to artifacts/glm_summary.json.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import the GLM analysis function from the sibling module
from code.analysis.glm_analysis import fit_coverage_glm
from code.config import get_config


def extract_glm_results(
    coverage_results_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit GLM on coverage data, extract coefficients and p-values, and save to JSON.

    Args:
        coverage_results_path: Path to coverage_results.csv. Defaults to config path.
        output_path: Path to save glm_summary.json. Defaults to config path.

    Returns:
        Dictionary containing the GLM results summary.
    """
    config = get_config()

    # Resolve paths
    if coverage_results_path is None:
        coverage_results_path = str(Path(config.artifacts_dir) / "coverage_results.csv")
    if output_path is None:
        output_path = str(Path(config.artifacts_dir) / "glm_summary.json")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load coverage data
    if not os.path.exists(coverage_results_path):
        raise FileNotFoundError(
            f"Coverage results file not found at {coverage_results_path}. "
            "Please run the coverage simulation pipeline first."
        )

    df = pd.read_csv(coverage_results_path)

    # Validate required columns
    required_cols = ['dataset', 'epsilon', 'noise_type', 'statistic', 'covered']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in coverage results: {missing_cols}"
        )

    # Ensure 'covered' is binary (0 or 1)
    df['covered'] = df['covered'].astype(int)
    if not df['covered'].isin([0, 1]).all():
        raise ValueError("Column 'covered' must contain only 0 or 1 values.")

    # Convert epsilon to numeric
    df['epsilon'] = pd.to_numeric(df['epsilon'], errors='coerce')

    # Drop rows with invalid epsilon
    df = df.dropna(subset=['epsilon'])

    if len(df) == 0:
        raise ValueError("No valid data rows remaining after cleaning.")

    # Fit the GLM
    # Model: covered ~ epsilon + noise_type + epsilon:noise_type
    # We group by dataset and statistic if needed, but the task description
    # implies a global model or a model per group. The spec says "Fit GLM:
    # covered ~ epsilon + noise_type + epsilon:noise_type".
    # To be robust, we will fit one model per unique (dataset, statistic) combination
    # and aggregate the results, or fit a global model with those as factors.
    # Given the formula in the task, we include dataset and statistic as factors
    # to control for them, or we fit separate models.
    # Let's fit a global model including dataset and statistic as fixed effects
    # to maximize power, as is common in meta-analyses of simulation runs.
    # Formula: covered ~ epsilon * noise_type + dataset + statistic
    # This captures the interaction of interest while controlling for dataset differences.

    unique_combinations = df[['dataset', 'statistic']].drop_duplicates().values
    results = {
        "model_specification": "covered ~ epsilon * noise_type + C(dataset) + C(statistic)",
        "global_results": None,
        "per_group_results": [],
        "metadata": {
            "total_observations": len(df),
            "unique_datasets": df['dataset'].nunique(),
            "unique_noise_types": df['noise_type'].nunique(),
            "epsilon_range": [float(df['epsilon'].min()), float(df['epsilon'].max())]
        }
    }

    # Fit global model
    try:
        global_model, global_result = fit_coverage_glm(
            df,
            formula="covered ~ epsilon * noise_type + C(dataset) + C(statistic)"
        )
        results["global_results"] = _result_to_dict(global_result)
    except Exception as e:
        results["global_results"] = {"error": str(e)}

    # Fit per-group models for detailed breakdown
    for dataset, statistic in unique_combinations:
        subset = df[(df['dataset'] == dataset) & (df['statistic'] == statistic)]
        if len(subset) < 10:
            continue  # Skip groups with too few observations

        try:
            model, res = fit_coverage_glm(
                subset,
                formula="covered ~ epsilon * noise_type"
            )
            group_res = {
                "dataset": str(dataset),
                "statistic": str(statistic),
                "observations": len(subset),
                "coefficients": _result_to_dict(res)
            }
            results["per_group_results"].append(group_res)
        except Exception as e:
            results["per_group_results"].append({
                "dataset": str(dataset),
                "statistic": str(statistic),
                "error": str(e)
            })

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    return results


def _result_to_dict(result) -> Dict[str, Any]:
    """Convert a statsmodels GLMResults object to a dictionary."""
    summary_data = {}

    # Extract parameters
    params = result.params
    pvalues = result.pvalues
    conf_int = result.conf_int()

    for term in params.index:
        summary_data[term] = {
            "estimate": float(params[term]),
            "std_error": float(result.bse[term]),
            "z_value": float(result.tvalues[term]),
            "p_value": float(pvalues[term]),
            "ci_lower": float(conf_int.loc[term, 0]),
            "ci_upper": float(conf_int.loc[term, 1])
        }

    # Add model fit statistics
    summary_data["_model_stats"] = {
        "log_likelihood": float(result.llf),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "deviance": float(result.deviance),
        "null_deviance": float(result.null_deviance),
        "converged": bool(result.converged)
    }

    return summary_data


def main():
    """Entry point for the GLM extraction script."""
    print("Starting GLM result extraction...")
    try:
        results = extract_glm_results()
        print(f"Successfully extracted GLM results.")
        print(f"Global model converged: {results['global_results'].get('_model_stats', {}).get('converged', 'N/A')}")
        print(f"Results saved to artifacts/glm_summary.json")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure the coverage simulation pipeline has been run first to generate coverage_results.csv.")
        raise
    except Exception as e:
        print(f"Error during extraction: {e}")
        raise


if __name__ == "__main__":
    main()
