"""
Heterogeneity Analysis Module (Task T018)

Calculates the I² statistic to quantify heterogeneity in a meta-analysis.
Reads meta-analysis results and writes a JSON report with the I² value.
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from utils.config import get_project_root


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_effect_sizes_and_se(meta_results_path: Path) -> List[Tuple[float, float]]:
    """
    Load effect sizes (r) and standard errors (se) from meta_results.json.

    The meta_results.json structure is expected to contain a 'studies' list
    or similar where 'effect_size' and 'se' can be extracted.
    If the file does not contain these, it returns an empty list.
    """
    try:
        data = load_json(meta_results_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {meta_results_path}: {e}")
        return []

    studies = data.get("studies", [])
    if not studies:
        # Fallback: check if the file is a list of studies directly
        if isinstance(data, list):
            studies = data
        else:
            return []

    result = []
    for study in studies:
        r = study.get("effect_size") or study.get("r")
        se = study.get("se") or study.get("standard_error")

        if r is not None and se is not None:
            try:
                r_val = float(r)
                se_val = float(se)
                if se_val > 0:
                    result.append((r_val, se_val))
            except (ValueError, TypeError):
                continue
    return result


def load_study_count_from_json(count_path: Path) -> int:
    """Load the study count N from study_count.json."""
    try:
        data = load_json(count_path)
        return int(data.get("N", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return 0


def calculate_i_squared(effect_sizes: List[Tuple[float, float]]) -> float:
    """
    Calculate I² statistic.

    I² = max(0, (Q - df) / Q) * 100%
    Where:
      Q = sum( (effect_i - pooled_effect)^2 / se_i^2 )  (Cochran's Q)
      df = k - 1
      pooled_effect is the fixed-effect weighted mean.

    Returns I² as a percentage (0 to 100).
    """
    k = len(effect_sizes)
    if k < 2:
        return 0.0

    # Calculate weights (inverse variance)
    weights = [1.0 / (se ** 2) for _, se in effect_sizes]
    total_weight = sum(weights)

    if total_weight == 0:
        return 0.0

    # Calculate pooled effect size (fixed-effect weighted mean)
    pooled_effect = sum(w * r for (r, _), w in zip(effect_sizes, weights)) / total_weight

    # Calculate Cochran's Q
    # Q = sum( w_i * (effect_i - pooled)^2 )
    Q = sum(w * ((r - pooled_effect) ** 2) for (r, _), w in zip(effect_sizes, weights))

    df = k - 1

    if Q <= df:
        return 0.0

    i_squared = (Q - df) / Q
    return i_squared * 100.0


def get_heterogeneity_interpretation(i_squared: float) -> str:
    """
    Return a standard interpretation string for the I² value.
    Based on Higgins et al. (2003).
    """
    if i_squared < 25.0:
        return "Low heterogeneity"
    elif i_squared < 50.0:
        return "Moderate heterogeneity"
    elif i_squared < 75.0:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"


def update_output_json(
    output_path: Path,
    i_squared: float,
    interpretation: str,
    k: int,
    q_stat: Optional[float] = None,
) -> None:
    """
    Write the heterogeneity results to the output JSON file.
    Rounds I² to exactly two decimal places.
    """
    data = {
        "i_squared": round(i_squared, 2),
        "interpretation": interpretation,
        "k": k,
        "q_statistic": round(q_stat, 2) if q_stat is not None else None,
        "degrees_of_freedom": k - 1 if k > 0 else 0,
    }
    save_json(output_path, data)


def run_heterogeneity_analysis(
    meta_results_path: Path,
    output_path: Path,
    study_count_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Main function to run the heterogeneity analysis.

    1. Loads effect sizes and SEs from meta_results_path.
    2. Calculates I² and Q statistic.
    3. Writes results to output_path.
    """
    if not meta_results_path.exists():
        result = {
            "status": "error",
            "reason": f"Meta-analysis results file not found: {meta_results_path}",
        }
        save_json(output_path, result)
        return result

    effect_sizes = load_effect_sizes_and_se(meta_results_path)
    k = len(effect_sizes)

    if k < 2:
        result = {
            "status": "skipped",
            "reason": "Insufficient studies (k < 2) to calculate heterogeneity.",
            "i_squared": 0.0,
            "interpretation": "N/A",
            "k": k,
        }
        save_json(output_path, result)
        return result

    i_squared = calculate_i_squared(effect_sizes)
    interpretation = get_heterogeneity_interpretation(i_squared)

    # Recalculate Q for the output if needed (it's used in calculation)
    weights = [1.0 / (se ** 2) for _, se in effect_sizes]
    total_weight = sum(weights)
    pooled_effect = sum(w * r for (r, _), w in zip(effect_sizes, weights)) / total_weight
    Q = sum(w * ((r - pooled_effect) ** 2) for (r, _), w in zip(effect_sizes, weights))

    update_output_json(output_path, i_squared, interpretation, k, Q)

    return {
        "status": "completed",
        "i_squared": round(i_squared, 2),
        "interpretation": interpretation,
        "k": k,
        "q_statistic": round(Q, 2),
    }


def main() -> int:
    """Entry point for the script."""
    project_root = get_project_root()
    meta_results_path = project_root / "data" / "derived" / "meta_results.json"
    output_path = project_root / "data" / "derived" / "heterogeneity_results.json"

    if not meta_results_path.exists():
        print(f"Error: {meta_results_path} not found. Please run meta_analysis.py first.")
        return 1

    result = run_heterogeneity_analysis(meta_results_path, output_path)

    if result.get("status") == "completed":
        print(f"I² calculated: {result['i_squared']}% ({result['interpretation']})")
        print(f"Results written to: {output_path}")
        return 0
    else:
        print(f"Heterogeneity analysis skipped or failed: {result.get('reason', 'Unknown')}")
        return 0  # Returning 0 as it's a valid state (skipped), not an error


if __name__ == "__main__":
    sys.exit(main())