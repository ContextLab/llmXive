"""Run scaling experiments for agent counts 3, 5, and 7.

This script executes a series of game simulations for each specified agent
count, records the specialization index and cue‑retrieval efficiency for
every game, aggregates the results, and produces a scaling plot with a
fitted power‑law curve.

The implementation relies exclusively on the project's existing
simulation utilities:

- ``parse_agent_list`` and ``simulate_one_game`` from
  ``code/generate_full_results.py`` – these create agents and run a single
  game, returning a dictionary that includes the required metrics.
- Metric computation functions from ``code/metrics`` are *not* called
  directly; ``simulate_one_game`` already returns the finished metrics.
- ``generate_scaling_plot`` from ``code/analysis/scaling.py`` – this fits a
  power‑law to the aggregated data and writes ``scaling_plot.pdf``.

The script writes per‑agent‑count CSV files under ``data/`` and a combined
CSV ``data/scaling_results.csv``.  The final plot is saved to
``projects/PROJ-586-social-memory-networks-modeling-collecti/results/
scaling_plot.pdf``.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List

import pandas as pd

# Local imports – these modules exist in the repository.
from generate_full_results import parse_agent_list, simulate_one_game
from analysis.scaling import generate_scaling_plot

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
AGENT_COUNTS: List[int] = [3, 5, 7]
GAMES_PER_CONFIG: int = 800
OUTPUT_DIR: Path = Path("data")
COMBINED_CSV: Path = OUTPUT_DIR / "scaling_results.csv"
PLOT_OUTPUT: Path = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_plot.pdf"
)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def ensure_dir(path: Path) -> None:
    """Create ``path`` if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def run_simulations_for_count(agent_count: int) -> pd.DataFrame:
    """Run ``GAMES_PER_CONFIG`` games for a given ``agent_count``.

    Returns a ``pandas.DataFrame`` with columns:
        - ``agent_count`` (int)
        - ``game_id`` (int)
        - ``specialization_index`` (float)
        - ``retrieval_efficiency`` (float)
    """
    # ``parse_agent_list`` expects a comma‑separated string of agent counts.
    # For a single count we simply pass the integer as a string.
    agents = parse_agent_list(str(agent_count))

    rows = []
    for game_id in range(GAMES_PER_CONFIG):
        # ``simulate_one_game`` returns a dict containing the metrics we need.
        # The exact keys are defined by the implementation in
        # ``generate_full_results.py``; we rely on the documented contract.
        result = simulate_one_game(agents, game_id)

        # Defensive programming – if a key is missing we raise a clear error.
        try:
            spec_idx = float(result["specialization_index"])
            retrieval = float(result["retrieval_efficiency"])
        except KeyError as exc:
            raise KeyError(
                f"simulate_one_game did not return expected metric: {exc}"
            ) from exc

        rows.append(
            {
                "agent_count": agent_count,
                "game_id": game_id,
                "specialization_index": spec_idx,
                "retrieval_efficiency": retrieval,
            }
        )

    df = pd.DataFrame(rows)
    return df

def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write ``df`` to ``path`` as CSV with a header."""
    ensure_dir(path.parent)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main(argv: List[str] | None = None) -> int:
    """Execute the scaling experiment pipeline.

    The function returns an exit code compatible with ``sys.exit``.
    """
    # ``argv`` is accepted for testability; when ``None`` we use ``sys.argv``.
    _ = argv  # currently unused – the script has no CLI options.

    ensure_dir(OUTPUT_DIR)

    # Collect per‑agent‑count DataFrames and write individual CSVs.
    all_dfs = []
    for count in AGENT_COUNTS:
        df = run_simulations_for_count(count)
        all_dfs.append(df)

        per_count_path = OUTPUT_DIR / f"scaling_results_{count}.csv"
        write_csv(df, per_count_path)

    # Concatenate all results and write the combined CSV.
    combined_df = pd.concat(all_dfs, ignore_index=True)
    write_csv(combined_df, COMBINED_CSV)

    # Generate the scaling plot (includes power‑law fitting).
    ensure_dir(PLOT_OUTPUT.parent)
    generate_scaling_plot(combined_df, output_path=PLOT_OUTPUT)

    return 0

if __name__ == "__main__":
    sys.exit(main())
