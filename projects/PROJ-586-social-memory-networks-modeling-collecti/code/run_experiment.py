"""
Main experiment runner for Social Memory Networks.
Supports full-context and limited-context conditions.
"""
import argparse
import sys
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import csv

# Local imports matching API surface
from utils.logging import setup_logger, get_logger
from utils.config import get_config, get_config_manager
from data.loaders import DatasetLoader, get_dataset, generate_all_datasets
from data.synthetic import generate_synthetic_games, SyntheticGameConfig
from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer
from metrics.specialization import compute_specialization_index, validate_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, validate_retrieval_efficiency
from metrics.validator import validate_single_game_metrics, validate_experiment_metrics

# Configure logger
logger = setup_logger("experiment", "experiment.log")

@dataclass
class GameResult:
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    context_window_tokens: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

def parse_args():
    parser = argparse.ArgumentParser(description="Run social memory experiment")
    parser.add_argument("--context", type=str, default="full", choices=["full", "limited"],
                        help="Context condition: 'full' or 'limited'")
    parser.add_argument("--agents", type=str, default="5",
                        help="Number of agents (int or comma-separated list for scaling)")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Output directory for results")
    parser.add_argument("--thresholds", type=str, default="128,256,512",
                        help="Comma-separated list of context window thresholds for sensitivity")
    parser.add_argument("--plot", type=str, default=None, choices=["scaling"],
                        help="Generate specific plots (e.g., scaling)")
    return parser.parse_args()

def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse agent string into list of integers."""
    return [int(x.strip()) for x in agent_str.split(",")]

def generate_synthetic_game_data(num_games: int, seed: int, agent_count: int,
                                 context_condition: str, context_window: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for the experiment.
    Uses the spec-compliant synthetic generator.
    """
    config = SyntheticGameConfig(
        num_games=num_games,
        seed=seed,
        num_agents=agent_count,
        context_condition=context_condition,
        context_window_tokens=context_window
    )
    # Generate using the real synthetic module
    games = generate_synthetic_games(config)
    return games

def run_single_game(game_id: int, games_data: List[Dict[str, Any]], agent_count: int,
                    context_condition: str, context_window: Optional[int] = None) -> GameResult:
    """
    Run a single game simulation with the specified agents and context.
    """
    try:
        # Reset shared memory buffer for each game
        reset_shared_memory_buffer()
        buffer = get_shared_memory_buffer()

        # Initialize agents
        agents = []
        for i in range(agent_count):
            agent_config = AgentConfig(agent_id=i, model_name="opt-125m", device="cpu")
            agent = BaseAgent(agent_config)
            agents.append(agent)

        # Get game data for this game
        if game_id < len(games_data):
            game_data = games_data[game_id]
        else:
            # Fallback: generate on the fly if needed (should not happen with pre-generated data)
            game_data = generate_synthetic_game_data(1, game_id, agent_count, context_condition, context_window)[0]

        # Simulate game turns
        game_log = []
        for turn in range(game_data.get("num_turns", 10)):
            current_agent = agents[turn % agent_count]
            context = game_data.get("context", "")
            
            # Apply context window truncation if limited
            if context_condition == "limited" and context_window:
                tokens = context.split()
                if len(tokens) > context_window:
                    context = " ".join(tokens[:context_window])

            # Agent makes a decision or memory action
            # In a real implementation, this would call the LLM
            # For synthetic data, we simulate the outcome based on game_data
            action = game_data.get("actions", [{}])[turn] if turn < len(game_data.get("actions", [])) else {}
            
            # Store in shared memory if action is a memory action
            if action.get("type") == "memory_action":
                buffer.store(action.get("content", ""))

            game_log.append({
                "turn": turn,
                "agent": current_agent.agent_id,
                "action": action,
                "context_length": len(context.split())
            })

        # Compute metrics
        # Specialization: how specialized are agents in their memory actions?
        # Retrieval: how efficiently can agents retrieve relevant memories?
        
        # For synthetic data, we compute metrics based on the generated actions
        actions = [a for t in game_log for a in [t["action"]] if a]
        
        # Compute specialization index
        # In a real implementation, this would analyze actual agent behavior
        # Here we use the synthetic data's ground truth if available
        spec_idx = compute_specialization_index(actions, agent_count)
        
        # Compute retrieval efficiency
        retrieval_eff = compute_retrieval_efficiency(actions, buffer, agent_count)

        # Validate metrics
        spec_valid = validate_specialization_index(spec_idx, agent_count)
        retrieval_valid = validate_retrieval_efficiency(retrieval_eff, agent_count)

        if not spec_valid.valid or not retrieval_valid.valid:
            logger.warning(f"Game {game_id}: Metrics validation failed - spec: {spec_valid}, retrieval: {retrieval_valid}")

        return GameResult(
            game_id=game_id,
            specialization_index=spec_idx,
            retrieval_efficiency=retrieval_eff,
            context_condition=context_condition,
            agent_count=agent_count,
            context_window_tokens=context_window,
            success=True
        )

    except Exception as e:
        logger.error(f"Game {game_id} failed: {str(e)}", exc_info=True)
        return GameResult(
            game_id=game_id,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            context_condition=context_condition,
            agent_count=agent_count,
            context_window_tokens=context_window,
            success=False,
            error_message=str(e)
        )

def compute_game_metrics(results: List[GameResult]) -> Dict[str, Any]:
    """Compute aggregate metrics from game results."""
    valid_results = [r for r in results if r.success]
    
    if not valid_results:
        return {
            "total_games": len(results),
            "valid_games": 0,
            "specialization_index_mean": 0.0,
            "specialization_index_std": 0.0,
            "retrieval_efficiency_mean": 0.0,
            "retrieval_efficiency_std": 0.0,
            "success_rate": 0.0
        }

    spec_indices = [r.specialization_index for r in valid_results]
    retrieval_effs = [r.retrieval_efficiency for r in valid_results]

    import numpy as np
    return {
        "total_games": len(results),
        "valid_games": len(valid_results),
        "specialization_index_mean": float(np.mean(spec_indices)),
        "specialization_index_std": float(np.std(spec_indices)),
        "retrieval_efficiency_mean": float(np.mean(retrieval_effs)),
        "retrieval_efficiency_std": float(np.std(retrieval_effs)),
        "success_rate": len(valid_results) / len(results)
    }

def save_results(results: List[GameResult], output_path: Path):
    """Save results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['game_id', 'specialization_index', 'retrieval_efficiency', 
                       'context_condition', 'agent_count', 'context_window_tokens', 
                       'success', 'error_message'])
        
        for r in results:
            writer.writerow([
                r.game_id,
                r.specialization_index,
                r.retrieval_efficiency,
                r.context_condition,
                r.agent_count,
                r.context_window_tokens,
                r.success,
                r.error_message or ""
            ])
    
    logger.info(f"Results saved to {output_path}")

def run_experiment(args):
    """Run the full experiment for specified parameters."""
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    agent_counts = parse_agent_counts(args.agents)
    output_dir = Path(args.output_dir)
    
    # Determine context window for limited context
    context_window = None
    if args.context == "limited":
        # Use first threshold or default
        thresholds = [int(x) for x in args.thresholds.split(",")]
        context_window = thresholds[0] if thresholds else 256
    
    all_results = []
    
    for agent_count in agent_counts:
        logger.info(f"Running experiment with {args.context} context, {agent_count} agents, {args.games} games")
        
        # Generate synthetic game data
        games_data = generate_synthetic_game_data(
            args.games, args.seed, agent_count, args.context, context_window
        )
        
        # Run games
        game_results = []
        for game_id in range(args.games):
            result = run_single_game(
                game_id, games_data, agent_count, args.context, context_window
            )
            game_results.append(result)
            
            if game_id % 100 == 0:
                logger.info(f"Completed {game_id}/{args.games} games")
        
        all_results.extend(game_results)
        
        # Compute and log aggregate metrics
        metrics = compute_game_metrics(game_results)
        logger.info(f"Agent count {agent_count}: {metrics}")
        
        # Save individual results
        result_filename = f"results_{args.context}_agents{agent_count}.csv"
        save_results(game_results, output_dir / result_filename)
    
    # Save combined results
    combined_filename = f"results_{args.context}.csv"
    save_results(all_results, output_dir / combined_filename)
    
    # Compute final aggregate metrics
    final_metrics = compute_game_metrics(all_results)
    logger.info(f"Final aggregate metrics: {final_metrics}")
    
    # Validate against SC-001 (>=95% games produce metrics)
    if final_metrics["success_rate"] < 0.95:
        logger.warning(f"Success rate {final_metrics['success_rate']} < 0.95 (SC-001 violation)")
    
    return all_results

def main():
    args = parse_args()
    run_experiment(args)

if __name__ == "__main__":
    main()
