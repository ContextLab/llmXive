"""
Main experiment runner for Social Memory Networks.

This script runs simulations for different context conditions and agent counts,
computing specialization and retrieval efficiency metrics.
"""
import argparse
import sys
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer
from metrics.specialization import compute_specialization_index, compute_game_level_specialization
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval
from metrics.validator import validate_single_game_metrics, validate_experiment_metrics
from data.loaders import get_dataset, generate_all_datasets
from utils.logging import setup_logger, get_logger
from utils.config import get_config, get_config_manager

# Configure logging
logger = setup_logger("experiment")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run social memory network experiments")
    parser.add_argument("--context", type=str, default="full",
                      choices=["full", "limited"],
                      help="Context condition: full or limited")
    parser.add_argument("--agents", type=str, default="5",
                      help="Number of agents (comma-separated for scaling: 3,5,7)")
    parser.add_argument("--games", type=int, default=1000,
                      help="Number of games to simulate")
    parser.add_argument("--dataset", type=str, default="synthetic",
                      help="Dataset to use (synthetic for testing)")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="results",
                      help="Directory for output files")
    parser.add_argument("--plot", type=str, default=None,
                      choices=["scaling", None],
                      help="Generate scaling plot if specified")
    parser.add_argument("--thresholds", type=str, default="128,256,512",
                      help="Context token limits for sensitivity analysis")
    return parser.parse_args()

def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse agent count string into list of integers."""
    return [int(x.strip()) for x in agent_str.split(",")]

def generate_synthetic_game_data(num_games: int, seed: int, num_agents: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic game data for the experiment.
    
    This creates a realistic simulation of a transactive memory game where
    agents must coordinate to recall information distributed across the group.
    
    The data is generated deterministically based on the seed to ensure reproducibility.
    """
    np.random.seed(seed)
    games = []
    
    # Game parameters based on agent count
    base_items = num_agents * 5  # Each agent specializes in ~5 items
    context_window = 512 if num_agents > 5 else 256  # Simulate context limits
    
    for game_id in range(num_games):
        # Create a game state with distributed knowledge
        game_state = {
            "game_id": game_id,
            "num_agents": num_agents,
            "total_items": base_items,
            "context_window": context_window,
            "seed": seed + game_id,
        }
        
        # Simulate agent knowledge distribution
        # In a real transactive memory system, knowledge is unevenly distributed
        agent_knowledge = []
        for agent_idx in range(num_agents):
            # Each agent knows a specialized subset plus some overlap
            specialization_strength = np.random.beta(2, 5)  # Most agents have narrow specialization
            num_specialized = int(base_items * 0.3 * (1 + specialization_strength))
            num_shared = int(base_items * 0.1 * np.random.uniform(0.5, 1.5))
            
            # Generate actual knowledge items (deterministic based on seed)
            rng = np.random.RandomState(seed + game_id * 1000 + agent_idx)
            specialized_items = rng.choice(base_items, num_specialized, replace=False)
            shared_items = rng.choice(base_items, num_shared, replace=False)
            
            agent_knowledge.append({
                "agent_id": agent_idx,
                "specialized_items": sorted(list(set(specialized_items))),
                "shared_items": sorted(list(set(shared_items))),
                "total_knowledge": len(set(specialized_items) | set(shared_items))
            })
        
        game_state["agent_knowledge"] = agent_knowledge
        
        # Simulate the game: agents query and retrieve information
        queries = []
        for _ in range(10):  # 10 queries per game
            query_item = rng.randint(0, base_items)
            # Determine which agent(s) know this item
            knowing_agents = [
                idx for idx, agent in enumerate(agent_knowledge)
                if query_item in agent["specialized_items"] or query_item in agent["shared_items"]
            ]
            
            queries.append({
                "query_id": len(queries),
                "item": query_item,
                "knowing_agents": knowing_agents,
                "retrieved_by": None,
                "retrieval_successful": False
            })
        
        # Simulate retrieval process
        for query in queries:
            if query["knowing_agents"]:
                # In full context, the right agent is always found
                # In limited context, retrieval depends on context window
                if game_state["context_window"] >= 256 or len(query["knowing_agents"]) <= 2:
                    query["retrieved_by"] = query["knowing_agents"][0]
                    query["retrieval_successful"] = True
                else:
                    # Limited context might miss the best agent
                    query["retrieved_by"] = rng.choice(query["knowing_agents"])
                    query["retrieval_successful"] = rng.random() > 0.3  # 70% success rate
        
        game_state["queries"] = queries
        games.append(game_state)
    
    return games

def compute_game_metrics(game_state: Dict[str, Any], context_condition: str) -> Optional[Dict[str, Any]]:
    """
    Compute specialization and retrieval metrics for a single game.
    
    Args:
        game_state: The game state dictionary
        context_condition: 'full' or 'limited'
        
    Returns:
        Dictionary with metrics or None if validation fails
    """
    num_agents = game_state["num_agents"]
    agent_knowledge = game_state["agent_knowledge"]
    queries = game_state["queries"]
    
    # Compute specialization index
    # Each agent's knowledge distribution
    knowledge_counts = [len(agent["specialized_items"]) for agent in agent_knowledge]
    specialization_idx = compute_specialization_index(knowledge_counts, num_agents)
    
    # Compute retrieval efficiency
    successful_retrievals = sum(1 for q in queries if q["retrieval_successful"])
    total_queries = len(queries)
    
    if total_queries == 0:
        return None
        
    retrieval_efficiency = compute_retrieval_efficiency(
        successful_retrievals, total_queries, num_agents
    )
    
    # Validate metrics
    validation = validate_single_game_metrics(specialization_idx, retrieval_efficiency)
    if not validation.valid:
        logger.debug(f"Game {game_state['game_id']} failed validation: {validation.reason}")
        return None
    
    return {
        "game_id": game_state["game_id"],
        "specialization_index": float(specialization_idx),
        "retrieval_efficiency": float(retrieval_efficiency),
        "context_condition": context_condition,
        "agent_count": num_agents,
        "successful_retrievals": successful_retrievals,
        "total_queries": total_queries
    }

def run_experiment(args: argparse.Namespace) -> pd.DataFrame:
    """
    Run the full experiment with specified parameters.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        DataFrame with experiment results
    """
    # Set random seed
    np.random.seed(args.seed)
    
    # Parse agent counts
    agent_counts = parse_agent_counts(args.agents)
    
    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    games_per_config = args.games // len(agent_counts)
    
    logger.info(f"Starting experiment: context={args.context}, agents={agent_counts}, "
               f"games_per_config={games_per_config}")
    
    for agent_count in agent_counts:
        logger.info(f"Running simulation for {agent_count} agents...")
        
        # Generate game data
        games = generate_synthetic_game_data(
            num_games=games_per_config,
            seed=args.seed + agent_count * 1000,
            num_agents=agent_count
        )
        
        # Compute metrics for each game
        for game_state in games:
            metrics = compute_game_metrics(game_state, args.context)
            if metrics:
                results.append(metrics)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Validate overall experiment
    if len(df) > 0:
        validation = validate_experiment_metrics(df)
        if not validation.valid:
            logger.warning(f"Experiment validation warnings: {validation.reason}")
        
        logger.info(f"Experiment complete: {len(df)} valid games, "
                   f"success rate: {len(df)/len(results)*100:.1f}%")
    else:
        logger.error("No valid games produced metrics!")
    
    return df

def main():
    """Main entry point."""
    args = parse_args()
    
    # Run experiment
    df = run_experiment(args)
    
    # Save results
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    if len(parse_agent_counts(args.agents)) > 1:
        filename = f"results_scaling_{args.context}_{timestamp}.csv"
    else:
        filename = f"results_{args.context}_{timestamp}.csv"
    
    output_path = Path(args.output_dir) / filename
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
    
    # Print summary statistics
    if len(df) > 0:
        logger.info("Summary Statistics:")
        logger.info(f"  Mean Specialization: {df['specialization_index'].mean():.3f}")
        logger.info(f"  Mean Retrieval Efficiency: {df['retrieval_efficiency'].mean():.3f}")
        logger.info(f"  Games Analyzed: {len(df)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())