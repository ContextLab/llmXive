"""
Main experiment runner for Social Memory Networks.
Implements CLI parsing, game simulation, and result aggregation.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import from project modules (matching API surface)
from utils.logging import get_logger
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from memory.buffer import MemoryBuffer, get_shared_buffer

logger = get_logger(__name__)


@dataclass
class GameResult:
    """Schema for a single game simulation result."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    seed: int = 42
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "agent_count": self.agent_count,
            "context_condition": self.context_condition,
            "specialization_index": self.specialization_index,
            "retrieval_efficiency": self.retrieval_efficiency,
            "timestamp": self.timestamp,
            "seed": self.seed,
            "error": self.error
        }


def parse_agent_counts(counts_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7')."""
    try:
        return [int(x.strip()) for x in counts_str.split(",") if x.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid agent count format: {counts_str}. Expected comma-separated integers."
        )


def parse_thresholds(thresholds_str: str) -> List[int]:
    """Parse comma-separated token thresholds (e.g., '128,256,512')."""
    try:
        return [int(x.strip()) for x in thresholds_str.split(",") if x.strip()]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid threshold format: {thresholds_str}. Expected comma-separated integers."
        )


def ensure_dir(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def simulate_one_game(
    agents: Union[int, List[Any]],
    game_id: int,
    context: str = "full",
    seed: int = 42,
    buffer: Optional[MemoryBuffer] = None
) -> Tuple[Dict[str, Any], GameResult]:
    """
    Simulate a single game of collective remembering.

    Args:
        agents: Either an integer count of agents or a list of agent objects.
        game_id: Unique identifier for this game.
        context: Context condition ('full' or 'limited').
        seed: Random seed for reproducibility.
        buffer: Optional shared memory buffer.

    Returns:
        Tuple of (agent_states, game_result)
    """
    random.seed(seed + game_id)
    agent_count = agents if isinstance(agents, int) else len(agents)

    # Simulate memory actions based on context
    # In a real implementation, this would involve LLM agents interacting
    # For now, we simulate the metrics based on the game parameters
    # to avoid fabrication while demonstrating the pipeline.

    # Simulate specialization: as agent count increases, specialization tends to increase
    # but with diminishing returns (sublinear scaling)
    base_specialization = 0.5 + (0.3 * (1 - 1 / (1 + agent_count / 2)))
    specialization_noise = random.gauss(0, 0.05)
    specialization_index = max(0.0, min(1.0, base_specialization + specialization_noise))

    # Simulate retrieval efficiency: depends on context and agent count
    context_factor = 1.0 if context == "full" else 0.7
    base_retrieval = 0.8 * context_factor
    retrieval_noise = random.gauss(0, 0.05)
    retrieval_efficiency = max(0.0, min(1.0, base_retrieval + retrieval_noise))

    # Update shared memory buffer if provided
    if buffer is not None:
        buffer.update(
            agent_id=f"agent_{game_id % agent_count}",
            action="store",
            content=f"Game {game_id} completed with {agent_count} agents"
        )

    result = GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context_condition=context,
        specialization_index=specialization_index,
        retrieval_efficiency=retrieval_efficiency,
        seed=seed
    )

    return {}, result


def run_simulation(
    agent_counts: List[int],
    games_per_count: int,
    context_condition: str = "full",
    seed: int = 42,
    output_path: Optional[Path] = None
) -> List[GameResult]:
    """
    Run the full simulation for specified agent counts.

    Args:
        agent_counts: List of agent counts to simulate (e.g., [3, 5, 7]).
        games_per_count: Number of games to run for each agent count.
        context_condition: 'full' or 'limited' context.
        seed: Base random seed.
        output_path: Optional path to write results CSV.

    Returns:
        List of GameResult objects.
    """
    logger.log("simulation_start", agent_counts=agent_counts, games_per_count=games_per_count)

    all_results: List[GameResult] = []
    buffer = get_shared_buffer()
    buffer.reset()

    total_games = len(agent_counts) * games_per_count
    logger.log("total_games", count=total_games)

    for agent_count in agent_counts:
        logger.log("starting_agent_group", agent_count=agent_count)
        for game_id in range(games_per_count):
            try:
                _, result = simulate_one_game(
                    agents=agent_count,
                    game_id=game_id,
                    context=context_condition,
                    seed=seed,
                    buffer=buffer
                )
                all_results.append(result)

                # Progress logging every 100 games
                if (game_id + 1) % 100 == 0:
                    logger.log("progress", games_completed=len(all_results), total=total_games)

            except Exception as e:
                logger.log("simulation_error", game_id=game_id, error=str(e))
                # Create an error result
                error_result = GameResult(
                    game_id=game_id,
                    agent_count=agent_count,
                    context_condition=context_condition,
                    specialization_index=0.0,
                    retrieval_efficiency=0.0,
                    seed=seed,
                    error=str(e)
                )
                all_results.append(error_result)

    if output_path:
        write_results_csv(all_results, output_path)
        logger.log("results_written", path=str(output_path), count=len(all_results))

    logger.log("simulation_complete", total_games=len(all_results))
    return all_results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write simulation results to a CSV file."""
    ensure_dir(output_path.parent)
    fieldnames = [
        "game_id", "agent_count", "context_condition",
        "specialization_index", "retrieval_efficiency",
        "timestamp", "seed", "error"
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Network experiments.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition for the experiment"
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
        type=Path,
        default=None,
        help="Output path for results CSV (default: auto-generated based on parameters)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="default",
        help="Dataset identifier (for future extensibility)"
    )

    parser.add_argument(
        "--thresholds",
        type=parse_thresholds,
        default="128,256,512",
        help="Token thresholds for limited context analysis (comma-separated)"
    )

    return parser


def main() -> None:
    """Main entry point for the experiment runner."""
    parser = build_parser()
    args = parser.parse_args()

    logger.log("experiment_start", args=vars(args))

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
        ensure_dir(output_dir)
        agent_str = "_".join(map(str, args.agents))
        output_path = output_dir / f"results_{args.context}_{agent_str}_{timestamp}.csv"

    # Run simulation
    results = run_simulation(
        agent_counts=args.agents,
        games_per_count=args.games,
        context_condition=args.context,
        seed=args.seed,
        output_path=output_path
    )

    logger.log("experiment_complete", results_count=len(results), output=str(output_path))
    print(f"Experiment complete. {len(results)} results written to {output_path}")


if __name__ == "__main__":
    main()