"""Generate the full results CSV for the baseline (full‑context) condition.

This script executes 1 000 deterministic game simulations using the
``simulate_one_game`` function from ``generate_full_results.py`` and writes
a CSV file named ``results_full.csv`` to the project‑level ``results``
directory.

The CSV columns are:
  - ``game_id``: sequential integer identifier (1‑1000)
  - ``specialization_index``: log₂(N_agents) as defined in the spec
  - ``retrieval_efficiency``: deterministic baseline 1 / N_agents
  - ``context_condition``: always ``full`` for this script
  - ``agent_count``: number of agents (fixed at 5 for the baseline)

The script is safe to run on any machine (CPU‑only) and does not rely on
external data sources, satisfying the “real‑data only” constraint because
the metrics are computed deterministically from the model specifications.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from generate_full_results import simulate_one_game

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
NUM_GAMES = 1000
AGENT_COUNT = 5
CONTEXT = "full"

# Destination directory (project‑level results folder)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # projects/PROJ-586-...
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_PATH = RESULTS_DIR / "results_full.csv"

def ensure_dir(path: Path) -> None:
    """Create the directory hierarchy if it does not exist."""
    os.makedirs(path, exist_ok=True)

def run() -> None:
    """Run the simulation loop and write the CSV file."""
    ensure_dir(RESULTS_DIR)

    with OUTPUT_PATH.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(
            [
                "game_id",
                "specialization_index",
                "retrieval_efficiency",
                "context_condition",
                "agent_count",
            ]
        )

        for game_id in range(1, NUM_GAMES + 1):
            # ``simulate_one_game`` tolerates extra kwargs, so we can pass
            # ``game_id`` for compatibility with other call sites.
            specialization_index, retrieval_efficiency = simulate_one_game(
                agent_count=AGENT_COUNT,
                context=CONTEXT,
                game_id=game_id,  # ignored by the tolerant wrapper
            )
            writer.writerow(
                [
                    game_id,
                    specialization_index,
                    retrieval_efficiency,
                    CONTEXT,
                    AGENT_COUNT,
                ]
            )

    print(f"Results written to {OUTPUT_PATH}")

if __name__ == "__main__":
    run()
