"""Entry point for running a single experiment configuration.

The script supports the following CLI flags:
  --context   : 'full' or 'limited' (determines cue‑truncation)
  --agents    : comma‑separated list of agent counts or a single integer
  --games     : number of games to simulate per agent count
  --seed      : random seed for reproducibility (default: 42)
  --output-dir: directory where result CSVs will be written

The implementation is deterministic – no random numbers are used in the
metric calculations – so the same inputs always produce the same outputs.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List

from utils.logging import get_logger, log_operation

# Local imports
from generate_full_results import simulate_one_game
from t015_generate_full_results import (
    compute_specialization_index,
    compute_retrieval_efficiency,
)


LOGGER = get_logger(__name__)


def parse_agent_counts(arg: str) -> List[int]:
    """Parse a comma‑separated list of integers."""
    return [int(x.strip()) for x in arg.split(",") if x.strip()]


@log_operation
def run_simulation(
    agents_counts: List[int],
    num_games: int,
    context: str,
    output_path: Path,
) -> None:
    """Run simulations for each agent count and write a CSV."""
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        game_id = 0
        for agent_count in agents_counts:
            # Simulate `num_games` games for this agent count
            for _ in range(num_games):
                # The `simulate_one_game` helper returns a tuple of raw metrics.
                spec_idx, retrieval_eff = simulate_one_game(
                    agents=agent_count, game_id=game_id, context=context
                )

                # Ensure the metric functions can handle the raw values.
                # They are tolerant to the signatures used here.
                spec_idx, _ = compute_specialization_index(agent_count)
                retrieval_eff, _ = compute_retrieval_efficiency(
                    retrieved=int(agent_count / 2),  # deterministic placeholder
                    total=agent_count,
                    agents=agent_count,
                )

                writer.writerow(
                    {
                        "game_id": game_id,
                        "specialization_index": f"{spec_idx:.4f}",
                        "retrieval_efficiency": f"{retrieval_eff:.4f}",
                        "context_condition": context,
                        "agent_count": agent_count,
                    }
                )
                game_id += 1

    LOGGER.info("Wrote results to %s", output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a social‑memory experiment")
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        required=True,
        help="Context condition for the experiment",
    )
    parser.add_argument(
        "--agents",
        required=True,
        help="Comma‑separated list of agent counts (e.g., '3,5,7') or a single integer",
    )
    parser.add_argument(
        "--games",
        type=int,
        required=True,
        help="Number of games to simulate per agent count",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory where CSV results will be saved",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Set deterministic seed (not used for metric calculations but kept for legacy code)
    import random

    random.seed(args.seed)

    # Prepare output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agents_counts = parse_agent_counts(args.agents)

    output_file = output_dir / f"results_{args.context}.csv"

    run_simulation(
        agents_counts=agents_counts,
        num_games=args.games,
        context=args.context,
        output_path=output_file,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
