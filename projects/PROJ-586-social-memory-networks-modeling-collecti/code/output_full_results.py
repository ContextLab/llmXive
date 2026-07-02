"""Output full results to CSV file."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Dict
from generate_full_results import simulate_one_game
from utils.logging import get_logger


def main():
    """Generate results_full.csv with game metrics."""
    logger = get_logger(__name__)

    # Ensure output directory exists
    output_dir = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "results_full.csv"

    # Simulation parameters (from spec: 1000 games per condition)
    num_games = 1000
    agent_counts = [5]  # US-1 baseline: 5 agents
    context_condition = "full"

    results: List[Dict] = []

    # Run simulations
    for game_id in range(num_games):
        for agent_count in agent_counts:
            try:
                spec_idx, ret_eff = simulate_one_game(
                    agent_count=agent_count,
                    game_id=game_id,
                    context=context_condition
                )
                results.append({
                    "game_id": game_id,
                    "specialization_index": spec_idx,
                    "retrieval_efficiency": ret_eff,
                    "context_condition": context_condition,
                    "agent_count": agent_count,
                })
            except Exception as e:
                logger.error(f"Error in game {game_id}: {e}")
                continue

    # Write results to CSV
    if results:
        fieldnames = [
            "game_id",
            "specialization_index",
            "retrieval_efficiency",
            "context_condition",
            "agent_count",
        ]
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Results written to {output_file}")
        print(f"Results written to {output_file}")
    else:
        logger.error("No results generated")
        print("ERROR: No results generated", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()