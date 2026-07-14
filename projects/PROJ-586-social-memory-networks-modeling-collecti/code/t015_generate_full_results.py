"""
Task T015: Generate results_full.csv for User Story 1 (Full-context condition).

This script runs a simulation of the full-context condition for a specified
number of games, computes specialization and retrieval metrics, and outputs
the results to a CSV file.

It uses the real experiment runner logic from `run_experiment.py` but
specifically targets the "full" context condition.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project modules
from utils.logging import get_logger
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from run_experiment import GameConfig, simulate_one_game, load_and_verify_dataset
from data.loaders import enable_synthetic_fallback, disable_synthetic_fallback

logger = get_logger("T015_main")

@dataclass
class GameResultRow:
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int

def run_simulation(
    num_games: int,
    agent_count: int,
    context_condition: str = "full",
    seed: int = 42,
    output_path: Optional[Path] = None
) -> List[GameResultRow]:
    """
    Run the simulation for a specific number of games and agents.

    Args:
        num_games: Number of games to simulate.
        agent_count: Number of agents in the simulation.
        context_condition: "full" or "limited".
        seed: Random seed for reproducibility.
        output_path: Optional path to write results immediately.

    Returns:
        List of GameResultRow objects.
    """
    logger.log("run_simulation_start", num_games=num_games, agent_count=agent_count)

    # Set seed
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)

    # Enable synthetic fallback as per FR-011 if real data is missing
    enable_synthetic_fallback()


def run_simulation(num_games: int, num_agents: int, context_condition: str, seed: int) -> List[GameResult]:
    """Run the simulation for a specified number of games."""
    results = []

    # Prepare output directory if needed
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    for game_id in range(num_games):
        try:
            # Configure game
            config = GameConfig(
                num_agents=agent_count,
                context_condition=context_condition,
                dataset_name="hanabi", # Default to hanabi, fallback to synthetic
                seed=seed + game_id
            )

            # Run simulation for one game
            # simulate_one_game returns (spec_index, ret_eff, game_result_dict)
            # We need to handle the return value carefully based on run_experiment.py
            try:
                spec_idx, ret_eff, game_result = simulate_one_game(config, game_id)
            except Exception as e:
                # If simulation fails, log and skip or handle as needed
                logger.log("simulation_error", game_id=game_id, error=str(e))
                # Skip this game or record as NaN/None? Spec says "for [deferred] games"
                # We will skip failed games to maintain data integrity, but log them.
                continue

            # Create result row
            row = GameResultRow(
                game_id=game_id,
                specialization_index=spec_idx,
                retrieval_efficiency=ret_eff,
                context_condition=context_condition,
                agent_count=agent_count
            )
            results.append(row)

        except Exception as e:
            logger.log("game_loop_error", game_id=game_id, error=str(e))
            continue

    # Write to CSV if path provided
    if output_path and results:
        write_results_csv(results, output_path)

    disable_synthetic_fallback()
    logger.log("run_simulation_end", total_results=len(results))
    return results

def write_results_csv(results: List[GameResultRow], output_path: Path) -> None:
    """Write results to a CSV file."""
    logger.log("write_results_csv", path=str(output_path), count=len(results))

    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(asdict(row))

    logger.log("write_results_csv_success", path=str(output_path))

def main() -> None:
    parser = argparse.ArgumentParser(description="T015: Generate full context results")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to simulate")
    parser.add_argument("--agents", type=int, default=5, help="Number of agents")
    parser.add_argument("--output", type=str, default="projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv", help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    output_path = Path(args.output)

    # Run simulation
    results = run_simulation(
        num_games=args.games,
        agent_count=args.agents,
        context_condition="full",
        seed=args.seed,
        output_path=output_path
    )

    if not results:
        logger.log("no_results_generated", error="Simulation produced no valid results")
        sys.exit(1)

    print(f"Successfully generated {len(results)} results at {output_path}")

if __name__ == "__main__":
    main()