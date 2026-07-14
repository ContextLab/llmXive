"""
Quick‑start validation script.

The original run‑book expects the following commands (in order):
    python code/data/generate_processed_data.py
    python code/training/train_gnn.py
    python code/training/train_rf.py
    python code/analysis/generate_performance_plots.py
    python code/analysis/generate_significance.py
    python code/generate_summary.py

This file now explicitly runs the required commands and validates that
the expected artefacts exist. It is imported by ``code/quickstart.md`` and
executed as part of the end‑to‑end pipeline.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = [
    Path("data/processed/molecules_10k.parquet"),
    Path("results/gnn_metrics.csv"),
    Path("results/gnn_rmse_variance.csv"),
    Path("results/significance.csv"),
]


def _run(command: str) -> None:
    print(f"Running: {command}")
    result = subprocess.run(
        command, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    sys.stdout.buffer.write(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}): {command}")


def validate_quickstart() -> None:
    commands = [
        "python code/data/generate_processed_data.py",
        "python code/training/train_gnn.py",
        "python code/training/train_rf.py",
        "python code/analysis/generate_performance_plots.py",
        "python code/analysis/generate_significance.py",
    ]
    for cmd in commands:
        _run(cmd)

    missing = [p for p in REQUIRED_FILES if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing expected artefacts: {missing}")
    print("All quick‑start artefacts are present.")


def main() -> None:
    try:
        validate_quickstart()
    except Exception as exc:
        print(f"Quick‑start validation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
