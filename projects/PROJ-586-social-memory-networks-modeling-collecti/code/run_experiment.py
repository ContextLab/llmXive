import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import get_shared_memory_buffer, reset_shared_memory_buffer, MemoryBuffer
from metrics.specialization import compute_specialization_index, compute_game_level_specialization
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval
from data.loaders import get_dataset, DatasetLoader
from data.synthetic import generate_synthetic_games, SyntheticGameConfig
from utils.config import get_config_manager, get_config
from utils.logging import get_logger, log_experiment_start, log_experiment_end

logger = get_logger(__name__)

def parse_args():
    """Parse command line arguments for experiment configuration."""
    parser = argparse.ArgumentParser(description='Social Memory Networks Experiment')
    parser.add_argument('--context', type=str, default='full',
                      choices=['full', 'limited'],
                      help='Context window condition (full or limited)')
    parser.add_argument('--agents', type=int, nargs='+', default=[2],
                      help='Number of agents to simulate')
    parser.add_argument('--games', type=int, default=1000,
                      help='Number of games per configuration')
    parser.add_argument('--dataset', type=str, default='synthetic',
                      help='Dataset type (synthetic or real)')
    parser.add_argument('--output-dir', type=str, default='data',
                      help='Output directory for results')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    parser.add_argument('--scaling', action='store_true',
                      help='Run scaling analysis with multiple agent counts')
    parser.add_argument('--agent-counts', type=int, nargs='+', default=[3, 5, 7],
                      help='Agent counts for scaling analysis (default: 3, 5, 7)')
    parser.add_argument('--games-per-config', type=int, default=800,
                      help='Number of games per agent configuration for scaling')
    return parser.parse_args()

def get_context_window(context_type: str) -> int:
    """Get context window size based on context type."""
    if context_type == 'full':
        return 2048
    elif context_type == 'limited':
        return 256
    else:
        return 2048

def create_agents(num_agents: int, context_window: int, seed: int) -> List[BaseAgent]:
    """Create a list of agents with the specified configuration."""
    agents = []
    for i in range(num_agents):
        config = AgentConfig(
            agent_id=f"agent_{i}",
            model_name="opt-125m",
            context_window=context_window,
            seed=seed + i,
            device="cpu"
        )
        agent = BaseAgent(config)
        agents.append(agent)
    return agents

def run_single_game(
    agents: List[BaseAgent],
    game_id: int,
    memory_buffer: MemoryBuffer,
    dataset: Dict[str, Any],
    context_window: int
) -> Dict[str, Any]:
    """
    Run a single game simulation with the given agents.
    
    Returns a dictionary with game results and metrics.
    """
    # Reset memory buffer for each game
    reset_shared_memory_buffer()
    
    # Generate synthetic game data if not provided
    if not dataset:
        config = SyntheticGameConfig(
            num_items=10,
            num_rounds=5,
            seed=game_id
        )
        dataset = generate_synthetic_games(config)[0]
    
    game_results = {
        'game_id': game_id,
        'agent_count': len(agents),
        'context_condition': 'full' if context_window >= 2048 else 'limited',
        'context_window': context_window,
        'agent_results': [],
        'memory_actions': [],
        'specialization_index': None,
        'retrieval_efficiency': None
    }
    
    # Simulate game rounds
    for round_num in range(dataset.get('num_rounds', 5)):
        round_data = dataset.get('rounds', [{}])[round_num] if 'rounds' in dataset else {}
        
        # Each agent processes the round
        for agent_idx, agent in enumerate(agents):
            # Agent generates response based on context
            agent_input = f"Round {round_num}: {round_data.get('prompt', 'game continuation')}"
            
            # Agent may store memory
            memory_action = agent.generate_memory_action(agent_input, round_num)
            if memory_action:
                result = memory_buffer.store(memory_action)
                game_results['memory_actions'].append({
                    'agent_id': agent.config.agent_id,
                    'action': memory_action,
                    'round': round_num
                })
            
            # Agent retrieves from memory
            retrieved = memory_buffer.retrieve(agent_input, context_window)
            
            game_results['agent_results'].append({
                'agent_id': agent.config.agent_id,
                'round': round_num,
                'response_length': len(agent.generate_response(agent_input, retrieved)),
                'memory_stored': memory_action is not None,
                'memory_retrieved': len(retrieved) > 0
            })
    
    # Compute metrics for this game
    specialization = compute_game_level_specialization(game_results['agent_results'])
    retrieval = compute_game_level_retrieval(game_results['agent_results'])
    
    game_results['specialization_index'] = specialization
    game_results['retrieval_efficiency'] = retrieval
    
    return game_results

def run_experiment(
    num_agents: int,
    num_games: int,
    context_window: int,
    dataset_type: str,
    seed: int,
    output_path: Path
) -> List[Dict[str, Any]]:
    """
    Run the full experiment with specified configuration.
    
    Args:
        num_agents: Number of agents in the simulation
        num_games: Number of games to simulate
        context_window: Context window size
        dataset_type: Type of dataset to use
        seed: Random seed
        output_path: Path to save results
    
    Returns:
        List of game result dictionaries
    """
    logger.info(f"Starting experiment: {num_agents} agents, {num_games} games")
    log_experiment_start({
        'num_agents': num_agents,
        'num_games': num_games,
        'context_window': context_window,
        'dataset_type': dataset_type,
        'seed': seed
    })
    
    # Set random seeds
    np.random.seed(seed)
    
    # Create agents
    agents = create_agents(num_agents, context_window, seed)
    logger.info(f"Created {len(agents)} agents")
    
    # Get or generate dataset
    if dataset_type == 'synthetic':
        config = SyntheticGameConfig(
            num_items=10,
            num_rounds=5,
            seed=seed
        )
        dataset = generate_synthetic_games(config)[0]
    else:
        dataset = get_dataset(dataset_type)
    
    # Initialize memory buffer
    memory_buffer = get_shared_memory_buffer()
    
    # Run games
    results = []
    for game_id in range(num_games):
        game_result = run_single_game(
            agents=agents,
            game_id=game_id,
            memory_buffer=memory_buffer,
            dataset=dataset,
            context_window=context_window
        )
        results.append(game_result)
        
        # Log progress every 100 games
        if (game_id + 1) % 100 == 0:
            logger.info(f"Completed {game_id + 1}/{num_games} games")
    
    # Save results to CSV
    results_df = pd.DataFrame([{
        'game_id': r['game_id'],
        'specialization_index': r['specialization_index'],
        'retrieval_efficiency': r['retrieval_efficiency'],
        'context_condition': r['context_condition'],
        'agent_count': r['agent_count'],
        'context_window': r['context_window']
    } for r in results])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
    
    log_experiment_end({
        'total_games': num_games,
        'output_file': str(output_path)
    })
    
    return results

def run_scaling_experiment(
    agent_counts: List[int],
    games_per_config: int,
    context_window: int,
    seed: int,
    output_dir: Path
) -> pd.DataFrame:
    """
    Run scaling analysis across multiple agent counts.
    
    Args:
        agent_counts: List of agent counts to test (e.g., [3, 5, 7])
        games_per_config: Number of games per agent configuration
        context_window: Context window size
        seed: Random seed
        output_dir: Directory to save results
    
    Returns:
        DataFrame with all results
    """
    all_results = []
    
    for agent_count in agent_counts:
        logger.info(f"Running scaling experiment: {agent_count} agents")
        
        output_path = output_dir / f"results_scaling_agent{agent_count}.csv"
        results = run_experiment(
            num_agents=agent_count,
            num_games=games_per_config,
            context_window=context_window,
            dataset_type='synthetic',
            seed=seed,
            output_path=output_path
        )
        
        all_results.extend(results)
        logger.info(f"Completed {agent_count} agent configuration")
    
    # Combine all results
    results_df = pd.DataFrame([{
        'game_id': r['game_id'],
        'specialization_index': r['specialization_index'],
        'retrieval_efficiency': r['retrieval_efficiency'],
        'context_condition': r['context_condition'],
        'agent_count': r['agent_count'],
        'context_window': r['context_window']
    } for r in all_results])
    
    # Save combined results
    combined_path = output_dir / "results_scaling.csv"
    results_df.to_csv(combined_path, index=False)
    logger.info(f"Combined scaling results saved to {combined_path}")
    
    return results_df

def main():
    """Main entry point for experiment runner."""
    args = parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting Social Memory Networks Experiment")
    logger.info(f"Configuration: context={args.context}, agents={args.agents}")
    
    if args.scaling:
        # Run scaling analysis with multiple agent counts
        context_window = get_context_window(args.context)
        results_df = run_scaling_experiment(
            agent_counts=args.agent_counts,
            games_per_config=args.games_per_config,
            context_window=context_window,
            seed=args.seed,
            output_dir=output_dir
        )
        
        # Print summary statistics
        logger.info("Scaling Experiment Summary:")
        for agent_count in args.agent_counts:
            subset = results_df[results_df['agent_count'] == agent_count]
            logger.info(f"  Agent count {agent_count}:")
            logger.info(f"    Games: {len(subset)}")
            logger.info(f"    Mean Specialization: {subset['specialization_index'].mean():.4f}")
            logger.info(f"    Mean Retrieval Efficiency: {subset['retrieval_efficiency'].mean():.4f}")
    else:
        # Run standard experiment with specified agent count(s)
        context_window = get_context_window(args.context)
        
        for num_agents in args.agents:
            output_path = output_dir / f"results_agents{num_agents}.csv"
            results = run_experiment(
                num_agents=num_agents,
                num_games=args.games,
                context_window=context_window,
                dataset_type=args.dataset,
                seed=args.seed,
                output_path=output_path
            )
            
            logger.info(f"Completed experiment with {num_agents} agents")
    
    logger.info("Experiment completed successfully")

if __name__ == '__main__':
    main()