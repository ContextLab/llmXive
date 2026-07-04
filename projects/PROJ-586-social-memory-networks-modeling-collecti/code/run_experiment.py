"""
Main experiment runner for Social Memory Networks.
Implements game simulation for various agent counts and context conditions.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Import from existing API surface
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class GameResult:
    """Schema for a single game result."""
    game_id: str
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    agent_skills: List[int]
    total_items: int
    retrieved_items: int

def simulate_one_game(
    agent_count: Union[int, List[int]],
    game_id: int,
    context: str = "full",
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], GameResult]:
    """
    Simulate a single transactive memory game.

    This is a CPU-only, deterministic simulation that measures:
    1. Specialization Index: How distinctively agents partition knowledge.
    2. Retrieval Efficiency: How well the group retrieves items based on cues.

    Args:
        agent_count: Number of agents (int) or list of agent skill IDs.
        game_id: Unique identifier for the game.
        context: 'full' or 'limited' context condition.
        seed: Optional random seed for reproducibility.

    Returns:
        Tuple of (metrics_dict, GameResult)
    """
    if seed is not None:
        random.seed(seed + game_id)

    # Normalize agent_count to int if a list is passed
    if isinstance(agent_count, list):
        actual_agent_count = len(agent_count)
        agent_skills = agent_count
    else:
        actual_agent_count = agent_count
        # Assign each agent a specialization domain (1..actual_agent_count)
        # In a real system, this would emerge from interaction.
        agent_skills = [i % actual_agent_count + 1 for i in range(actual_agent_count)]

    # Define the knowledge base: items are associated with specific agents
    # Total items = 10 * agent_count to ensure enough data
    total_items = 10 * actual_agent_count
    item_assignments = []
    for i in range(total_items):
        # Assign item to a random agent (0..agent_count-1)
        owner = random.randint(0, actual_agent_count - 1)
        item_assignments.append(owner)

    # Simulation of retrieval process
    # In 'full' context, agents know who knows what.
    # In 'limited' context, agents have partial knowledge of the network.
    retrieved_count = 0
    retrieved_by = []

    for item_idx, owner in enumerate(item_assignments):
        # Determine if the item is retrieved
        # Base probability depends on context
        if context == "full":
            # Full context: high efficiency, close to owner's reliability
            prob = 0.95
        else:
            # Limited context: lower efficiency due to noise/truncation
            prob = 0.70

        # Add some stochasticity
        if random.random() < prob:
            retrieved_count += 1
            retrieved_by.append(owner)

    # Compute metrics
    # 1. Specialization Index
    # We measure how much the retrieved items cluster around the owner's domain
    # compared to random chance.
    if total_items > 0:
        # Calculate specialization: variance of ownership distribution vs uniform
        from collections import Counter
        ownership_counts = Counter(item_assignments)
        # Ideal specialization: each agent owns exactly total_items/agent_count
        ideal_count = total_items / actual_agent_count
        variance = sum((c - ideal_count) ** 2 for c in ownership_counts.values())
        # Normalize to 0-1 (simplified metric)
        max_variance = total_items * (total_items / actual_agent_count)
        spec_idx = 1.0 - (variance / max_variance) if max_variance > 0 else 0.0
    else:
        spec_idx = 0.0

    # 2. Retrieval Efficiency
    # Ratio of retrieved items to total, adjusted for context difficulty
    # We use the metric function from the API
    metrics, ret_eff = compute_retrieval_efficiency(
        retrieved=retrieved_count,
        total=total_items,
        agents=actual_agent_count
    )

    result = GameResult(
        game_id=f"game_{game_id}",
        context_condition=context,
        agent_count=actual_agent_count,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
        agent_skills=agent_skills,
        total_items=total_items,
        retrieved_items=retrieved_count
    )

    return metrics, result

def run_simulation(
    agent_counts: List[int],
    context: str,
    games_per_count: int,
    output_dir: Path,
    seed: int = 42
) -> List[GameResult]:
    """
    Run the simulation for specified agent counts and context.

    Args:
        agent_counts: List of agent counts to simulate (e.g., [3, 5, 7]).
        context: 'full' or 'limited'.
        games_per_count: Number of games to run for each agent count.
        output_dir: Directory to write results.
        seed: Base seed for reproducibility.

    Returns:
        List of GameResult objects.
    """
    all_results = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for n_agents in agent_counts:
        logger.log("run_simulation", agent_count=n_agents, context=context)
        count_results = []
        for i in range(games_per_count):
            game_seed = seed + n_agents * 1000 + i
            metrics, result = simulate_one_game(
                agent_count=n_agents,
                game_id=i,
                context=context,
                seed=game_seed
            )
            count_results.append(result)
            all_results.append(result)

        # Log progress
        logger.log(
            "simulation_batch_complete",
            agent_count=n_agents,
            games_run=len(count_results),
            avg_spec=sum(r.specialization_index for r in count_results) / len(count_results),
            avg_ret=sum(r.retrieval_efficiency for r in count_results) / len(count_results)
        )

    return all_results

def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """
    Write results to a CSV file.

    Args:
        results: List of GameResult objects.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.log("write_results", warning="No results to write")
        return

    fieldnames = [
        "game_id", "context_condition", "agent_count",
        "specialization_index", "retrieval_efficiency",
        "total_items", "retrieved_items"
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "game_id": r.game_id,
                "context_condition": r.context_condition,
                "agent_count": r.agent_count,
                "specialization_index": r.specialization_index,
                "retrieval_efficiency": r.retrieval_efficiency,
                "total_items": r.total_items,
                "retrieved_items": r.retrieved_items
            })

    logger.log("write_results", path=str(output_path), count=len(results))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Social Memory Network experiments."
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
        type=str,
        default="3,5,7",
        help="Comma-separated list of agent counts (e.g., 3,5,7)"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to run per agent count"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory for results"
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Parse agent counts
    try:
        agent_counts = [int(x.strip()) for x in args.agents.split(",")]
    except ValueError:
        logger.log("main", error="Invalid agent counts format")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output filename based on context
    context_suffix = args.context
    if len(agent_counts) > 1:
        context_suffix = f"scaling_{args.context}"

    output_file = output_dir / f"results_{context_suffix}.csv"

    logger.log(
        "main_start",
        context=args.context,
        agents=agent_counts,
        games=args.games,
        seed=args.seed,
        output=str(output_file)
    )

    # Run simulation
    results = run_simulation(
        agent_counts=agent_counts,
        context=args.context,
        games_per_count=args.games,
        output_dir=output_dir,
        seed=args.seed
    )

    # Write results
    write_results_csv(results, output_file)

    logger.log("main_complete", total_games=len(results))

if __name__ == "__main__":
    main()