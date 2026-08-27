import os
import json
import logging
from pathlib import Path
import numpy as np

from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def compute_cv(ece_scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute the Coefficient of Variation (CV) of ECE scores across seeds.

    Args:
        ece_scores: Dictionary loaded from results/ece_scores_by_seed.json.
                    Expected structure:
                    {
                        "Deep Ensembles": [val1, val2, val3],
                        "MC Dropout": [val1, val2, val3],
                        "Sparse GP": [val1, val2, val3],
                        ...
                    }

    Returns:
        Dictionary containing:
            - "cv_scores": Dict mapping method name to its CV.
            - "pass": True if ALL methods have CV <= 0.05, False otherwise.
            - "details": Detailed breakdown for reporting.
    """
    cv_scores = {}
    all_pass = True
    details = {}

    for method, scores in ece_scores.items():
        if not isinstance(scores, list) or len(scores) == 0:
            logger.warning(f"No scores found for method: {method}")
            continue

        scores_array = np.array(scores, dtype=float)
        mean_val = np.mean(scores_array)
        std_val = np.std(scores_array, ddof=0)  # Population std for CV calculation

        if mean_val == 0:
            # Avoid division by zero; if mean is 0 and std is 0, CV is 0.
            # If mean is 0 and std > 0, CV is undefined (set to large number or 0 depending on logic).
            # Here, if mean is 0, we treat it as perfect stability if std is 0.
            cv = 0.0 if std_val == 0 else float('inf')
        else:
            cv = std_val / mean_val

        cv_scores[method] = cv
        
        # Check threshold
        method_pass = cv <= 0.05
        if not method_pass:
            all_pass = False

        details[method] = {
            "mean_ece": float(mean_val),
            "std_ece": float(std_val),
            "cv": float(cv),
            "pass": method_pass,
            "scores": [float(s) for s in scores]
        }

    return {
        "cv_scores": cv_scores,
        "pass": all_pass,
        "details": details,
        "threshold": 0.05
    }

def main():
    """
    Main entry point to compute robustness report.
    Reads results/ece_scores_by_seed.json and writes results/robustness_report.json.
    """
    # Define paths relative to project root
    # Assuming this script runs from project root or is invoked via python -m
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "results" / "ece_scores_by_seed.json"
    output_path = project_root / "results" / "robustness_report.json"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T025a has been completed and generated the ECE scores file."
        )

    logger.info(f"Loading ECE scores from {input_path}")
    with open(input_path, "r") as f:
        ece_scores = json.load(f)

    logger.info("Computing Coefficient of Variation (CV) for each method")
    result = compute_cv(ece_scores)

    logger.info(f"Robustness check result: {'PASS' if result['pass'] else 'FAIL'}")
    logger.info(f"Writing robustness report to {output_path}")

    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info("Robustness report generation complete.")

if __name__ == "__main__":
    main()