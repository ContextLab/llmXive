"""CLI entry‑point for running the full‑context experiment and writing results."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Tuple

from generate_full_results import simulate_one_game
from utils.logging import get_logger


def parse_agent_counts(arg: str) -> List[int]:
    """Parse a comma‑separated list of agent counts, e.g. ``3,5,7``."""
    try:
        return [int(x.strip()) for x in arg.split(",") if x.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid agent count list: {arg}") from exc


def ensure_dir(path: Path) -> None:
    """Create the directory hierarchy if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_results_csv(
    results: List[Tuple[int, float, float, str, int]],
    output_path: Path,
) -> None:
    """
    Write a list of result tuples to ``results_full.csv``.

    Each tuple is expected to be:
        (game_id, specialization_index, retrieval_efficiency, context_condition, agent_count)
    """
    header = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in results:
            writer.writerow(row)


def run_simulation(
    agent_count: int,
    games: int,
    context: str,
    seed: int = 42,
) -> List[Tuple[int, float, float, str, int]]:
    """
    Run ``games`` simulations for a given ``agent_count`` and ``context``.

    Returns a list of result rows ready for CSV output.
    """
    logger = get_logger(__name__)
    logger.info("Starting simulation", agent_count=agent_count, games=games, context=context, seed=seed)

    results: List[Tuple[int, float, float, str, int]] = []
    for game_id in range(1, games + 1):
        spec_idx, ret_eff = simulate_one_game(agent_count, game_id, context)
        results.append((game_id, spec_idx, ret_eff, context, agent_count))
    logger.info("Simulation complete", total_games=games)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run full‑context social memory experiment")
    parser.add_argument("--agents", type=parse_agent_counts, required=True, help="Comma‑separated list of agent counts")
    parser.add_argument("--games", type=int, default=1000, help="Number of games per agent count")
    parser.add_argument("--context", choices=["full", "limited"], default="full", help="Context condition")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory where results CSV will be written",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ensure_dir(args.output_dir)
    output_file = args.output_dir / "results_full.csv"

    all_results: List[Tuple[int, float, float, str, int]] = []
    for count in args.agents:
        all_results.extend(run_simulation(count, args.games, args.context, args.seed))

    write_results_csv(all_results, output_file)
    get_logger().info("Results written", path=str(output_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
