"""
Multiple Comparison Correction for Meta-Analysis Results.

This module implements Bonferroni correction for multiple comparisons
when analyzing multiple brain tracts. It reads tract counts and study
counts from processed data files and applies the correction logic.
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume project root is 2 levels up from this file
    return Path(__file__).resolve().parent.parent.parent

def load_tract_data_from_json(file_path: str) -> Dict[str, Any]:
    """
    Load tract count data from a JSON file.

    Args:
        file_path: Path to the tract_count.json file.

    Returns:
        Dictionary containing tract count data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Tract count file not found: {file_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    return data

def load_study_count_from_json(file_path: str) -> Dict[str, Any]:
    """
    Load study count data from a JSON file.

    Args:
        file_path: Path to the study_count.json file.

    Returns:
        Dictionary containing study count data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Study count file not found: {file_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    return data

def count_unique_tracts(tract_data: Dict[str, Any]) -> int:
    """
    Extract the number of unique tracts from tract data.

    Args:
        tract_data: Dictionary containing tract count information.

    Returns:
        The number of unique tracts (k).
    """
    return tract_data.get('k', 0)

def apply_bonferroni_correction(p_values: List[float], k: int) -> Tuple[List[float], float]:
    """
    Apply Bonferroni correction to a list of p-values.

    The Bonferroni correction divides the significance threshold (alpha)
    by the number of comparisons (k) to control the family-wise error rate.

    Args:
        p_values: List of raw p-values from statistical tests.
        k: Number of comparisons (tracts).

    Returns:
        Tuple of (adjusted_p_values, adjusted_threshold).
        adjusted_p_values: List of p-values multiplied by k (capped at 1.0).
        adjusted_threshold: The new significance threshold (0.05 / k).
    """
    if k <= 0:
        return p_values, 0.05

    adjusted_threshold = 0.05 / k
    adjusted_p_values = [min(p * k, 1.0) for p in p_values]

    return adjusted_p_values, adjusted_threshold

def run_correction_analysis() -> Dict[str, Any]:
    """
    Run the multiple comparison correction analysis.

    This function:
    1. Reads tract count (k) from data/processed/tract_count.json
    2. Reads study count (N) from data/processed/study_count.json
    3. Applies Bonferroni correction if k >= 2 and N >= 10
    4. Generates a limitations note for the final results
    5. Returns a dictionary with correction results

    Returns:
        Dictionary containing correction analysis results.
    """
    project_root = get_project_root()
    tract_count_path = project_root / "data" / "processed" / "tract_count.json"
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    results_path = project_root / "data" / "derived" / "results.json"

    result = {
        "bonferroni_applied": False,
        "k": 0,
        "N": 0,
        "adjusted_threshold": 0.05,
        "reason": "",
        "limitations_note": ""
    }

    # Load tract count data
    try:
        tract_data = load_tract_data_from_json(str(tract_count_path))
        k = count_unique_tracts(tract_data)
        result["k"] = k
        logger.info(f"Loaded tract count: k = {k}")
    except FileNotFoundError as e:
        logger.warning(f"Tract count file not found: {e}")
        result["reason"] = "Tract count file missing - Bonferroni correction skipped"
        result["limitations_note"] = "Limitations: Bonferroni correction could not be applied due to missing tract count data."
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in tract count file: {e}")
        result["reason"] = "Tract count file contains invalid JSON - Bonferroni correction skipped"
        result["limitations_note"] = "Limitations: Bonferroni correction could not be applied due to invalid tract count data."
        return result

    # Load study count data
    try:
        study_data = load_study_count_from_json(str(study_count_path))
        N = study_data.get("N", 0)
        result["N"] = N
        logger.info(f"Loaded study count: N = {N}")
    except FileNotFoundError as e:
        logger.warning(f"Study count file not found: {e}")
        result["reason"] = "Study count file missing - Bonferroni correction skipped"
        result["limitations_note"] = "Limitations: Bonferroni correction could not be applied due to missing study count data."
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in study count file: {e}")
        result["reason"] = "Study count file contains invalid JSON - Bonferroni correction skipped"
        result["limitations_note"] = "Limitations: Bonferroni correction could not be applied due to invalid study count data."
        return result

    # Decision logic for Bonferroni correction
    if k < 2:
        logger.warning(f"Bonferroni correction skipped: k < 2 (k={k})")
        result["reason"] = f"Bonferroni correction skipped: k < 2 (k={k})"
        result["limitations_note"] = "Limitations: Bonferroni correction was not applied because there were fewer than 2 tracts to compare."
        result["bonferroni_applied"] = False
    elif N < 10:
        logger.warning(f"Bonferroni correction skipped: N < 10 (N={N})")
        result["reason"] = f"Bonferroni correction skipped: N < 10 (N={N})"
        result["limitations_note"] = "Limitations: Bonferroni correction was not applied because there were fewer than 10 studies (N < 10)."
        result["bonferroni_applied"] = False
    else:
        # Apply Bonferroni correction
        adjusted_threshold = 0.05 / k
        result["bonferroni_applied"] = True
        result["adjusted_threshold"] = adjusted_threshold
        result["reason"] = f"Bonferroni correction applied: k={k}, N={N}, adjusted alpha = {adjusted_threshold:.6f}"
        result["limitations_note"] = "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
        logger.info(f"Bonferroni correction applied: k={k}, N={N}, adjusted alpha = {adjusted_threshold:.6f}")

    # Save results to a temporary file for integration with main pipeline
    # The main pipeline will merge this into the final results.json
    correction_output_path = project_root / "data" / "derived" / "correction_results.json"
    with open(correction_output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Correction results saved to {correction_output_path}")

    return result

def main():
    """Main entry point for the correction analysis."""
    logger.info("Starting multiple comparison correction analysis...")
    result = run_correction_analysis()

    print("\n=== Multiple Comparison Correction Results ===")
    print(f"Bonferroni Applied: {result['bonferroni_applied']}")
    print(f"Number of Tracts (k): {result['k']}")
    print(f"Number of Studies (N): {result['N']}")
    print(f"Adjusted Threshold: {result['adjusted_threshold']}")
    print(f"Reason: {result['reason']}")
    print(f"Limitations Note: {result['limitations_note']}")
    print("=" * 50)

    return result

if __name__ == "__main__":
    main()