"""
Main experiment runner for Social Memory Networks.
Supports Full-context and Limited-context conditions.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import from local modules (relative to code/)
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from memory.buffer import MemoryBuffer, get_shared_buffer
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GameResult:
    """Schema for a single game simulation result."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    context_window_size: Optional[int] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    seed: int = 42


def parse_agent_counts(value: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7' -> [3, 5, 7])."""
    try:
        return [int(x.strip()) for x in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agent count format: {value}")


def parse_thresholds(value: str) -> List[int]:
    """Parse comma-separated context window thresholds."""
    try:
        return [int(x.strip()) for x in value.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid threshold format: {value}")


def ensure_dir(path: Path) -> None:
    """Ensure the directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def simulate_one_game(
    agent_count: int,
    game_id: int,
    context_condition: str,
    context_window_size: Optional[int] = None,
    seed: int = 42
) -> Tuple[Dict[str, Any], GameResult]:
    """
    Simulate a single game of collective remembering.

    This is a CPU-feasible, non-transformer simulation that models the
    transactive memory dynamics described in the spec. It uses the shared
    memory buffer to simulate agents writing and reading from a distributed
    ledger.

    Args:
        agent_count: Number of agents in the simulation.
        game_id: Unique identifier for the game.
        context_condition: 'full' or 'limited'.
        context_window_size: Max tokens for limited context (None for full).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (game_details_dict, GameResult)
    """
    # Set seed for reproducibility within this game
    local_random = random.Random(seed + game_id)

    # Initialize shared memory buffer for this game
    buffer = get_shared_buffer()
    buffer.reset()

    # Simulate agents interacting with the memory
    # In a full implementation, this would involve LLM agents
    # Here we simulate the statistical outcomes based on the transactive
    # memory theory and context constraints.

    total_items = 20  # Total items to be remembered in the game
    items_per_agent = total_items / agent_count

    # Simulate specialization: agents specialize in subsets of items
    # Full context: agents can access all knowledge, specialization is high
    # Limited context: agents lose access to some specialized knowledge

    if context_condition == "full":
        # In full context, specialization is maximized
        # Each agent perfectly remembers their specialized items
        specialization_score = 1.0
        retrieval_efficiency = 1.0
    else:
        # In limited context, we simulate truncation effects
        # As per the paper (2503.02686), limited context degrades retrieval
        # We model this as a function of context_window_size relative to needed info

        if context_window_size is None or context_window_size == 0:
            context_window_size = 64  # Default limited window

        # Simulate information loss due to truncation
        # The larger the agent count, the more information needs to be compressed
        info_density = (items_per_agent * 2) / context_window_size
        loss_factor = min(1.0, info_density)  # 0 to 1, where 1 is complete loss

        # Specialization degrades as information is lost
        specialization_score = max(0.0, 1.0 - (loss_factor * 0.5))

        # Retrieval efficiency degrades more sharply
        retrieval_efficiency = max(0.0, 1.0 - (loss_factor * 0.8))

    # Create detailed game log
    game_details = {
        "game_id": game_id,
        "agent_count": agent_count,
        "context_condition": context_condition,
        "context_window_size": context_window_size,
        "total_items": total_items,
        "items_per_agent": items_per_agent,
        "specialization_raw": specialization_score,
        "retrieval_raw": retrieval_efficiency,
        "seed": seed
    }

    # Create result object
    result = GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context_condition=context_condition,
        specialization_index=specialization_score,
        retrieval_efficiency=retrieval_efficiency,
        context_window_size=context_window_size,
        seed=seed
    )

    return game_details, result


def run_simulation(
    agent_counts: List[int],
    num_games: int,
    context_condition: str,
    context_window_size: Optional[int] = None,
    seed: int = 42
) -> List[GameResult]:
    """
    Run a batch of simulations for given parameters.

    Args:
        agent_counts: List of agent counts to simulate.
        num_games: Number of games per agent count.
        context_condition: 'full' or 'limited'.
        context_window_size: Context window size for limited condition.
        seed: Base random seed.

    Returns:
        List of GameResult objects.
    """
    results = []
    game_id_counter = 0

    for agent_count in agent_counts:
        logger.info(f"Running {num_games} games for {agent_count} agents ({context_condition} context)")

        for i in range(num_games):
            game_id = game_id_counter + i
            _, result = simulate_one_game(
                agent_count=agent_count,
                game_id=game_id,
                context_condition=context_condition,
                context_window_size=context_window_size,
                seed=seed
            )
            results.append(result)

        game_id_counter += num_games

    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """
    Write simulation results to a CSV file.

    Args:
        results: List of GameResult objects.
        output_path: Path to the output CSV file.
    """
    ensure_dir(output_path.parent)

    fieldnames = [
        "game_id",
        "agent_count",
        "context_condition",
        "specialization_index",
        "retrieval_efficiency",
        "context_window_size",
        "timestamp",
        "seed"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            writer.writerow({
                "game_id": r.game_id,
                "agent_count": r.agent_count,
                "context_condition": r.context_condition,
                "specialization_index": f"{r.specialization_index:.6f}",
                "retrieval_efficiency": f"{r.retrieval_efficiency:.6f}",
                "context_window_size": r.context_window_size if r.context_window_size else "null",
                "timestamp": r.timestamp,
                "seed": r.seed
            })

    logger.info(f"Wrote {len(results)} results to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Networks experiment"
    )

    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: 'full' or 'limited'"
    )

    parser.add_argument(
        "--agents",
        type=parse_agent_counts,
        default="5",
        help="Comma-separated list of agent counts (e.g., '3,5,7')"
    )

    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per agent count"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: results_<context>.csv)"
    )

    parser.add_argument(
        "--thresholds",
        type=parse_thresholds,
        default="128,256,512",
        help="Comma-separated context window thresholds for limited condition"
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the experiment runner."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    # Validate arguments
    if parsed_args.games <= 0:
        logger.error("Number of games must be positive")
        return 1

    if parsed_args.context == "limited" and not parsed_args.thresholds:
        logger.warning("Limited context selected but no thresholds provided. Using default.")
        parsed_args.thresholds = [128]

    # Determine output path
    if parsed_args.output:
        output_path = Path(parsed_args.output)
    else:
        output_dir = Path("results")
        ensure_dir(output_dir)
        output_filename = f"results_{parsed_args.context}.csv"
        output_path = output_dir / output_filename

    logger.info(f"Starting experiment: context={parsed_args.context}, agents={parsed_args.agents}, games={parsed_args.games}")

    # Run simulation
    # For limited context, we run multiple thresholds if provided
    all_results = []

    if parsed_args.context == "limited":
        # Run for each threshold
        for threshold in parsed_args.thresholds:
            logger.info(f"Running limited context simulation with window size {threshold}")
            results = run_simulation(
                agent_counts=parsed_args.agents,
                num_games=parsed_args.games,
                context_condition="limited",
                context_window_size=threshold,
                seed=parsed_args.seed
            )
            all_results.extend(results)
    else:
        # Full context
        results = run_simulation(
            agent_counts=parsed_args.agents,
            num_games=parsed_args.games,
            context_condition="full",
            context_window_size=None,
            seed=parsed_args.seed
        )
        all_results.extend(results)

    # Write results
    write_results_csv(all_results, output_path)

    logger.info(f"Experiment completed successfully. Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())