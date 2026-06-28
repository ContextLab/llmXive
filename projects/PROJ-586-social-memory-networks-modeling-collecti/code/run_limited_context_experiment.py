"""
Run limited-context experiment for User Story 2.

This script executes 1000 games with limited context window and outputs
results to results_limited.csv in the results directory.
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import random

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from run_experiment import parse_args, get_context_window, create_agents, run_single_game, run_experiment, main
from metrics.specialization import compute_specialization_index, compute_game_level_specialization, validate_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval, validate_retrieval_efficiency
from metrics.validator import validate_single_game_metrics, validate_experiment_metrics, validate_and_filter_records
from data.loaders import generate_all_datasets, get_dataset_spec
from utils.logging import setup_logger, get_logger, log_experiment_start, log_experiment_end
from utils.config import get_config, get_config_manager


def run_limited_context_experiment(
    num_games: int = 1000,
    num_agents: int = 4,
    context_tokens: int = 128,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Run experiment with limited context window.
    
    Args:
        num_games: Number of games to simulate
        num_agents: Number of agents in the experiment
        context_tokens: Context window token limit (limited)
        seed: Random seed for reproducibility
        output_dir: Directory to write output CSV (default: results/)
    
    Returns:
        DataFrame with game results including metrics
    """
    # Set random seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # Setup logger
    logger = setup_logger("limited_context_experiment")
    log_experiment_start(logger, "Limited Context Experiment", {
        "num_games": num_games,
        "num_agents": num_agents,
        "context_tokens": context_tokens,
        "seed": seed
    })
    
    # Determine output directory
    if output_dir is None:
        # Use project-specific results directory as per tasks.md
        project_root = code_dir.parent.parent
        output_dir = project_root / "results"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "results_limited.csv"
    
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Output path: {output_path}")
    
    # Generate synthetic dataset for the experiment
    logger.info("Generating synthetic dataset...")
    dataset_spec = get_dataset_spec("synthetic")
    games_data = generate_all_datasets(num_games, dataset_spec)
    
    # Initialize agents
    logger.info(f"Creating {num_agents} agents...")
    agents = create_agents(num_agents, seed=seed)
    
    # Run games and collect metrics
    results = []
    valid_count = 0
    failed_count = 0
    
    for game_id in range(num_games):
        try:
            # Run single game with limited context
            game_result = run_single_game(
                game_id=game_id,
                agents=agents,
                game_data=games_data[game_id],
                context_tokens=context_tokens,
                context_condition="limited"
            )
            
            # Compute metrics for this game
            if game_result is not None:
                # Compute specialization index
                spec_metrics = compute_game_level_specialization(game_result)
                specialization_index = validate_specialization_index(spec_metrics)
                
                # Compute retrieval efficiency
                retrieval_metrics = compute_game_level_retrieval(game_result)
                retrieval_efficiency = validate_retrieval_efficiency(retrieval_metrics)
                
                # Validate combined metrics
                validation = validate_single_game_metrics(
                    specialization_index=specialization_index,
                    retrieval_efficiency=retrieval_efficiency
                )
                
                if validation.is_valid:
                    results.append({
                        "game_id": game_id,
                        "specialization_index": float(specialization_index),
                        "retrieval_efficiency": float(retrieval_efficiency),
                        "context_condition": "limited",
                        "agent_count": num_agents
                    })
                    valid_count += 1
                else:
                    failed_count += 1
                    logger.debug(f"Game {game_id} failed validation: {validation.reason}")
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            logger.warning(f"Game {game_id} failed with error: {e}")
            continue
        
        # Progress logging every 100 games
        if (game_id + 1) % 100 == 0:
            logger.info(f"Completed {game_id + 1}/{num_games} games (valid: {valid_count}, failed: {failed_count})")
    
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Validate experiment metrics
    experiment_validation = validate_experiment_metrics(results_df)
    logger.info(f"Experiment validation: {experiment_validation.is_valid}")
    logger.info(f"Validation rate: {experiment_validation.validation_rate:.2%}")
    
    # Check SC-001 requirement (≥95% games produce metrics)
    if experiment_validation.validation_rate < 0.95:
        logger.warning(f"Validation rate {experiment_validation.validation_rate:.2%} is below SC-001 threshold of 95%")
    
    # Compute and log statistics
    if len(results_df) > 0:
        mean_spec = results_df["specialization_index"].mean()
        mean_retrieval = results_df["retrieval_efficiency"].mean()
        std_spec = results_df["specialization_index"].std()
        std_retrieval = results_df["retrieval_efficiency"].std()
        
        logger.info(f"Specialization Index - Mean: {mean_spec:.4f}, Std: {std_spec:.4f}")
        logger.info(f"Retrieval Efficiency - Mean: {mean_retrieval:.4f}, Std: {std_retrieval:.4f}")
    
    # Save to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results_df)} records to {output_path}")
    
    log_experiment_end(logger, "Limited Context Experiment", {
        "total_games": num_games,
        "valid_games": valid_count,
        "failed_games": failed_count,
        "validation_rate": experiment_validation.validation_rate,
        "output_file": str(output_path)
    })
    
    return results_df


def main():
    """Main entry point for limited context experiment."""
    parser = argparse.ArgumentParser(
        description="Run limited-context experiment for social memory networks"
    )
    parser.add_argument(
        "--num-games", type=int, default=1000,
        help="Number of games to simulate (default: 1000)"
    )
    parser.add_argument(
        "--num-agents", type=int, default=4,
        help="Number of agents (default: 4)"
    )
    parser.add_argument(
        "--context-tokens", type=int, default=128,
        help="Context window token limit (default: 128)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory for results CSV (default: project results/)"
    )
    
    args = parser.parse_args()
    
    # Convert output_dir to Path if provided
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    # Run experiment
    results = run_limited_context_experiment(
        num_games=args.num_games,
        num_agents=args.num_agents,
        context_tokens=args.context_tokens,
        seed=args.seed,
        output_dir=output_dir
    )
    
    print(f"\nExperiment completed successfully!")
    print(f"Output saved to: projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_limited.csv")
    print(f"Total games: {args.num_games}")
    print(f"Valid games: {len(results)}")
    
    if len(results) > 0:
        print(f"\nSummary Statistics:")
        print(f"  Specialization Index: {results['specialization_index'].mean():.4f} ± {results['specialization_index'].std():.4f}")
        print(f"  Retrieval Efficiency: {results['retrieval_efficiency'].mean():.4f} ± {results['retrieval_efficiency'].std():.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())