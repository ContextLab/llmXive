"""
Scaling Experiment Runner for User Story 3.
Runs 800 games per configuration for agent counts 3, 5, 7.
Outputs data/scaling_results.csv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List

import pandas as pd

from utils.logging import get_logger
from run_experiment import simulate_one_game, GameResult

logger = get_logger(__name__)

AGENT_COUNTS = [3, 5, 7]
GAMES_PER_COUNT = 800
CONTEXT = "full"
OUTPUT_PATH = Path("data/scaling_results.csv")


def ensure_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def run_simulations_for_count(agent_count: int, games: int, context: str) -> List[GameResult]:
    results = []
    for i in range(games):
        game_id = f"scale_{agent_count}_{i}"
        res = simulate_one_game(agent_count, game_id, context)
        results.append(res)
    return results


def write_csv(results: List[GameResult], path: Path):
    ensure_dir(path)
    fieldnames = ["agent_count", "specialization_index", "retrieval_efficiency", "context_condition", "game_id"]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                "agent_count": r.agent_count,
                "specialization_index": r.specialization_index,
                "retrieval_efficiency": r.retrieval_efficiency,
                "context_condition": r.context,
                "game_id": r.game_id
            }
            writer.writerow(row)


def build_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Run scaling experiments.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--games", type=int, default=GAMES_PER_COUNT)
    parser.add_argument("--counts", type=str, default="3,5,7")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    counts = [int(x) for x in args.counts.split(",")]
    all_results = []

    for count in counts:
        logger.info(f"Running {args.games} games for agent count {count}...")
        results = run_simulations_for_count(count, args.games, CONTEXT)
        all_results.extend(results)

    write_csv(all_results, args.output)
    logger.info(f"Scaling data written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
