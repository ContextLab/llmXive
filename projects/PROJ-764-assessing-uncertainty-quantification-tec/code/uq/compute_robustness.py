import os
import json
import logging
from pathlib import Path
import numpy as np
from typing import Dict, Any

def compute_cv(ece_scores: Dict[str, float]) -> float:
    """Compute Coefficient of Variation for ECE scores."""
    values = [v for v in ece_scores.values() if v is not None]
    if len(values) < 2:
        return None
    mean = np.mean(values)
    std = np.std(values)
    if mean == 0:
        return None
    return std / mean

def main():
    logger = logging.getLogger(__name__)
    logger.info("Computing robustness report...")

    ece_path = Path("results/ece_scores_by_seed.json")
    if not ece_path.exists():
        logger.error("ECE scores file not found. Cannot compute robustness.")
        return

    with open(ece_path) as f:
        ece_scores = json.load(f)

    cv = compute_cv(ece_scores)
    seeds_used = [int(k.split('_')[1]) for k in ece_scores.keys()]

    robustness_report = {
        'cv': cv,
        'pass': cv is not None and cv <= 0.05,
        'seeds_used': seeds_used
    }

    report_path = Path("results/robustness_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(robustness_report, f, indent=2)

    logger.info(f"Saved robustness report to {report_path}")

if __name__ == "__main__":
    main()
