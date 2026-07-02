"""
Main experiment runner for Social Memory Networks.
Implements game simulation loops for US-1, US-2, and US-3.
"""
import argparse
import csv
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project-relative imports based on provided API surface
from agent.base_agent import BaseAgent, AgentConfig
from memory.buffer import MemoryBuffer, get_shared_memory_buffer
from metrics.specialization import compute_specialization_index, compute_game_level_specialization
from metrics.retrieval import compute_retrieval_efficiency, compute_game_level_retrieval
from metrics.validator import validate_and_filter_records, compute_metric_statistics
from data.loaders import get_dataset
from utils.logging import setup_logger, get_logger
from utils.config import get_config

# Ensure project root is in path for relative imports if running as script
if 'code' not in sys.path:
    project_root = Path(__file__).resolve().parent
    if project_root.name == 'code':
        sys.path.insert(0, str(project_root.parent))

@dataclass
class GameResult:
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    success: bool
    duration: float

def parse_agent_counts(agent_arg: str) -> List[int]:
    """Parse comma-separated agent counts."""
    if not agent_arg:
        return [5]  # Default
    return [int(x.strip()) for x in agent_arg.split(',')]

def run_single_game(game_id: int, context_condition: str, agent_count: int, 
                    dataset: Any, config: Dict[str, Any]) -> Optional[GameResult]:
    """
    Run a single game simulation with specified agents and context.
    Returns GameResult or None if simulation fails.
    """
    start_time = time.time()
    logger = get_logger()
    
    try:
        # Initialize memory buffer (shared across agents in this game)
        buffer = get_shared_memory_buffer()
        buffer.reset()
        
        # Initialize agents
        agents = []
        for i in range(agent_count):
            agent_config = AgentConfig(
                agent_id=i,
                model_name="facebook/opt-125m",
                device="cpu",  # CPU-only as per constraints
                context_condition=context_condition
            )
            agent = BaseAgent(agent_config)
            agents.append(agent)
        
        # Get game data from dataset
        # Using synthetic fallback as per T004 constraint
        game_data = dataset.get_game(game_id)
        if game_data is None:
            logger.warning(f"Game {game_id} not found in dataset")
            return None
        
        # Simulate game rounds
        success = False
        for round_num in range(min(10, config.get('max_rounds', 10))):
            # Each agent acts based on context and memory
            for agent in agents:
                # Agent observes game state
                observation = game_data.get('state', {}).get(f'round_{round_num}', {})
                
                # Agent retrieves from shared memory
                memory_context = buffer.get_recent_entries(k=3)
                
                # Agent decides action
                action = agent.step(observation, memory_context)
                
                # Store action in shared memory if applicable
                if action and action.get('type') == 'store':
                    buffer.store(action.get('content', ''))
                
                # Check for game completion
                if action and action.get('type') == 'success':
                    success = True
                    break
            
            if success:
                break
        
        # Compute metrics
        specialization = compute_game_level_specialization(agents, buffer)
        retrieval = compute_game_level_retrieval(agents, buffer)
        
        duration = time.time() - start_time
        
        return GameResult(
            game_id=game_id,
            context_condition=context_condition,
            agent_count=agent_count,
            specialization_index=specialization,
            retrieval_efficiency=retrieval,
            success=success,
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Game {game_id} failed: {e}")
        return None

def save_results(results: List[GameResult], output_path: str):
    """Save results to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'game_id', 'specialization_index', 'retrieval_efficiency', 
            'context_condition', 'agent_count', 'success', 'duration'
        ])
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                'game_id': r.game_id,
                'specialization_index': r.specialization_index,
                'retrieval_efficiency': r.retrieval_efficiency,
                'context_condition': r.context_condition,
                'agent_count': r.agent_count,
                'success': r.success,
                'duration': r.duration
            })

def run_experiment(args: argparse.Namespace) -> List[GameResult]:
    """
    Run the full experiment based on CLI arguments.
    Supports US-1 (full context), US-2 (limited context), and US-3 (scaling).
    """
    logger = get_logger()
    config = get_config()
    
    # Load dataset (uses synthetic fallback as per T004)
    dataset = get_dataset(args.dataset)
    
    all_results = []
    
    # Determine agent counts to run
    agent_counts = parse_agent_counts(args.agents)
    
    # Determine games per configuration
    games_per_config = args.games
    
    # Determine context condition
    context_condition = args.context
    
    # If scaling analysis (US-3), run for each agent count
    if context_condition == 'scaling' or len(agent_counts) > 1:
        logger.info(f"Running scaling analysis for agent counts: {agent_counts}")
        for n_agents in agent_counts:
            logger.info(f"Running {games_per_config} games with {n_agents} agents")
            for game_id in range(games_per_config):
                result = run_single_game(
                    game_id=game_id,
                    context_condition='scaling',
                    agent_count=n_agents,
                    dataset=dataset,
                    config=config
                )
                if result:
                    all_results.append(result)
    else:
        # Run single context condition
        logger.info(f"Running {games_per_config} games with {agent_counts[0]} agents in {context_condition} context")
        for game_id in range(games_per_config):
            result = run_single_game(
                game_id=game_id,
                context_condition=context_condition,
                agent_count=agent_counts[0],
                dataset=dataset,
                config=config
            )
            if result:
                all_results.append(result)
    
    return all_results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Social Memory Networks Experiment')
    parser.add_argument('--context', type=str, default='full',
                      choices=['full', 'limited', 'scaling'],
                      help='Context condition: full, limited, or scaling')
    parser.add_argument('--agents', type=str, default='5',
                      help='Agent count(s), comma-separated (e.g., 3,5,7)')
    parser.add_argument('--games', type=int, default=1000,
                      help='Number of games to run')
    parser.add_argument('--dataset', type=str, default='synthetic',
                      help='Dataset to use')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(level=logging.INFO)
    logger = get_logger()
    
    logger.info(f"Starting experiment: context={args.context}, agents={args.agents}, games={args.games}")
    
    # Run experiment
    results = run_experiment(args)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        context_prefix = args.context.replace('_', '')
        if len(parse_agent_counts(args.agents)) > 1:
            output_path = f"projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_results_{context_prefix}.csv"
        else:
            output_path = f"projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_{context_prefix}.csv"
    
    # Save results
    save_results(results, output_path)
    
    logger.info(f"Experiment complete. {len(results)} games processed. Results saved to {output_path}")
    
    # Print summary statistics
    if results:
        from metrics.validator import compute_metric_statistics
        stats = compute_metric_statistics(results)
        logger.info(f"Specialization Index (mean): {stats['specialization_mean']:.4f}")
        logger.info(f"Retrieval Efficiency (mean): {stats['retrieval_mean']:.4f}")
        logger.info(f"Success Rate: {stats['success_rate']:.2%}")

if __name__ == '__main__':
    main()
