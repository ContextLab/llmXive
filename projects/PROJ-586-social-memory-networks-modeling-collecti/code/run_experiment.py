"""
Social Memory Networks - Experiment Runner

This module provides the main experiment orchestration for running
multi-agent social memory experiments with different context conditions.

Supports:
- Full context condition (baseline)
- Limited context condition (truncation impact)
- Various agent counts for scaling analysis
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import json
import time

# Import from project modules
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import get_dataset, save_experiment_results, get_dataset_spec
from data.synthetic import generate_synthetic_games, SyntheticGameConfig
from memory.buffer import (
    MemoryAction, MemoryEntry, MemoryActionRequest, MemoryActionResult,
    MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer,
    parse_memory_action, execute_memory_action, handle_agent_output
)
from metrics.specialization import (
    SpecializationMetrics, compute_specialization_index,
    compute_game_level_specialization, validate_specialization_index
)
from metrics.retrieval import (
    RetrievalMetrics, compute_retrieval_rate, compute_retrieval_efficiency,
    validate_retrieval_efficiency, compute_game_level_retrieval
)
from metrics.validator import (
    ValidationResult, GameMetricRecord, validate_single_game_metrics,
    validate_experiment_metrics, validate_and_filter_records, compute_metric_statistics
)
from utils.config import Config, ConfigManager, get_config_manager, get_config, load_config
from utils.logging import setup_logger, get_logger, log_experiment_start, log_experiment_end, info, warning, error, debug

# Constants
DEFAULT_GAME_COUNT = 1000
DEFAULT_AGENT_COUNT = 3
DEFAULT_CONTEXT_WINDOW = 2048  # Full context
LIMITED_CONTEXT_WINDOW = 512   # Limited context for US-2
DEFAULT_SEED = 42
OUTPUT_DIR = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for experiment configuration."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    
    # Context condition
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: 'full' for baseline, 'limited' for truncation"
    )
    
    # Agent configuration
    parser.add_argument(
        "--agents",
        type=int,
        default=DEFAULT_AGENT_COUNT,
        help=f"Number of agents (default: {DEFAULT_AGENT_COUNT})"
    )
    
    # Dataset configuration
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        choices=["synthetic", "hanabi", "coqa"],
        help="Dataset to use (synthetic fallback only)"
    )
    
    # Game count
    parser.add_argument(
        "--games",
        type=int,
        default=DEFAULT_GAME_COUNT,
        help=f"Number of games to simulate (default: {DEFAULT_GAME_COUNT})"
    )
    
    # Random seed
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})"
    )
    
    # Output path
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: auto-generated based on context)"
    )
    
    # Verbosity
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def get_context_window(context_condition: str) -> int:
    """Get the context window size based on condition."""
    if context_condition == "limited":
        return LIMITED_CONTEXT_WINDOW
    return DEFAULT_CONTEXT_WINDOW


def create_agents(
    num_agents: int,
    config: Config,
    seed: int
) -> List[BaseAgent]:
    """Create a list of agents with unique IDs."""
    agents = []
    for i in range(num_agents):
        agent_config = AgentConfig(
            agent_id=f"agent_{i}",
            model_name="opt-125m",
            device="cpu",
            precision="float32",
            seed=seed + i
        )
        agent = BaseAgent(agent_config)
        agents.append(agent)
    return agents


def run_single_game(
    game_id: int,
    agents: List[BaseAgent],
    context_window: int,
    dataset: str,
    seed: int,
    logger: Any
) -> Optional[Dict[str, Any]]:
    """
    Run a single game simulation with the given agents.
    
    Returns a dictionary with game results including metrics,
    or None if the game fails validation.
    """
    try:
        # Reset shared memory buffer for each game
        reset_shared_memory_buffer()
        memory_buffer = get_shared_memory_buffer()
        
        # Generate synthetic game data
        game_config = SyntheticGameConfig(
            num_agents=len(agents),
            context_window=context_window,
            seed=seed + game_id,
            dataset_type=dataset
        )
        
        game_data = generate_synthetic_games([game_config])[0]
        
        # Initialize game state
        game_state = {
            "game_id": game_id,
            "agents": agents,
            "memory_buffer": memory_buffer,
            "context_window": context_window,
            "turn": 0,
            "max_turns": 10,
            "completed_clues": [],
            "agent_contributions": {f"agent_{i}": [] for i in range(len(agents))}
        }
        
        # Run game simulation
        for turn in range(game_state["max_turns"]):
            game_state["turn"] = turn
            
            # Each agent takes a turn
            for agent in agents:
                # Prepare context with truncation if limited
                full_context = game_data["context"]
                if context_window < len(full_context):
                    truncated_context = full_context[:context_window]
                else:
                    truncated_context = full_context
                
                # Agent processes context and decides on action
                agent_output = agent.process_context(truncated_context, game_state)
                
                # Handle memory action if present
                if hasattr(agent_output, 'memory_action') and agent_output.memory_action:
                    action_result = handle_agent_output(
                        agent_output,
                        memory_buffer,
                        game_state
                    )
                    
                    # Record agent contribution
                    agent_id = agent.config.agent_id
                    game_state["agent_contributions"][agent_id].append({
                        "turn": turn,
                        "action": action_result.action if action_result else None,
                        "success": action_result.success if action_result else False
                    })
                
                # Check for game completion
                if agent_output.completed:
                    game_state["completed_clues"].append(agent_output.clue)
                    break
        
        # Compute metrics for this game
        specialization_metrics = compute_game_level_specialization(
            game_state["agent_contributions"],
            len(agents)
        )
        
        retrieval_metrics = compute_game_level_retrieval(
            game_state["agent_contributions"],
            len(agents)
        )
        
        # Validate metrics
        spec_validation = validate_specialization_index(specialization_metrics)
        retrieval_validation = validate_retrieval_efficiency(retrieval_metrics)
        
        if not spec_validation.is_valid or not retrieval_validation.is_valid:
            logger.warning(f"Game {game_id}: Metrics validation failed")
            return None
        
        # Compile game result
        result = {
            "game_id": game_id,
            "specialization_index": specialization_metrics.specialization_index,
            "retrieval_efficiency": retrieval_metrics.efficiency,
            "context_condition": "limited" if context_window == LIMITED_CONTEXT_WINDOW else "full",
            "agent_count": len(agents),
            "context_window": context_window,
            "completed_clues": len(game_state["completed_clues"]),
            "total_turns": game_state["turn"] + 1,
            "agent_contributions_count": {
                aid: len(contribs)
                for aid, contribs in game_state["agent_contributions"].items()
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Game {game_id} failed with error: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def run_experiment(
    context_condition: str,
    num_agents: int,
    num_games: int,
    dataset: str,
    seed: int,
    output_path: Optional[Path] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Run the full experiment with specified configuration.
    
    Args:
        context_condition: 'full' or 'limited'
        num_agents: Number of agents to simulate
        num_games: Number of games to run
        dataset: Dataset type to use
        seed: Random seed
        output_path: Optional output path for results
        verbose: Enable verbose logging
        
    Returns:
        DataFrame with experiment results
    """
    # Setup logger
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logger("experiment", log_level=log_level)
    
    # Get context window
    context_window = get_context_window(context_condition)
    
    # Determine output path
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if context_condition == "limited":
            output_path = OUTPUT_DIR / "results_limited.csv"
        else:
            output_path = OUTPUT_DIR / "results_full.csv"
    
    # Log experiment start
    log_experiment_start(logger, {
        "context_condition": context_condition,
        "num_agents": num_agents,
        "num_games": num_games,
        "context_window": context_window,
        "dataset": dataset,
        "seed": seed,
        "output_path": str(output_path)
    })
    
    info(logger, f"Starting experiment: {context_condition} context, {num_agents} agents, {num_games} games")
    info(logger, f"Context window: {context_window} tokens")
    
    # Create agents
    config = get_config()
    agents = create_agents(num_agents, config, seed)
    info(logger, f"Created {len(agents)} agents")
    
    # Run games
    results = []
    start_time = time.time()
    
    for game_id in range(num_games):
        game_result = run_single_game(
            game_id=game_id,
            agents=agents,
            context_window=context_window,
            dataset=dataset,
            seed=seed,
            logger=logger
        )
        
        if game_result is not None:
            results.append(game_result)
            
            # Log progress every 100 games
            if (game_id + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (game_id + 1) / elapsed
                info(logger, f"Progress: {game_id + 1}/{num_games} games ({rate:.2f} games/sec)")
    
    elapsed = time.time() - start_time
    info(logger, f"Experiment completed in {elapsed:.2f} seconds")
    info(logger, f"Successful games: {len(results)}/{num_games}")
    
    # Convert to DataFrame
    if len(results) > 0:
        df = pd.DataFrame(results)
        
        # Validate experiment metrics
        validation = validate_experiment_metrics(df)
        if not validation.is_valid:
            warning(logger, f"Experiment validation warnings: {validation.messages}")
        
        # Compute statistics
        stats = compute_metric_statistics(df)
        info(logger, f"Specialization index mean: {stats['specialization']['mean']:.4f}")
        info(logger, f"Retrieval efficiency mean: {stats['retrieval']['mean']:.4f}")
        
        # Save results
        save_experiment_results(df, output_path)
        info(logger, f"Results saved to {output_path}")
        
        # Log experiment end
        log_experiment_end(logger, {
            "games_completed": len(results),
            "games_failed": num_games - len(results),
            "elapsed_seconds": elapsed,
            "output_path": str(output_path),
            "validation": validation.to_dict()
        })
        
        return df
    else:
        error(logger, "No valid game results produced")
        log_experiment_end(logger, {
            "games_completed": 0,
            "games_failed": num_games,
            "error": "No valid results"
        })
        return pd.DataFrame()


def main():
    """Main entry point for the experiment runner."""
    args = parse_args()
    
    # Set random seed for reproducibility
    np.random.seed(args.seed)
    
    # Run experiment
    df = run_experiment(
        context_condition=args.context,
        num_agents=args.agents,
        num_games=args.games,
        dataset=args.dataset,
        seed=args.seed,
        output_path=Path(args.output) if args.output else None,
        verbose=args.verbose
    )
    
    # Exit with appropriate code
    if len(df) > 0:
        print(f"Experiment completed successfully: {len(df)} games")
        sys.exit(0)
    else:
        print("Experiment failed: no valid results")
        sys.exit(1)


if __name__ == "__main__":
    main()