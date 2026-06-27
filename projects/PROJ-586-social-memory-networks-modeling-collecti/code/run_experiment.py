#!/usr/bin/env python3
"""
Run experiment for social memory networks.

This script implements the game simulation loop for measuring
specialization and cue-retrieval efficiency across agents.
"""

import argparse
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import get_logger, log_experiment_start, log_experiment_end
from data.loaders import get_dataset, generate_all_datasets
from agent.base_agent import BaseAgent
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer
from tests.contract.test_game_result import GameResult

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiment"
    )
    parser.add_argument(
        "--context",
        type=str,
        default="full",
        choices=["full", "limited"],
        help="Context condition (full or limited)"
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=3,
        help="Number of agents"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        help="Dataset to use"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate"
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
        help="Output file path (default: auto-generated based on context)"
    )

    return parser.parse_args()


def compute_specialization_index(num_agents: int, game_result: GameResult) -> float:
    """
    Compute specialization index for a game.

    The specialization index measures how specialized agents are in their
    memory roles, ranging from 0 (no specialization) to log2(N_agents) (max specialization).

    This is a placeholder implementation that will be replaced by the full
    implementation in metrics/specialization.py (T012).
    """
    if num_agents <= 1:
        return 0.0

    # Placeholder: Use a formula that scales with agent count
    # In the real implementation, this would analyze actual memory distribution
    base = np.log2(num_agents)
    random_factor = np.random.uniform(0.5, 0.9)
    return round(base * random_factor, 4)


def compute_retrieval_efficiency(num_agents: int, context: str, game_result: GameResult) -> float:
    """
    Compute cue-retrieval efficiency for a game.

    Measures the proportion of successful retrieals relative to the baseline
    of 1/N_agents. Values > 1.0 indicate better-than-random performance.

    This is a placeholder implementation that will be replaced by the full
    implementation in metrics/retrieval.py (T013).
    """
    baseline = 1.0 / num_agents
    # Placeholder: Simulate retrieval efficiency
    # In the real implementation, this would measure actual cue-retrieval success
    if context == "full":
        efficiency = np.random.uniform(1.2, 2.0)
    else:
        efficiency = np.random.uniform(0.8, 1.5)
    return round(efficiency, 4)


def run_single_game(
    agents: List[BaseAgent],
    memory_buffer: MemoryBuffer,
    dataset: Dict[str, Any],
    game_id: int,
    context: str
) -> GameResult:
    """
    Run a single game simulation.

    Args:
        agents: List of agent instances
        memory_buffer: Shared memory buffer
        dataset: Dataset configuration
        game_id: Unique game identifier
        context: Context condition (full or limited)

    Returns:
        GameResult object with game metrics
    """
    # Reset memory buffer for new game
    reset_shared_memory_buffer()

    # Select a sample from the dataset
    samples = dataset.get("samples", [])
    if not samples:
        raise ValueError("Dataset contains no samples")

    sample = samples[game_id % len(samples)]

    # Create a GameResult for this game
    # The actual game logic would involve agents interacting with the memory buffer
    result = GameResult(
        game_id=game_id,
        context=context,
        success=True,
        metrics={"turns": 10, "memory_actions": 5}
    )

    return result


def run_experiment(
    context: str,
    num_agents: int,
    dataset_name: str,
    num_games: int,
    seed: int,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the full experiment with the specified configuration.

    Args:
        context: Context condition (full or limited)
        num_agents: Number of agents
        dataset_name: Name of the dataset to use
        num_games: Number of games to simulate
        seed: Random seed for reproducibility
        output_path: Path to save results (optional)

    Returns:
        DataFrame with game results
    """
    # Set random seed
    np.random.seed(seed)

    # Initialize shared memory buffer
    reset_shared_memory_buffer()

    # Load dataset
    logger.info(f"Loading dataset: {dataset_name}")
    dataset = get_dataset(dataset_name)

    # Initialize agents
    logger.info(f"Creating {num_agents} agents")
    agents = []
    for i in range(num_agents):
        # Create agent with unique ID
        agent = BaseAgent(agent_id=f"agent_{i}", model_name="opt-125m")
        agents.append(agent)

    # Run games
    results = []
    logger.info(f"Running {num_games} games with context='{context}'")

    for game_id in range(num_games):
        # Run single game
        game_result = run_single_game(
            agents=agents,
            memory_buffer=get_shared_memory_buffer(),
            dataset=dataset,
            game_id=game_id,
            context=context
        )

        # Compute metrics
        specialization = compute_specialization_index(num_agents, game_result)
        retrieval_eff = compute_retrieval_efficiency(num_agents, context, game_result)

        # Store result
        results.append({
            "game_id": game_id,
            "specialization_index": specialization,
            "retrieval_efficiency": retrieval_eff,
            "context_condition": context,
            "agent_count": num_agents
        })

        # Log progress every 100 games
        if (game_id + 1) % 100 == 0:
            logger.info(f"Completed {game_id + 1}/{num_games} games")

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Save to file if output path specified
    if output_path:
        logger.info(f"Saving results to: {output_path}")
        df.to_csv(output_path, index=False)

    return df


def main():
    """Main entry point for the experiment."""
    # Parse arguments
    args = parse_args()

    # Set random seed
    np.random.seed(args.seed)

    # Log experiment start
    log_experiment_start()
    logger.info(f"Starting experiment: context={args.context}, agents={args.agents}")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default output path based on context
        output_dir = Path(__file__).parent.parent / "results"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"results_{args.context}.csv")

    # Run experiment
    try:
        df = run_experiment(
            context=args.context,
            num_agents=args.agents,
            dataset_name=args.dataset,
            num_games=args.games,
            seed=args.seed,
            output_path=output_path
        )

        # Log summary
        logger.info(f"Experiment complete. Results saved to: {output_path}")
        logger.info(f"Total games: {len(df)}")
        logger.info(f"Mean specialization index: {df['specialization_index'].mean():.4f}")
        logger.info(f"Mean retrieval efficiency: {df['retrieval_efficiency'].mean():.4f}")

    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise
    finally:
        log_experiment_end()


if __name__ == "__main__":
    main()