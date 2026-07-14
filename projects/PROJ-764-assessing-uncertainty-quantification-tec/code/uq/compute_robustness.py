"""
Compute Coefficient of Variation (CV) of ECE scores across multiple runs.

This script reads ECE scores aggregated from multiple seeds (T025a output)
and computes the robustness metric (CV) for each UQ method.

Output: results/robustness_report.json
"""
import os
import json
import logging
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_FILE = "results/ece_scores_by_seed.json"
OUTPUT_FILE = "results/robustness_report.json"
CV_THRESHOLD = 0.05  # Pass if CV <= 0.05

def compute_cv(values):
    """Compute Coefficient of Variation (std / mean)."""
    if len(values) < 2:
        logger.warning(f"Only {len(values)} values provided; cannot compute CV reliably.")
        return float('nan')
    
    mean_val = np.mean(values)
    std_val = np.std(values, ddof=0)  # Population std for consistency across runs
    
    if mean_val == 0:
        logger.warning("Mean ECE is zero; CV is undefined (division by zero).")
        return float('nan')
    
    return std_val / mean_val

def main():
    """Main entry point for robustness computation."""
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T025a has completed and generated results/ece_scores_by_seed.json")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading ECE scores from {input_path}")
    with open(input_path, 'r') as f:
        data = json.load(f)

    # Expected structure: {"method_name": [ece_seed42, ece_seed43, ece_seed44, ...]}
    report = {
        "methods": {},
        "summary": {}
    }

    all_passed = True
    best_method = None
    best_cv = float('inf')

    for method, ece_scores in data.items():
        if not isinstance(ece_scores, list) or len(ece_scores) == 0:
            logger.warning(f"Skipping method '{method}': invalid or empty ECE scores.")
            continue

        cv = compute_cv(ece_scores)
        passed = cv <= CV_THRESHOLD if not np.isnan(cv) else False

        if not passed:
            all_passed = False

        if cv < best_cv and not np.isnan(cv):
            best_cv = cv
            best_method = method

        report["methods"][method] = {
            "ece_scores": ece_scores,
            "mean_ece": float(np.mean(ece_scores)),
            "std_ece": float(np.std(ece_scores, ddof=0)),
            "cv": float(cv) if not np.isnan(cv) else None,
            "pass": passed
        }

        logger.info(f"Method '{method}': Mean ECE={np.mean(ece_scores):.4f}, "
                    f"Std={np.std(ece_scores, ddof=0):.4f}, CV={cv:.4f}, "
                    f"Pass={passed}")

    report["summary"] = {
        "cv_threshold": CV_THRESHOLD,
        "all_methods_pass": all_passed,
        "best_method_by_cv": best_method,
        "best_cv_value": float(best_cv) if not np.isinf(best_cv) else None
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing robustness report to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info("Robustness computation completed successfully.")
    logger.info(f"Overall Pass Status: {'PASS' if all_passed else 'FAIL'} (CV <= {CV_THRESHOLD})")
    logger.info(f"Best Method (lowest CV): {best_method} (CV={best_cv:.4f})")

    # Note: We DO NOT exit with code 1 if pass is false, as per task requirements.
    # The report simply records the finding.

if __name__ == "__main__":
    main()