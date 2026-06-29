from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Set

# Must match the steps used by run_dummy_log
EXPECTED_STEPS: List[str] = [
    "ingest_transcripts",
    "detect_markers",
    "compute_scores",
    "extract_metrics",
    "impute_confounders",
    "merge_datasets",
    "run_regression",
    "validation",
]

def compute_log_completeness(log_dir: Path) -> float:
    """
    Compute completeness as the proportion of ``EXPECTED_STEPS`` that appear
    in any ``*.log`` file inside *log_dir*.
    """
    present_steps: Set[str] = set()
    for log_file in log_dir.glob("*.log"):
        with log_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    step = entry.get("step")
                    if isinstance(step, str):
                        present_steps.add(step)
                except json.JSONDecodeError:
                    # Skip malformed lines – they do not contribute to completeness
                    continue
    if not EXPECTED_STEPS:
        return 1.0
    completeness = len(present_steps.intersection(EXPECTED_STEPS)) / len(EXPECTED_STEPS)
    return completeness

def aggregate_completeness(completeness: float) -> dict:
    """
    Wrap the completeness value in a dict ready for JSON serialisation.
    """
    return {"completeness": completeness}

def write_metric_file(metric: dict, output_path: Path) -> None:
    """
    Write *metric* to *output_path* as pretty‑printed JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metric, f, indent=2)

def main(log_dir: Path, output_path: Path) -> None:
    """
    CLI entry point used by the unit test.

    Parameters
    ----------
    log_dir: Path
        Directory containing log files.
    output_path: Path
        Destination for the JSON metric file.
    """
    completeness = compute_log_completeness(log_dir)
    metric = aggregate_completeness(completeness)
    write_metric_file(metric, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute logging completeness metric.")
    parser.add_argument("--log_dir", type=Path, required=True, help="Directory with log files.")
    parser.add_argument(
        "--output_path", type=Path, required=True, help="Path for the metric JSON file."
    )
    args = parser.parse_args()
    main(args.log_dir, args.output_path)