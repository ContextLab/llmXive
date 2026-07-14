"""
Forest‑plot generation (Task T034).

The script now reads the sweep summary produced by T033 and creates a
PNG visualisation saved under ``output/forest_plot.png``.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def load_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        logger.error(f"File not found: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_p_value_shift(baseline: List[Dict[str, Any]], cleaned: List[Dict[str, Any]]) -> List[float]:
    """
    Compute absolute p‑value shift for each dataset.
    """
    shifts = []
    for b, c in zip(baseline, cleaned):
        b_p = b.get("t_test", {}).get("p_value", 1)
        c_p = c.get("t_test", {}).get("p_value", 1)
        shifts.append(abs(b_p - c_p))
    return shifts

def load_metrics_for_plotting(sweep_path: Path) -> List[float]:
    """
    Load the forest‑plot data (p‑value shifts) from the sweep summary.
    """
    sweep = load_json(sweep_path)
    shifts = []
    for k, info in sweep.items():
        # The cleaned metrics for each k are stored separately; we load them
        cleaned_path = Path(info.get("cleaned_metrics_path", ""))
        if not cleaned_path.is_file():
            continue
        cleaned = load_json(cleaned_path)
        baseline_path = Path("data/processed/baseline_metrics.json")
        baseline = load_json(baseline_path)
        shifts.extend(calculate_p_value_shift(baseline, cleaned))
    return shifts

def generate_forest_plot(sweep_path: Path, output_path: Path) -> None:
    shifts = load_metrics_for_plotting(sweep_path)
    if not shifts:
        logger.warning("No p‑value shift data available for forest plot.")
        return

    plt.figure(figsize=(8, 6))
    y_pos = range(len(shifts))
    plt.barh(y_pos, shifts, align='center')
    plt.yticks(y_pos, [f"Dataset {i+1}" for i in y_pos])
    plt.xlabel("Absolute p‑value shift")
    plt.title("Forest plot of p‑value shifts across outlier thresholds")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Forest plot saved to {output_path}")

def main() -> None:
    sweep_path = Path("data/processed/outlier_threshold_sweep.json")
    output_path = Path("output/forest_plot.png")
    generate_forest_plot(sweep_path, output_path)

if __name__ == "__main__":
    main()