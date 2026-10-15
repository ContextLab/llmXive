"""Run the LLM‑Xive static‑dynamic analysis pipeline.

This script provides a minimal ``--dry-run`` mode that sets up the
project‑wide directory structure, pins random seeds for reproducibility,
and creates a tiny CSV result file (≤ 10 rows) so that the quick‑start
command can be demonstrated end‑to‑end.

The full pipeline (data ingestion, graph extraction, feature
engineering, model training, etc.) will be implemented in later tasks.
"""
import argparse
import csv
import random
import sys
from pathlib import Path

import numpy as np
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Global reproducibility settings
# ----------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

log = get_logger(__name__)
log.info("Random seed set to %d", SEED)

def ensure_project_dirs() -> None:
    """Create all top‑level directories required by the pipeline."""
    # Directories that hold data and artefacts
    for dir_path in [
        paths.data(),
        paths.data("results"),
        paths.interim(),
        paths.features(),
        paths.models(),
        paths.reports(),
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Source code directories (they already exist in the repo,
    # but ``mkdir`` is safe if the repository layout is altered.)
    for src_dir in [
        paths.code("pipeline"),
        paths.code("cli"),
    ]:
        src_dir.mkdir(parents=True, exist_ok=True)

def write_sample_result(csv_path: Path) -> None:
    """Write a tiny CSV with dummy predictions.

    The file contains at most ten rows and the following columns:
    ``patch_id, true_label, predicted_label, predicted_prob``.
    """
    header = ["patch_id", "true_label", "predicted_label", "predicted_prob"]
    rows = [
        ["patch_001", "pass", "pass", "0.95"],
        ["patch_002", "fail", "fail", "0.92"],
        ["patch_003", "pass", "fail", "0.40"],
        ["patch_004", "fail", "pass", "0.55"],
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    log.info("Sample result written to %s", csv_path)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="LLM‑Xive static‑dynamic gap analysis pipeline (dry‑run mode)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create project directories and a tiny sample CSV result.",
    )
    args = parser.parse_args(argv)

    # Always ensure the directory skeleton exists – even without dry‑run.
    ensure_project_dirs()

    if args.dry_run:
        sample_path = paths.data("results", "sample_run.csv")
        write_sample_result(sample_path)
        print(f"Dry‑run completed. Sample result at: {sample_path}")
    else:
        # Placeholder for the full pipeline implementation.
        print("Full pipeline not yet implemented.", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
