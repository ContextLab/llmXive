"""
code/analysis/bias.py

Implements Egger's regression test for publication bias in meta-analysis.
Reads meta-analysis results and study counts, performs the regression,
and writes the results to data/derived/egger_test.json.
"""

import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent


def load_json(file_path: Path) -> Dict[str, Any]:
    """Loads a JSON file and returns its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Saves a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_study_count_from_json(file_path: Path) -> int:
    """
    Loads the study count N from a JSON file.
    Expects format: {"N": <int>} or {"count": <int>}.
    """
    data = load_json(file_path)
    # Handle different possible keys used in the pipeline
    if 'N' in data:
        return int(data['N'])
    elif 'count' in data:
        return int(data['count'])
    else:
        raise ValueError(f"Could not find 'N' or 'count' in {file_path}")


def load_effect_sizes_and_se(meta_results_path: Path) -> Tuple[List[float], List[float]]:
    """
    Extracts effect sizes (r) and standard errors (SE) from meta_results.json.
    Expected structure in meta_results.json:
    {
      "studies": [
        {"effect_size": r_val, "se": se_val, ...},
        ...
      ],
      ...
    }
    Returns: (list of r, list of SE)
    """
    data = load_json(meta_results_path)
    studies = data.get("studies", [])

    if not studies:
        # Fallback: check if 'results' key exists with studies inside
        results = data.get("results", {})
        studies = results.get("studies", [])

    if not studies:
        raise ValueError("No studies found in meta_results.json")

    r_values = []
    se_values = []

    for study in studies:
        r_val = study.get("effect_size")
        se_val = study.get("se")

        if r_val is not None and se_val is not None:
            # Filter out non-finite values to avoid math errors
            if math.isfinite(r_val) and math.isfinite(se_val) and se_val > 0:
                r_values.append(float(r_val))
                se_values.append(float(se_val))

    return r_values, se_values


def run_eggerr_regression(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Performs Egger's regression test for publication bias.
    Standard Normal Deviate (SND) = r / SE
    Precision = 1 / SE
    Regression: SND ~ Precision
    Intercept significantly different from 0 indicates bias.
    """
    if len(r_values) < 3:
        # Egger's test requires at least 3 studies for meaningful regression
        return {
            "skipped": True,
            "reason": "Insufficient studies (< 3) for Egger's regression",
            "n_studies": len(r_values)
        }

    # Calculate Standard Normal Deviate (SND) and Precision
    snd = [r / se for r, se in zip(r_values, se_values)]
    precision = [1.0 / se for se in se_values]

    # Perform linear regression: SND = beta0 + beta1 * Precision + error
    # We use scipy.stats.linregress
    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(precision, snd)
    except Exception as e:
        return {
            "skipped": True,
            "reason": f"Regression failed: {str(e)}",
            "n_studies": len(r_values)
        }

    # Egger's test statistic is the intercept (beta0)
    # Null hypothesis: intercept = 0 (no bias)
    # We use the t-statistic and p-value from the regression
    t_stat = intercept / std_err if std_err != 0 else 0.0
    df = len(r_values) - 2
    # Two-tailed p-value
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    return {
        "skipped": False,
        "n_studies": len(r_values),
        "intercept": float(intercept),
        "intercept_se": float(std_err),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "slope": float(slope),
        "r_squared": float(r_value ** 2),
        "degrees_of_freedom": df,
        "bias_detected": p_val < 0.05,
        "interpretation": "Significant publication bias detected" if p_val < 0.05 else "No significant publication bias detected"
    }


def run_bias_assessment(meta_results_path: Path, study_count_path: Path) -> Dict[str, Any]:
    """
    Orchestrates the bias assessment:
    1. Loads study count N.
    2. If N < 10, skips Egger's test.
    3. Else, loads effect sizes and SEs, runs regression, returns results.
    """
    try:
        n_studies = load_study_count_from_json(study_count_path)
    except FileNotFoundError:
        return {
            "skipped": True,
            "reason": "Study count file not found",
            "file": str(study_count_path)
        }
    except ValueError as e:
        return {
            "skipped": True,
            "reason": f"Invalid study count: {str(e)}",
            "file": str(study_count_path)
        }

    # Gate logic: Skip if N < 10
    if n_studies < 10:
        return {
            "skipped": True,
            "reason": "N < 10",
            "n_studies": n_studies
        }

    # Load effect sizes and standard errors
    try:
        r_values, se_values = load_effect_sizes_and_se(meta_results_path)
    except FileNotFoundError:
        return {
            "skipped": True,
            "reason": "Meta results file not found",
            "file": str(meta_results_path)
        }
    except ValueError as e:
        return {
            "skipped": True,
            "reason": f"Error loading meta results: {str(e)}",
            "file": str(meta_results_path)
        }

    if not r_values or not se_values:
        return {
            "skipped": True,
            "reason": "No valid effect sizes or standard errors found",
            "n_studies": n_studies
        }

    # Run Egger's regression
    results = run_eggerr_regression(r_values, se_values)
    results["n_studies_checked"] = n_studies
    results["meta_results_file"] = str(meta_results_path)
    results["study_count_file"] = str(study_count_path)

    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Saves the bias assessment results to a JSON file."""
    save_json(results, output_path)


def main() -> int:
    """
    Main entry point for the Egger's bias test script.
    Reads configuration from environment or defaults, runs the test,
    and writes results to data/derived/egger_test.json.
    """
    project_root = get_project_root()

    # Default paths
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    output_path = project_root / "data" / "derived" / "egger_test.json"

    # Allow override via command line args (optional)
    if len(sys.argv) > 1:
        meta_results_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        study_count_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])

    print(f"Running Egger's bias test...")
    print(f"  Meta results: {meta_results_path}")
    print(f"  Study count: {study_count_path}")
    print(f"  Output: {output_path}")

    try:
        results = run_bias_assessment(meta_results_path, study_count_path)
        save_results(results, output_path)
        print(f"Results saved to {output_path}")
        print(f"  Skipped: {results.get('skipped', False)}")
        if not results.get('skipped', False):
            print(f"  P-value: {results.get('p_value', 'N/A'):.4f}")
            print(f"  Bias detected: {results.get('bias_detected', 'N/A')}")
        return 0
    except Exception as e:
        print(f"Error during bias assessment: {str(e)}", file=sys.stderr)
        # Write error result to output file for pipeline consistency
        error_result = {
            "skipped": True,
            "reason": f"Runtime error: {str(e)}",
            "n_studies": 0
        }
        save_results(error_result, output_path)
        return 1


if __name__ == "__main__":
    sys.exit(main())