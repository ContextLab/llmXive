"""Generate the full‑context results CSV for User Story 1.

This script runs a lightweight simulation for a configurable number of
games, records the required metrics, and writes them to
``projects/PROJ-586-social-memory-networks-modeling-collecti/results/
results_full.csv``.

It relies on the existing ``generate_full_results`` module for the core
per‑game simulation logic.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import List

# Import the shared simulation helper
from generate_full_results import simulate_one_game, ensure_dir


DEFAULT_RESULTS_DIR = Path(
    "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
)
DEFAULT_OUTPUT_FILE = DEFAULT_RESULTS_DIR / "results_full.csv"


def parse_agent_list(arg: str) -> List[int]:
    """Parse a comma‑separated list of agent counts."""
    return [int(x) for x in arg.split(",") if x.strip()]


def write_results_csv(
    records: List[dict],
    output_path: Path = DEFAULT_OUTPUT_FILE,
) -> None:
    """Write a list of metric dictionaries to *output_path* as CSV."""
    ensure_dir(output_path.parent)
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            # Ensure all required keys exist; missing keys default to empty.
            row = {k: rec.get(k, "") for k in fieldnames}
            writer.writerow(row)


def run_simulation(
    agent_counts: List[int],
    num_games: int,
    context: str,
    seed: int = 42,
) -> List[dict]:
    """Run *num_games* simulations for each agent count in *agent_counts*."""
    random.seed(seed)
    results: List[dict] = []
    game_id = 0
    for agents in agent_counts:
        for _ in range(num_games):
            game_id += 1
            # ``simulate_one_game`` returns a dict with the required metrics.
            # It expects the number of agents and the context condition.
            metrics = simulate_one_game(agent_count=agents, context=context)
            # Enrich the record with identifiers required by the CSV schema.
            metrics.update(
                {
                    "game_id": game_id,
                    "context_condition": context,
                    "agent_count": agents,
                }
            )
            results.append(metrics)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate full‑context experiment results (US‑1)."
    )
    parser.add_argument(
        "--agents",
        type=parse_agent_list,
        required=True,
        help="Comma‑separated list of agent counts (e.g., '3,5,7').",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate per agent count.",
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition for the simulation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to write the CSV results file.",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    records = run_simulation(
        agent_counts=args.agents,
        num_games=args.games,
        context=args.context,
        seed=args.seed,
    )
    write_results_csv(records, output_path=args.output)
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()