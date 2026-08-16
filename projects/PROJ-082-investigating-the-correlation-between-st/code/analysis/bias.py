"""
code/analysis/bias.py
Implements Egger's linear regression test for publication bias.

This module performs Egger's test to detect asymmetry in funnel plots,
which may indicate publication bias or other small-study effects.

Skip Logic:
- Explicitly SKIPS if N (from data/processed/study_count.json) < 10.
- Outputs exact string 'egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"'
  when skipped.
"""
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Project root resolution
def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up to find the project root (assumes code/analysis/bias.py structure)
    # Usually root is parent of 'code'
    if "code" in current.parts:
        return current.parents[1]
    return current.parent.parent

def load_study_count_from_json() -> int:
    """
    Load N from data/processed/study_count.json.
    Raises FileNotFoundError if missing.
    """
    root = get_project_root()
    path = root / "data" / "processed" / "study_count.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing study count file: {path}. Run T014a first.")
    with open(path, "r") as f:
        data = json.load(f)
    return int(data.get("N", 0))

def load_effect_sizes_and_se() -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors (se) from data/derived/results.json.
    Assumes the meta-analysis has been run and populated 'studies' list or similar.
    If meta-analysis was skipped (N < 10), this should return empty lists or raise.
    """
    root = get_project_root()
    path = root / "data" / "derived" / "results.json"
    
    # Check if meta-analysis was skipped first
    status_path = root / "data" / "processed" / "meta_status.json"
    if status_path.exists():
        with open(status_path, "r") as f:
            status = json.load(f)
        if status.get("status") == "skipped":
            return [], []
    
    if not path.exists():
        raise FileNotFoundError(f"Missing results file: {path}")

    with open(path, "r") as f:
        data = json.load(f)

    # Expecting a list of studies with 'r' and 'se' or similar
    studies = data.get("studies", [])
    if not studies:
        # Try alternative key if structure varies
        studies = data.get("effect_sizes", [])

    r_values = []
    se_values = []

    for s in studies:
        if isinstance(s, dict):
            r = s.get("r")
            se = s.get("se")
            if r is not None and se is not None:
                r_values.append(float(r))
                se_values.append(float(se))

    return r_values, se_values

def run_eggerr_regression(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Run Egger's linear regression test.
    Returns dict with intercept, p_value, and status.
    
    Egger's test regression:
    - Dependent variable (y): Standard Normal Deviate (SND) = r / SE
    - Independent variable (x): Precision = 1 / SE
    - Significant intercept indicates asymmetry (potential publication bias)
    """
    if len(r_values) < 10:
        return {
            "status": "skipped",
            "reason": "Insufficient studies (N < 10) for Egger's regression",
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }

    if not r_values or not se_values:
        return {
            "status": "skipped",
            "reason": "No valid effect sizes provided",
            "egger_skipped_reason": "Skipped: No valid effect sizes provided"
        }

    try:
        # Egger's test: Standard Normal Deviate (SND) vs Precision (1/SE)
        # SND = r / SE
        # Precision = 1 / SE
        # Regression: SND ~ Precision
        
        z_scores = [r / se for r, se in zip(r_values, se_values)]
        precision = [1.0 / se for se in se_values]

        x = np.array(precision)
        y = np.array(z_scores)

        # Linear regression
        slope, intercept, r_val, p_value, std_err = stats.linregress(x, y)

        return {
            "status": "completed",
            "intercept": float(intercept),
            "p_value": float(p_value),
            "slope": float(slope),
            "r_squared": float(r_val ** 2)
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": f"Regression failed: {str(e)}"
        }

def run_bias_assessment() -> Dict[str, Any]:
    """
    Main entry point for bias assessment.
    Reads N, checks skip condition, runs regression if eligible.
    
    Skip Logic:
    - If N < 10, returns skip status with exact egger_skipped_reason string.
    - If N >= 10, runs Egger's regression and returns results.
    """
    try:
        n = load_study_count_from_json()
    except FileNotFoundError as e:
        return {
            "status": "error",
            "reason": str(e)
        }

    if n < 10:
        return {
            "status": "skipped",
            "reason": "Insufficient studies",
            "N": n,
            "egger_skipped_reason": "Skipped: Insufficient studies (N < 10) for Egger's regression"
        }

    r_values, se_values = load_effect_sizes_and_se()
    
    if not r_values:
        return {
            "status": "skipped",
            "reason": "No effect sizes available in results",
            "N": n,
            "egger_skipped_reason": "Skipped: No effect sizes available in results"
        }

    return run_eggerr_regression(r_values, se_values)

def main():
    """CLI entry point."""
    result = run_bias_assessment()
    root = get_project_root()
    output_path = root / "data" / "derived" / "bias_results.json"
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Bias assessment results written to {output_path}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()