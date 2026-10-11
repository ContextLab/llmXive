"""Merge fold metrics and statistical summary into a single report.

T023: Reads results/fold_metrics.json (from T019) and
results/stats_summary.json (from T022), merges them into one
comprehensive report, and saves it to data/outputs/metrics.json
(Constitution Principle IV: single source of truth).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure code/ is on the import path for sibling module imports.
CODE_ROOT = Path(__file__).resolve().parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from utils.logger import setup_logger

logger = setup_logger("merge")

PROJECT_ROOT = CODE_ROOT.parent
FOLD_METRICS_PATH = PROJECT_ROOT / "results" / "fold_metrics.json"
STATS_SUMMARY_PATH = PROJECT_ROOT / "results" / "stats_summary.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "outputs" / "metrics.json"


def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file, failing loudly if missing or invalid."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Run the upstream tasks (T019 training, T022 stats) first."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate_model_metrics(fold_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate fold-wise MAE/RMSE/R2 into mean and std per model."""
    summary: Dict[str, Any] = {}
    models = fold_metrics.get("models", fold_metrics)
    for model_name, folds in models.items():
        if not isinstance(folds, list):
            continue
        agg: Dict[str, Dict[str, float]] = {}
        for metric in ("mae", "rmse", "r2"):
            values: List[float] = [
                float(fold[metric]) for fold in folds if metric in fold
            ]
            if values:
                mean = sum(values) / len(values)
                var = (
                    sum((v - mean) ** 2 for v in values) / (len(values) - 1)
                    if len(values) > 1
                    else 0.0
                )
                agg[metric] = {
                    "mean": round(mean, 6),
                    "std": round(var ** 0.5, 6),
                    "n_folds": len(values),
                    "fold_values": [round(v, 6) for v in values],
                }
        summary[model_name] = agg
    return summary


def merge_reports(fold_metrics: Dict[str, Any], stats_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Merge the two artifacts into the comprehensive report."""
    report: Dict[str, Any] = {
        "fold_metrics": fold_metrics,
        "model_summary": aggregate_model_metrics(fold_metrics),
        "statistical_comparison": stats_summary,
    }
    return report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """Atomically save the merged report as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    tmp_path.replace(output_path)
    logger.info("Merged report saved to %s", output_path)


def main() -> None:
    """Main entry point for T023."""
    logger.info("Loading fold metrics from %s", FOLD_METRICS_PATH)
    fold_metrics = load_json(FOLD_METRICS_PATH)
    logger.info("Loading statistical summary from %s", STATS_SUMMARY_PATH)
    stats_summary = load_json(STATS_SUMMARY_PATH)

    report = merge_reports(fold_metrics, stats_summary)
    save_report(report, OUTPUT_PATH)
    logger.info("Merge complete.")


if __name__ == "__main__":
    main()