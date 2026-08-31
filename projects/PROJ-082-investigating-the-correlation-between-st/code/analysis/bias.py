"""
Egger's Regression Test for Publication Bias.

This module implements Egger's linear regression test to detect small-study effects
(a potential indicator of publication bias) in a meta-analysis.

Logic:
1. Read N (study count) from data/processed/study_count.json.
2. If N < 10: Skip analysis, record status as 'skipped', and write to data/derived/results.json.
3. If 10 <= N < 20: Run regression but append a 'low_power_warning' flag.
4. If N >= 20: Run standard regression.
5. The regression model is: Z_i / SE_i = beta_0 + beta_1 * (1 / SE_i) + epsilon_i
   where the intercept (beta_0) tests for bias.
6. Append results (intercept, p-value, warning flags) to data/derived/results.json.
"""

import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# --------------------------------------------------------------------------
# Helper Functions (Path & IO)
# --------------------------------------------------------------------------

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def load_json(file_path: Path) -> Dict[str, Any]:
    """Loads a JSON file and returns its content."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Saves data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

# --------------------------------------------------------------------------
# Data Loading
# --------------------------------------------------------------------------

def load_study_count_from_json() -> int:
    """
    Reads N from data/processed/study_count.json.
    Returns the count of unique studies.
    """
    project_root = get_project_root()
    path = project_root / "data" / "processed" / "study_count.json"
    try:
        data = load_json(path)
        return int(data.get("N", 0))
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as e:
        raise RuntimeError(f"Failed to load study count: {e}")

def load_effect_sizes_and_se() -> List[Tuple[float, float]]:
    """
    Reads extracted studies from data/processed/extracted_studies.csv.
    Returns a list of tuples (r, se) for rows where both are valid numbers.
    """
    project_root = get_project_root()
    path = project_root / "data" / "processed" / "extracted_studies.csv"

    if not path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {path}")

    results = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_val = row.get('r')
            se_val = row.get('se')

            if r_val is not None and se_val is not None:
                try:
                    r_float = float(r_val)
                    se_float = float(se_val)
                    # Filter out non-positive SEs which break the regression
                    if se_float > 0 and not math.isnan(r_float) and not math.isnan(se_float):
                        results.append((r_float, se_float))
                except (ValueError, TypeError):
                    continue

    return results

# --------------------------------------------------------------------------
# Core Logic: Egger's Regression
# --------------------------------------------------------------------------

def run_eggerr_regression(effects: List[Tuple[float, float]]) -> Dict[str, Any]:
    """
    Performs Egger's linear regression test.
    Model: Z_i / SE_i = beta_0 + beta_1 * (1 / SE_i) + epsilon_i
    where Z_i is the effect size (r) and SE_i is the standard error.
    We test if the intercept (beta_0) is significantly different from 0.

    Returns a dict with:
      - intercept: beta_0
      - intercept_pvalue: p-value for the intercept
      - slope: beta_1
      - r_squared: R-squared of the fit
      - n_studies: number of studies used
    """
    if len(effects) < 2:
        return {
            "intercept": None,
            "intercept_pvalue": None,
            "slope": None,
            "r_squared": None,
            "n_studies": len(effects),
            "error": "Insufficient data points for regression (need >= 2)"
        }

    r_vals = np.array([e[0] for e in effects])
    se_vals = np.array([e[1] for e in effects])

    # Precision weight (1/SE)
    precision = 1.0 / se_vals

    # Standardized Effect (Z approx = r / SE)
    # Note: In strict Egger's for correlation, we often use Fisher's Z,
    # but given the data is 'r', we use r/SE as the standard metric in this context.
    standardized_effect = r_vals / se_vals

    # Linear Regression: standardized_effect ~ precision
    # Using scipy.stats.linregress
    slope, intercept, r_value, p_value, std_err = stats.linregress(precision, standardized_effect)

    return {
        "intercept": float(intercept),
        "intercept_pvalue": float(p_value),
        "slope": float(slope),
        "r_squared": float(r_value ** 2),
        "n_studies": len(effects),
        "error": None
    }

# --------------------------------------------------------------------------
# Main Orchestration Logic
# --------------------------------------------------------------------------

def run_bias_assessment() -> Dict[str, Any]:
    """
    Orchestrates the bias assessment:
    1. Check N. If < 10, skip.
    2. Load effects.
    3. Run regression.
    4. Append low-power warning if 10 <= N < 20.
    5. Return results dict to be merged into results.json.
    """
    project_root = get_project_root()
    results_path = project_root / "data" / "derived" / "results.json"

    # 1. Check Study Count
    try:
        n = load_study_count_from_json()
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}

    bias_result = {
        "eggers_test": {
            "status": "skipped",
            "reason": "Insufficient studies (N < 10)",
            "N": n
        },
        "low_power_warning": False
    }

    if n < 10:
        return bias_result

    # 2. Load Data
    try:
        effects = load_effect_sizes_and_se()
    except FileNotFoundError as e:
        return {"status": "error", "message": str(e)}

    if len(effects) < 2:
        bias_result["eggers_test"] = {
            "status": "skipped",
            "reason": f"Insufficient valid effect sizes (found {len(effects)}, need >= 2)",
            "N": n
        }
        return bias_result

    # 3. Run Regression
    regression_stats = run_eggerr_regression(effects)

    if regression_stats.get("error"):
        bias_result["eggers_test"] = {
            "status": "failed",
            "reason": regression_stats["error"],
            "N": n
        }
        return bias_result

    # 4. Construct Result
    eggers_outcome = "no_bias_detected"
    p_val = regression_stats["intercept_pvalue"]
    if p_val is not None and p_val < 0.05:
        eggers_outcome = "significant_small_study_effect"

    bias_result["eggers_test"] = {
        "status": "completed",
        "N": n,
        "intercept": regression_stats["intercept"],
        "intercept_pvalue": p_val,
        "slope": regression_stats["slope"],
        "r_squared": regression_stats["r_squared"],
        "outcome": eggers_outcome
    }

    # 5. Low Power Warning
    if 10 <= n < 20:
        bias_result["low_power_warning"] = True
        bias_result["eggers_test"]["note"] = "Low statistical power due to small sample size (10 <= N < 20). Interpret with caution."

    return bias_result

def save_results(bias_result: Dict[str, Any]) -> None:
    """
    Loads existing data/derived/results.json (if exists) or creates a new one,
    then updates/merges the bias assessment results.
    """
    project_root = get_project_root()
    results_path = project_root / "data" / "derived" / "results.json"

    # Load existing or create new
    if results_path.exists():
        try:
            existing = load_json(results_path)
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}

    # Merge
    existing["bias_assessment"] = bias_result

    # Save
    save_json(results_path, existing)

# --------------------------------------------------------------------------
# CLI Entry Point
# --------------------------------------------------------------------------

def main() -> int:
    """
    CLI entry point for Egger's Regression Test.
    """
    try:
        # Run assessment
        result = run_bias_assessment()

        # Save to results.json
        save_results(result)

        # Log status
        status = result.get("eggers_test", {}).get("status", "unknown")
        if status == "skipped":
            reason = result.get("eggers_test", {}).get("reason", "Unknown")
            print(f"Egger's Test SKIPPED: {reason}")
        elif status == "completed":
            p_val = result.get("eggers_test", {}).get("intercept_pvalue")
            warning = " [LOW POWER WARNING]" if result.get("low_power_warning") else ""
            print(f"Egger's Test COMPLETED (P={p_val:.4f}){warning}")
        else:
            print(f"Egger's Test FAILED: {result.get('eggers_test', {}).get('reason', 'Unknown error')}")

        return 0
    except Exception as e:
        print(f"Error running bias assessment: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())