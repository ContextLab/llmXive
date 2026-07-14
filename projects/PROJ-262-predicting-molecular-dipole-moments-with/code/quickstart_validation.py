"""
Quick‑start validation script.

The original quick‑start validation was not part of the run‑book, causing the
pipeline to miss required checks.  This script now executes the minimal
sequence of commands that must succeed for the research pipeline to be
considered complete:

1. Generate processed data (creates ``data/processed/molecules_10k.parquet``).
2. Train the GNN model (produces ``results/metrics.csv`` and checkpoint files).
3. Train the Random Forest baseline (produces its own metrics CSV).
4. Validate that all declared artefacts exist.

The script is invoked from ``quickstart.md`` (the run‑book) and will exit
with status 0 only if every step succeeds.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = [
    Path("data/processed/molecules_10k.parquet"),
    Path("results/metrics.csv"),
    Path("results/metrics_rf.csv"),
    Path("results/significance.csv"),
]

def run_command(command: list[str]) -> None:
    """Run a shell command, raising if it fails."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError(f"Command {' '.join(command)} failed with exit code {result.returncode}")

def main() -> None:
    # Step 1: generate processed data
    run_command([sys.executable, "code/data/generate_processed_data.py"])

    # Step 2: train GNN
    run_command([sys.executable, "code/training/train_gnn.py"])

    # Step 3: train Random Forest (already implemented elsewhere)
    run_command([sys.executable, "code/training/train_rf.py"])

    # Verify required artefacts
    missing = [str(p) for p in REQUIRED_FILES if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"The following required files are missing: {', '.join(missing)}")
    print("All quick‑start validation checks passed.")

if __name__ == "__main__":
    main()