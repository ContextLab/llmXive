"""
Main experiment runner for Social Memory Networks.
Supports full-context, limited-context, and scaling experiments.
"""
import argparse
import sys
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Import local modules
from data.loaders import DatasetLoader, get_dataset_spec, generate_all_datasets
from data.synthetic import generate_synthetic_games, SyntheticGameConfig
from metrics.specialization import compute_game_level_specialization, compute_specialization_index
from metrics.retrieval import compute_game_level_retrieval, compute_retrieval_efficiency
from metrics.validator import validate_and_filter_records, compute_metric_statistics
from utils.logging import setup_logger, get_logger
from utils.config import get_config

# Configure logging
logger = setup_logger("run_experiment", level=logging.INFO)

# Constants
DEFAULT_NUM_GAMES = 1000
DEFAULT_AGENT_COUNT = 5
OUTPUT_DIR = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")

def parse_args():
    parser = argparse.ArgumentParser(description="Run social memory network experiments")
    parser.add_argument("--context", type=str, choices=["full", "limited"], default="full",
                        help="Context condition: full or limited")
    parser.add_argument("--agents", type=str, default="5",
                        help="Agent count(s), comma-separated (e.g., 3,5,7 or single value)")
    parser.add_argument("--games", type=int, default=DEFAULT_NUM_GAMES,
                        help="Number of games to simulate per agent count")
    parser.add_argument("--dataset", type=str, default="synthetic",
                        help="Dataset source (currently only 'synthetic' is supported)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--thresholds", type=str, default="128,256,512",
                        help="Token thresholds for limited context (comma-separated)")
    parser.add_argument("--plot", type=str, choices=["scaling", None], default=None,
                        help="Generate scaling plot if specified")
    return parser.parse_args()

def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse comma-separated agent counts into a list of integers."""
    return [int(x.strip()) for x in agent_str.split(",")]

def generate_synthetic_game_data(
    num_games: int,
    agent_count: int,
    context_condition: str,
    thresholds: List[int],
    seed: int
) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for the experiment.
    Uses the synthetic data generator with real random seeds.
    """
    # Set seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)

    # Generate synthetic games using the provided generator
    config = SyntheticGameConfig(
        num_games=num_games,
        num_agents=agent_count,
        context_condition=context_condition,
        thresholds=thresholds,
        seed=seed
    )

    logger.info(f"Generating {num_games} synthetic games for {agent_count} agents "
                f"in {context_condition} context mode")

    games = generate_synthetic_games(config)
    logger.info(f"Generated {len(games)} games successfully")

    return games

def compute_game_metrics(
    games: List[Dict[str, Any]],
    context_condition: str,
    agent_count: int
) -> List[Dict[str, Any]]:
    """
    Compute specialization and retrieval metrics for each game.
    """
    records = []

    for game_id, game_data in enumerate(games):
        try:
            # Compute game-level specialization
            spec_metrics = compute_game_level_specialization(game_data)
            specialization_index = spec_metrics["specialization_index"]

            # Compute game-level retrieval
            retrieval_metrics = compute_game_level_retrieval(game_data)
            retrieval_efficiency = retrieval_metrics["retrieval_efficiency"]

            record = {
                "game_id": game_id,
                "specialization_index": specialization_index,
                "retrieval_efficiency": retrieval_efficiency,
                "context_condition": context_condition,
                "agent_count": agent_count
            }
            records.append(record)

        except Exception as e:
            logger.warning(f"Game {game_id} failed metric computation: {e}")
            continue

    return records

def run_experiment(
    context_condition: str,
    agent_count: int,
    num_games: int,
    thresholds: List[int],
    seed: int
) -> List[Dict[str, Any]]:
    """
    Run a single experiment configuration.
    """
    logger.info(f"Starting experiment: context={context_condition}, agents={agent_count}, "
                f"games={num_games}")

    # Generate synthetic data
    games = generate_synthetic_game_data(
        num_games=num_games,
        agent_count=agent_count,
        context_condition=context_condition,
        thresholds=thresholds,
        seed=seed
    )

    # Compute metrics
    records = compute_game_metrics(
        games=games,
        context_condition=context_condition,
        agent_count=agent_count
    )

    # Validate metrics
    validation_result = validate_and_filter_records(records)
    logger.info(f"Validation: {validation_result['valid_count']}/{validation_result['total_count']} "
                f"games passed validation")

    if validation_result['valid_count'] < 0.95 * validation_result['total_count']:
        logger.warning(f"Validation rate {validation_result['valid_count']/validation_result['total_count']:.2%} "
                       f"is below 95% threshold")

    return records

def save_results(records: List[Dict[str, Any]], output_path: Path):
    """Save results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(records)} records to {output_path}")

def main():
    args = parse_args()

    # Validate dataset
    if args.dataset != "synthetic":
        logger.error(f"Dataset '{args.dataset}' is not supported. Only 'synthetic' is available.")
        sys.exit(1)

    # Parse agent counts
    agent_counts = parse_agent_counts(args.agents)

    # Parse thresholds
    thresholds = [int(x.strip()) for x in args.thresholds.split(",")]

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_records = []

    for agent_count in agent_counts:
        # Determine output filename
        if len(agent_counts) == 1:
            if args.context == "limited":
                output_file = OUTPUT_DIR / "results_limited.csv"
            else:
                output_file = OUTPUT_DIR / "results_full.csv"
        else:
            output_file = OUTPUT_DIR / f"results_agent_{agent_count}.csv"

        # Run experiment
        records = run_experiment(
            context_condition=args.context,
            agent_count=agent_count,
            num_games=args.games,
            thresholds=thresholds,
            seed=args.seed
        )

        all_records.extend(records)

        # Save individual results
        save_results(records, output_file)

    # Save combined results if multiple agent counts
    if len(agent_counts) > 1:
        combined_file = OUTPUT_DIR / f"results_{args.context}_combined.csv"
        save_results(all_records, combined_file)

    # Compute and log statistics
    stats = compute_metric_statistics(all_records)
    logger.info("Experiment Statistics:")
    logger.info(f"  Specialization Index: mean={stats['specialization']['mean']:.4f}, "
                f"std={stats['specialization']['std']:.4f}")
    logger.info(f"  Retrieval Efficiency: mean={stats['retrieval']['mean']:.4f}, "
                f"std={stats['retrieval']['std']:.4f}")

    logger.info("Experiment completed successfully")

if __name__ == "__main__":
    main()