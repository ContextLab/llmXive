"""
Main experiment runner for social memory network simulations.
Supports full-context and limited-context conditions.
"""
import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging import setup_logger, get_logger
from utils.config import get_config
from data.loaders import DatasetLoader, get_dataset
from data.synthetic import generate_synthetic_games, SyntheticGameConfig
from agent.base_agent import BaseAgent, AgentConfig
from memory.buffer import MemoryBuffer, get_shared_memory_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from metrics.validator import validate_experiment_metrics

# Constants
DEFAULT_GAMES_FULL = 1000
DEFAULT_GAMES_LIM = 1000
DEFAULT_GAMES_SCALING = 800
RESULTS_DIR = PROJECT_ROOT / "results"

class GameResult:
    """Container for a single game's metrics."""
    def __init__(
        self,
        game_id: int,
        specialization_index: float,
        retrieval_efficiency: float,
        context_condition: str,
        agent_count: int,
        context_tokens: int = 0
    ):
        self.game_id = game_id
        self.specialization_index = specialization_index
        self.retrieval_efficiency = retrieval_efficiency
        self.context_condition = context_condition
        self.agent_count = agent_count
        self.context_tokens = context_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "specialization_index": self.specialization_index,
            "retrieval_efficiency": self.retrieval_efficiency,
            "context_condition": self.context_condition,
            "agent_count": self.agent_count,
            "context_tokens": self.context_tokens
        }

def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse comma-separated agent counts."""
    return [int(x.strip()) for x in agent_str.split(",")]

def run_single_game(
    game_id: int,
    agent_count: int,
    context_condition: str,
    context_tokens: int,
    logger: logging.Logger,
    config: Dict[str, Any]
) -> Optional[GameResult]:
    """
    Run a single game simulation with specified context constraints.
    
    Args:
        game_id: Unique game identifier
        agent_count: Number of agents in the simulation
        context_condition: 'full' or 'limited'
        context_tokens: Token limit for limited context (0 for full)
        logger: Logger instance
        config: Configuration dictionary
        
    Returns:
        GameResult if successful, None otherwise
    """
    try:
        # Reset shared memory buffer
        buffer = get_shared_memory_buffer()
        buffer.reset()

        # Initialize agents
        agents = []
        for i in range(agent_count):
            agent_config = AgentConfig(
                model_name=config.get("model_name", "opt-125m"),
                agent_id=i,
                device=config.get("device", "cpu"),
                context_limit=context_tokens if context_condition == "limited" else None
            )
            agent = BaseAgent(agent_config)
            agents.append(agent)

        # Generate synthetic game data
        game_config = SyntheticGameConfig(
            num_agents=agent_count,
            num_items=20,
            num_rounds=5,
            seed=config.get("seed", 42) + game_id
        )
        games = generate_synthetic_games([game_config])
        
        if not games or len(games) == 0:
            logger.warning(f"Game {game_id}: No synthetic data generated")
            return None

        game_data = games[0]
        
        # Simulate game rounds
        for round_num in range(game_data["num_rounds"]):
            for agent in agents:
                # Agent observes current state
                state = game_data["rounds"][round_num]
                
                # Agent decides to store or retrieve from memory
                action = agent.decide_action(state, buffer)
                
                if action["type"] == "store":
                    buffer.store(action["content"], agent.agent_id)
                elif action["type"] == "retrieve":
                    retrieved = buffer.retrieve(action["cue"], agent.agent_id)
                    agent.process_retrieval(retrieved)

        # Compute metrics
        specialization = compute_specialization_index(
            [a.memory_contributions for a in agents],
            agent_count
        )
        
        retrieval = compute_retrieval_efficiency(
            [a.retrieval_successes for a in agents],
            [a.retrieval_attempts for a in agents],
            agent_count
        )

        result = GameResult(
            game_id=game_id,
            specialization_index=specialization,
            retrieval_efficiency=retrieval,
            context_condition=context_condition,
            agent_count=agent_count,
            context_tokens=context_tokens
        )
        
        return result

    except Exception as e:
        logger.error(f"Game {game_id} failed: {str(e)}")
        return None

def save_results(results: List[GameResult], output_path: Path) -> None:
    """Save game results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())

def run_experiment(
    context_condition: str,
    agent_counts: List[int],
    games_per_config: int,
    thresholds: Optional[List[int]] = None,
    seed: int = 42
) -> List[GameResult]:
    """
    Run the full experiment for a given context condition.
    
    Args:
        context_condition: 'full' or 'limited'
        agent_counts: List of agent counts to test
        games_per_config: Number of games per agent count
        thresholds: Context token thresholds for limited context
        seed: Random seed
        
    Returns:
        List of GameResult objects
    """
    logger = setup_logger(
        "experiment",
        log_file=PROJECT_ROOT / "experiment.log"
    )
    logger.info(f"Starting {context_condition} context experiment")
    logger.info(f"Agent counts: {agent_counts}")
    logger.info(f"Games per config: {games_per_config}")
    
    config = get_config()
    config["seed"] = seed
    
    all_results = []
    
    for agent_count in agent_counts:
        # Determine context tokens
        if context_condition == "limited":
            # Use first threshold or default
            token_limit = thresholds[0] if thresholds else 256
        else:
            token_limit = 0  # Full context
        
        logger.info(f"Running {games_per_config} games with {agent_count} agents "
                   f"(context={context_condition}, tokens={token_limit})")
        
        for game_id in range(games_per_config):
            result = run_single_game(
                game_id=game_id,
                agent_count=agent_count,
                context_condition=context_condition,
                context_tokens=token_limit,
                logger=logger,
                config=config
            )
            
            if result:
                all_results.append(result)
                
                # Progress logging
                if (game_id + 1) % 100 == 0:
                    logger.info(f"Completed {game_id + 1}/{games_per_config} games")
    
    # Validate results
    valid_count = validate_experiment_metrics(all_results)
    logger.info(f"Valid results: {valid_count}/{len(all_results)}")
    
    return all_results

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Social Memory Network Experiment")
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Comma-separated agent counts (e.g., '3,5,7')"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=DEFAULT_GAMES_FULL,
        help="Number of games per agent count"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="256",
        help="Comma-separated context token thresholds for limited context"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    parser.add_argument(
        "--plot",
        choices=["scaling"],
        default=None,
        help="Generate scaling plot"
    )
    
    args = parser.parse_args()
    
    agent_counts = parse_agent_counts(args.agents)
    thresholds = parse_agent_counts(args.thresholds) if args.thresholds else None
    
    # Determine output filename
    if args.context == "full":
        output_file = RESULTS_DIR / "results_full.csv"
    else:
        output_file = RESULTS_DIR / "results_limited.csv"
    
    # Run experiment
    results = run_experiment(
        context_condition=args.context,
        agent_counts=agent_counts,
        games_per_config=args.games,
        thresholds=thresholds,
        seed=args.seed
    )
    
    # Save results
    save_results(results, output_file)
    print(f"Results saved to {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())