"""Convenient wrapper script to generate the full‑context results CSV (T015)."""
from __future__ import annotations

import sys
from pathlib import Path

from run_experiment import main as run_experiment_main


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run() -> int:
    """
    Execute the experiment with the parameters required by T015:
    - full context
    - agent counts 3,5,7
    - 1000 games per agent count
    - output written to the project's results directory
    """
    args = [
        "--context",
        "full",
        "--agents",
        "3,5,7",
        "--games",
        "1000",
    ]
    return run_experiment_main(args)


if __name__ == "__main__":
    sys.exit(run())
