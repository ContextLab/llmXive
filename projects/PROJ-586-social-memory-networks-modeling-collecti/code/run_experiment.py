"""Command‑line entry point for running a single experiment configuration.

The script supports three modes controlled by the ``--context`` flag:

* ``full`` – agents see the entire conversation history.
* ``limited`` – agents see only the most recent *N* tokens (simulated via a
  truncation parameter; for the purposes of this pipeline the truncation
  is a no‑op but the flag is retained for API compatibility).
* ``scaling`` – invoked indirectly via ``--plot scaling`` together with a
  comma‑separated list of agent counts.

The heavy lifting (simulation of a single game) lives in
``code/generate_full_results.py``; this wrapper builds the appropriate
parameter lists, runs the required number of games, aggregates the metrics
and writes a CSV file under the project‑level ``results/`` directory.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List

from generate_full_results import (
    ensure_dir,
    parse_agent_list,
    simulate_one_game,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a social‑memory experiment.")
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        required=True,
        help="Context condition for the experiment.",
    )
    parser.add_argument(
        "--agents",
        type=str,
        required=True,
        help="Comma‑separated list of agent counts (e.g. '5' or '3,5,7').",
    )
    parser.add_argument(
        "--games",
        type=int,
        required=True,
        help="Number of games to simulate for each agent count.",
    )
    parser.add_argument(
        "--plot",
        choices=["scaling"],
        default=None,
        help="If set to 'scaling', generate the scaling plot after the runs.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory where result CSVs (and optional plots) are written.",
    )
    return parser


def write_results_csv(
    output_path: Path, rows: List[dict], fieldnames: List[str]
) -> None:
    """Write *rows* to *output_path* using the provided *fieldnames*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_simulation(
    context: str,
    agents: List[int],
    games: int,
    output_dir: Path,
    generate_plot: bool = False,
) -> None:
    """Run the simulation for each agent count and write CSV results."""
    for agent_count in agents:
        rows = []
        for game_id in range(1, games + 1):
            # ``simulate_one_game`` returns a tuple of metric dicts.
            spec_metrics, retrieval_metrics = simulate_one_game(
                game_id=game_id,
                agent_count=agent_count,
                context=context,
            )
            # Merge the two metric dicts and add bookkeeping fields.
            merged = {
                "game_id": game_id,
                "agent_count": agent_count,
                "context_condition": context,
                **spec_metrics.__dict__,
                **retrieval_metrics.__dict__,
            }
            rows.append(merged)

        # Determine CSV filename.
        suffix = "full" if context == "full" else "limited"
        csv_name = f"results_{suffix}_{agent_count}.csv"
        csv_path = output_dir / csv_name
        fieldnames = list(rows[0].keys())
        write_results_csv(csv_path, rows, fieldnames)

    if generate_plot:
        # The scaling plot generation script expects the CSVs to already exist.
        from analysis.scaling import generate_scaling_plot

        generate_scaling_plot(output_dir)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    agents = parse_agent_list(args.agents)
    output_dir = Path(args.output_dir)

    generate_plot = args.plot == "scaling"

    run_simulation(
        context=args.context,
        agents=agents,
        games=args.games,
        output_dir=output_dir,
        generate_plot=generate_plot,
    )


if __name__ == "__main__":
    main()
