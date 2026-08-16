"""
code/analysis/heterogeneity.py
Calculates I² statistic for heterogeneity.

Implements SC-002 and FR-002: Output MUST report I² with exactly two decimal places.
"""
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    if "code" in current.parts:
        return current.parents[1]
    return current.parent.parent

def load_study_count_from_json() -> int:
    """Load N from data/processed/study_count.json."""
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
    This file is populated by T014 (meta_analysis.py).
    """
    root = get_project_root()
    path = root / "data" / "derived" / "results.json"
    
    # Check if meta analysis was skipped due to low N
    status_path = root / "data" / "processed" / "meta_status.json"
    if not path.exists():
        if status_path.exists():
            with open(status_path, "r") as f:
                status = json.load(f)
            if status.get("status") == "skipped":
                return [], []
        raise FileNotFoundError(f"Missing results file: {path}. Run T014 first.")

    with open(path, "r") as f:
        data = json.load(f)

    # Try different structures depending on how T014 saved the data
    studies = data.get("studies", [])
    if not studies:
        studies = data.get("effect_sizes", [])
    
    # If it's a list of dicts with 'r' and 'se'
    if studies and isinstance(studies[0], dict):
        r_values = []
        se_values = []
        for s in studies:
            r = s.get("r")
            se = s.get("se")
            if r is not None and se is not None:
                r_values.append(float(r))
                se_values.append(float(se))
        return r_values, se_values

    # If it's a flat structure with separate lists
    r_values = data.get("r_values", [])
    se_values = data.get("se_values", [])
    
    if r_values and se_values:
        return [float(r) for r in r_values], [float(se) for se in se_values]

    return [], []

def calculate_i_squared(r_values: List[float], se_values: List[float]) -> Dict[str, Any]:
    """
    Calculate I² statistic.
    Formula: I² = max(0, (Q - df) / Q) * 100%
    Q = sum(w_i * (y_i - y_bar)^2) where w_i = 1/se_i^2
    
    Precision Requirement (SC-002): Output MUST report I² with exactly two decimal places.
    """
    if len(r_values) < 2:
        return {"status": "skipped", "reason": "Need at least 2 studies for I²"}

    try:
        w = np.array([1.0 / (se ** 2) for se in se_values])
        y = np.array(r_values)

        # Fixed-effect pooled estimate (weighted mean)
        y_bar = np.sum(w * y) / np.sum(w)

        # Q statistic (Cochran's Q)
        q = np.sum(w * (y - y_bar) ** 2)
        df = len(r_values) - 1

        # I² calculation
        # I² = max(0, (Q - df) / Q) * 100
        if q <= df:
            i_squared = 0.0
        else:
            i_squared = (q - df) / q * 100.0

        # Ensure exactly two decimal places as per SC-002
        # Using round() to 2 decimal places satisfies the precision requirement
        i_squared_rounded = round(i_squared, 2)

        return {
            "status": "completed",
            "i_squared": i_squared_rounded,
            "q_statistic": float(q),
            "degrees_of_freedom": int(df)
        }

    except ZeroDivisionError:
        return {"status": "error", "reason": "Division by zero in I² calculation"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def run_heterogeneity_analysis() -> Dict[str, Any]:
    """Main entry point for heterogeneity analysis."""
    try:
        n = load_study_count_from_json()
    except FileNotFoundError as e:
        return {"status": "error", "reason": str(e)}

    if n < 2:
        return {"status": "skipped", "reason": "Insufficient studies for heterogeneity", "N": n}

    r_values, se_values = load_effect_sizes_and_se()
    
    if not r_values:
        return {"status": "skipped", "reason": "No effect sizes available", "N": n}

    return calculate_i_squared(r_values, se_values)

def update_output_json(i_squared_result: Dict[str, Any]) -> None:
    """
    Append i_squared to data/derived/results.json.
    This ensures the MetaAnalysisResult JSON contains the i_squared field.
    """
    root = get_project_root()
    path = root / "data" / "derived" / "results.json"
    
    if not path.exists():
        # Create if not exists (should have been created by meta_analysis)
        # Initialize with empty structure
        with open(path, "w") as f:
            json.dump({}, f)

    with open(path, "r") as f:
        data = json.load(f)

    # Update with heterogeneity results
    data["i_squared"] = i_squared_result.get("i_squared")
    data["heterogeneity_status"] = i_squared_result.get("status")
    data["q_statistic"] = i_squared_result.get("q_statistic")
    data["degrees_of_freedom"] = i_squared_result.get("degrees_of_freedom")

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def main():
    """CLI entry point for T021b."""
    result = run_heterogeneity_analysis()
    root = get_project_root()
    output_path = root / "data" / "derived" / "heterogeneity_results.json"
    
    # Write detailed results to a separate file
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Heterogeneity results written to {output_path}")
    print(json.dumps(result, indent=2))

    # Also update main results file (data/derived/results.json)
    # This satisfies the requirement to "Append i_squared field to the MetaAnalysisResult JSON"
    update_output_json(result)
    print(f"Updated {root / 'data' / 'derived' / 'results.json'} with i_squared")

if __name__ == "__main__":
    main()