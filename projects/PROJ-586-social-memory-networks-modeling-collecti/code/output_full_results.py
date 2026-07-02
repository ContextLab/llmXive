"""
Script to generate the full‑context experiment results for User Story 1.

The script runs 1 000 simulated games using the existing ``simulate_one_game``
helper (implemented in ``generate_full_results.py``) and writes a CSV file
``results_full.csv`` to the project's ``results`` directory.

The CSV columns are:
    - game_id
    - specialization_index
    - retrieval_efficiency
    - context_condition
    - agent_count

The implementation relies only on standard‑library modules and the public
API of the project, so it works on the CPU‑only CI environment.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Dict

# Import helpers from the existing module.  These are part of the public
# interface defined in ``code/generate_full_results.py``.
from generate_full_results import (
    ensure_dir,
    simulate_one_game,
    parse_agent_list,
)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
NUM_GAMES = 1000
AGENT_COUNTS = [3, 5, 7]          # Example agent counts used in the paper.
CONTEXT_CONDITION = "full"
OUTPUT_PATH = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results/"
    "results_full.csv"
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_simulation(agent_count: int) -> List[Dict[str, object]]:
    """
    Run ``NUM_GAMES`` simulations for a given ``agent_count`` and return a
    list of dictionaries ready to be written to CSV.
    """
    rows: List[Dict[str, object]] = []
    for game_id in range(1, NUM_GAMES + 1):
        # ``simulate_one_game`` is expected to return a tuple:
        #   (specialization_index, retrieval_efficiency)
        # The exact signature is defined in ``generate_full_results.py``.
        specialization_index, retrieval_efficiency = simulate_one_game(
            game_id=game_id,
            agent_count=agent_count,
            context=CONTEXT_CONDITION,
        )
        rows.append(
            {
                "game_id": game_id,
                "specialization_index": specialization_index,
                "retrieval_efficiency": retrieval_efficiency,
                "context_condition": CONTEXT_CONDITION,
                "agent_count": agent_count,
            }
        )
    return rows

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the experiment and write the CSV file.
    """
    # Ensure the target directory exists.
    ensure_dir(OUTPUT_PATH.parent)

    # Collect rows for each requested agent count.
    all_rows: List[Dict[str, object]] = []
    for count in AGENT_COUNTS:
        all_rows.extend(_run_simulation(count))

    # Write CSV.
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ Results written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
