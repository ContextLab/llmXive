"""
Per‑dataset p‑value shift reporting (Task T036).

Utilises the sweep summary to compute median and IQR of p‑value shifts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def load_metrics(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        logger.error(f"Metrics file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_p_value_shifts(baseline: List[Dict[str, Any]], cleaned: List[Dict[str, Any]]) -> List[float]:
    shifts = []
    for b, c in zip(baseline, cleaned):
        b_p = b.get("t_test", {}).get("p_value", 1)
        c_p = c.get("t_test", {}).get("p_value", 1)
        shifts.append(abs(b_p - c_p))
    return shifts

def calculate_median_and_iqr(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"median": float("nan"), "iqr": float("nan")}
    arr = np.array(values)
    median = float(np.median(arr))
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    return {"median": round(median, 4), "iqr": round(iqr, 4)}

def generate_per_dataset_pvalue_shift_report() -> None:
    baseline = load_metrics(Path("data/processed/baseline_metrics.json"))
    sweep_path = Path("data/processed/outlier_threshold_sweep.json")
    if not sweep_path.is_file():
        logger.error("Sweep summary not found.")
        return
    sweep = json.load(open(sweep_path, "r", encoding="utf-8"))

    all_shifts = []
    for k, info in sweep.items():
        cleaned_path = Path(info.get("cleaned_metrics_path", ""))
        if not cleaned_path.is_file():
            continue
        cleaned = load_metrics(cleaned_path)
        shifts = calculate_p_value_shifts(baseline, cleaned)
        all_shifts.extend(shifts)

    stats = calculate_median_and_iqr(all_shifts)
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "p_value_shift_median": stats["median"],
        "p_value_shift_iqr": stats["iqr"],
    }
    report_path = Path("output/pvalue_shift_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"P‑value shift report written to {report_path}")

def main() -> None:
    generate_per_dataset_pvalue_shift_report()

if __name__ == "__main__":
    main()