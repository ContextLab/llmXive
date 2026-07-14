"""
Per‑dataset CI‑width change reporting (Task T037).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        logger.error(f"File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_ci_width_change(baseline: List[Dict[str, Any]], cleaned: List[Dict[str, Any]]) -> List[float]:
    changes = []
    for b, c in zip(baseline, cleaned):
        b_ci = b.get("t_test", {}).get("ci", [0, 0])
        c_ci = c.get("t_test", {}).get("ci", [0, 0])
        b_width = b_ci[1] - b_ci[0]
        c_width = c_ci[1] - c_ci[0]
        changes.append(c_width - b_width)
    return changes

def calculate_median_and_iqr(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"median": float("nan"), "iqr": float("nan")}
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    return {"median": round(median, 4), "iqr": round(iqr, 4)}

def generate_per_dataset_ci_width_report() -> None:
    baseline = load_json(Path("data/processed/baseline_metrics.json"))
    sweep_path = Path("data/processed/outlier_threshold_sweep.json")
    if not sweep_path.is_file():
        logger.error("Sweep summary not found.")
        return
    sweep = json.load(open(sweep_path, "r", encoding="utf-8"))

    all_changes = []
    for k, info in sweep.items():
        cleaned_path = Path(info.get("cleaned_metrics_path", ""))
        if not cleaned_path.is_file():
            continue
        cleaned = load_json(cleaned_path)
        changes = calculate_ci_width_change(baseline, cleaned)
        all_changes.extend(changes)

    stats = calculate_median_and_iqr(all_changes)
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "ci_width_change_median": stats["median"],
        "ci_width_change_iqr": stats["iqr"],
    }
    report_path = Path("output/ci_width_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"CI‑width report written to {report_path}")

def main() -> None:
    generate_per_dataset_ci_width_report()

if __name__ == "__main__":
    main()