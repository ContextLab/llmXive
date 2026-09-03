"""
Overfitting detection logic for regression models.
Detects high training score vs low validation score scenarios.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from code.config import PROCESSED_PATH, get_logger

logger = get_logger(__name__)

def load_cv_results() -> Dict[str, Any]:
    """
    Load cross-validation results from the aggregated JSON file.
    """
    cv_path = PROCESSED_PATH / "cross_validation_results.json"
    if not cv_path.exists():
        logger.error(f"Cross-validation results file not found: {cv_path}")
        raise FileNotFoundError(f"CV results file not found: {cv_path}")

    with open(cv_path, "r") as f:
        return json.load(f)

def calculate_overfitting_metrics(
    cv_results: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Calculate overfitting metrics for each system.
    Returns a list of dictionaries containing overfitting metrics per system.
    """
    overfitting_metrics = []

    systems = cv_results.get("systems", [])
    if not systems:
        logger.warning("No systems found in CV results.")
        return overfitting_metrics

    for system_data in systems:
        system_name = system_data.get("system_name", "unknown")
        folds = system_data.get("folds", [])

        if not folds:
            logger.warning(f"No folds found for system {system_name}.")
            continue

        train_scores = []
        val_scores = []

        for fold in folds:
            train_score = fold.get("train_score")
            val_score = fold.get("val_score")

            if train_score is not None:
                train_scores.append(train_score)
            if val_score is not None:
                val_scores.append(val_score)

        if not train_scores or not val_scores:
            logger.warning(
                f"Insufficient scores for system {system_name}. Skipping."
            )
            continue

        mean_train_score = np.mean(train_scores)
        mean_val_score = np.mean(val_scores)
        std_val_score = np.std(val_scores)

        # Overfitting gap: difference between training and validation performance
        overfitting_gap = mean_train_score - mean_val_score

        # Relative overfitting ratio
        if mean_val_score != 0:
            overfitting_ratio = overfitting_gap / abs(mean_val_score)
        else:
            overfitting_ratio = float("inf") if overfitting_gap > 0 else 0.0

        overfitting_metrics.append(
            {
                "system_name": system_name,
                "mean_train_score": mean_train_score,
                "mean_val_score": mean_val_score,
                "std_val_score": std_val_score,
                "overfitting_gap": overfitting_gap,
                "overfitting_ratio": overfitting_ratio,
                "num_folds": len(folds),
            }
        )

    return overfitting_metrics

def detect_overfitting(
    metrics: List[Dict[str, Any]],
    gap_threshold: float = 0.15,
    ratio_threshold: float = 0.2,
) -> List[Dict[str, Any]]:
    """
    Detect overfitting based on thresholds.
    Flags systems where:
    - overfitting_gap > gap_threshold
    - overfitting_ratio > ratio_threshold

    Returns a list of flagged systems with details.
    """
    flagged_systems = []

    for m in metrics:
        system_name = m["system_name"]
        gap = m["overfitting_gap"]
        ratio = m["overfitting_ratio"]

        is_overfitting = gap > gap_threshold and ratio > ratio_threshold

        flag_reason = []
        if gap > gap_threshold:
            flag_reason.append(
                f"High gap ({gap:.3f} > {gap_threshold})"
            )
        if ratio > ratio_threshold:
            flag_reason.append(
                f"High ratio ({ratio:.3f} > {ratio_threshold})"
            )

        status = "OVERFITTING_DETECTED" if is_overfitting else "OK"

        flagged_systems.append(
            {
                "system_name": system_name,
                "status": status,
                "overfitting_gap": gap,
                "overfitting_ratio": ratio,
                "mean_train_score": m["mean_train_score"],
                "mean_val_score": m["mean_val_score"],
                "std_val_score": m["std_val_score"],
                "flag_reason": flag_reason if is_overfitting else [],
            }
        )

        if is_overfitting:
            logger.warning(
                f"Overfitting detected for {system_name}: "
                f"Gap={gap:.3f}, Ratio={ratio:.3f}. Reasons: {', '.join(flag_reason)}"
            )
        else:
            logger.info(
                f"System {system_name}: No overfitting detected. "
                f"Gap={gap:.3f}, Ratio={ratio:.3f}"
            )

    return flagged_systems

def save_overfitting_report(
    flagged_systems: List[Dict[str, Any]], output_path: Optional[Path] = None
) -> Path:
    """
    Save overfitting detection report to JSON file.
    """
    if output_path is None:
        output_path = PROCESSED_PATH / "overfitting_report.json"

    report = {
        "total_systems": len(flagged_systems),
        "overfitting_detected_count": sum(
            1 for s in flagged_systems if s["status"] == "OVERFITTING_DETECTED"
        ),
        "systems": flagged_systems,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Overfitting report saved to {output_path}")
    return output_path

def main() -> None:
    """
    Main entry point for overfitting detection.
    """
    logger.info("Starting overfitting detection...")

    try:
        cv_results = load_cv_results()
        metrics = calculate_overfitting_metrics(cv_results)
        flagged_systems = detect_overfitting(metrics)
        report_path = save_overfitting_report(flagged_systems)

        logger.info(f"Overfitting detection complete. Report: {report_path}")

        # Print summary
        overfitting_count = sum(
            1 for s in flagged_systems if s["status"] == "OVERFITTING_DETECTED"
        )
        logger.info(
            f"Summary: {overfitting_count}/{len(flagged_systems)} systems show overfitting."
        )

    except FileNotFoundError as e:
        logger.error(f"Failed to load CV results: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Overfitting detection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
