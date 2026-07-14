"""
CI‑width heatmap generation (Task T035).

Reads the cleaned metrics for each threshold and visualises the change in
confidence‑interval width relative to the baseline.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from utils import setup_logging

logger = setup_logging(log_level="INFO")

def load_ci_width_changes(baseline: List[Dict[str, Any]], cleaned: List[Dict[str, Any]]) -> List[float]:
    changes = []
    for b, c in zip(baseline, cleaned):
        b_ci = b.get("t_test", {}).get("ci", [0, 0])
        c_ci = c.get("t_test", {}).get("ci", [0, 0])
        b_width = b_ci[1] - b_ci[0]
        c_width = c_ci[1] - c_ci[0]
        changes.append(c_width - b_width)
    return changes

def aggregate_for_heatmap(sweep_path: Path) -> pd.DataFrame:
    """
    Produce a DataFrame with rows = thresholds, columns = dataset indices,
    values = CI‑width change.
    """
    sweep = json.load(open(sweep_path, "r", encoding="utf-8"))
    baseline_path = Path("data/processed/baseline_metrics.json")
    baseline = json.load(open(baseline_path, "r", encoding="utf-8"))

    data = {}
    for k, info in sweep.items():
        cleaned_path = Path(info.get("cleaned_metrics_path", ""))
        if not cleaned_path.is_file():
            continue
        cleaned = json.load(open(cleaned_path, "r", encoding="utf-8"))
        changes = load_ci_width_changes(baseline, cleaned)
        data[f"k={k}"] = changes

    df = pd.DataFrame(data)
    return df

def generate_heatmap(sweep_path: Path, output_path: Path) -> None:
    df = aggregate_for_heatmap(sweep_path)
    if df.empty:
        logger.warning("No CI‑width change data available for heatmap.")
        return
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.T, annot=True, fmt=".3f", cmap="viridis")
    plt.title("CI‑width changes across outlier thresholds")
    plt.xlabel("Dataset index")
    plt.ylabel("Threshold")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"CI heatmap saved to {output_path}")

def main() -> None:
    sweep_path = Path("data/processed/outlier_threshold_sweep.json")
    output_path = Path("output/ci_heatmap.png")
    generate_heatmap(sweep_path, output_path)

if __name__ == "__main__":
    main()