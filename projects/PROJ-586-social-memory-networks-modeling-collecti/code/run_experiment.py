"""
Main experiment runner for social memory network simulations.

This script orchestrates the simulation of multi-agent games with
different context conditions and agent counts, computing metrics
for specialization and retrieval efficiency.

Usage:
    python run_experiment.py --context full --agents 5 --games 1000
    python run_experiment.py --context limited --agents 5 --games 1000
    python run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling
"""

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.base_agent import BaseAgent, AgentConfig
from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer, parse_memory_action
from metrics.specialization import compute_specialization_index, validate_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, validate_retrieval_efficiency
from metrics.validator import validate_and_filter_records, compute_metric_statistics
from data.synthetic import generate_synthetic_games, SyntheticGameConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    seed: int
    num_turns: int
    memory_entries: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'game_id': self.game_id,
            'specialization_index': self.specialization_index,
            'retrieval_efficiency': self.retrieval_efficiency,
            'context_condition': self.context_condition,
            'agent_count': self.agent_count,
            'seed': self.seed,
            'num_turns': self.num_turns,
            'memory_entries': self.memory_entries
        }

from dataclasses import dataclass


def parse_agent_counts(agent_string: str) -> List[int]:
    """
    Parse agent counts from comma-separated string.
    
    Args:
        agent_string: Comma-separated list of agent counts (e.g., "3,5,7")
        
    Returns:
        List of agent counts
    """
    return [int(x.strip()) for x in agent_string.split(',')]


def run_single_game(game_id: int, agent_count: int, context_tokens: int,
                   seed: int, context_condition: str) -> Optional[GameResult]:
    """
    Run a single game simulation with specified parameters.
    
    This function creates agents, initializes the memory buffer,
    runs the game simulation, and computes the required metrics.
    
    Args:
        game_id: Unique ID for the game
        agent_count: Number of agents in the simulation
        context_tokens: Context window size
        seed: Random seed for reproducibility
        context_condition: 'full' or 'limited'
        
    Returns:
        GameResult object or None if validation fails
    """
    try:
        # Reset shared memory for this game
        reset_shared_memory_buffer()
        buffer = get_shared_memory_buffer()
        
        # Set random seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Create agents
        agents = []
        for i in range(agent_count):
            config = AgentConfig(
                agent_id=f"agent_{i}",
                model_name="opt-125m",
                device="cpu",
                context_tokens=context_tokens
            )
            # For synthetic testing, we create a mock agent that doesn't require actual model loading
            # In a real implementation, this would load the actual model
            agents.append({
                'id': f"agent_{i}",
                'config': config,
                'memory': []
            })
        
        # Generate synthetic game data for this configuration
        game_config = SyntheticGameConfig(
            num_games=1,
            num_agents=agent_count,
            context_tokens=context_tokens,
            seed=seed,
            max_turns=50,
            memory_capacity=100
        )
        games = generate_synthetic_games(game_config)
        game_data = games[0]
        
        # Simulate turns and memory operations
        memory_entries_count = 0
        retrieval_events = []
        specialization_events = []
        
        for turn_data in game_data['turns']:
            agent_id = turn_data['agent_id']
            action = turn_data['action']
            
            if action == 'store':
                # Simulate storing information
                content = f"Stored content by {agent_id} at turn {turn_data['turn_id']}"
                buffer.store(agent_id=agent_id, content=content)
                memory_entries_count += 1
                specialization_events.append({
                    'agent_id': agent_id,
                    'action': 'store',
                    'turn': turn_data['turn_id']
                })
            
            elif action == 'retrieve':
                # Simulate retrieval
                query = f"Query by {agent_id} at turn {turn_data['turn_id']}"
                results = buffer.retrieve(query=query, limit=5)
                retrieval_events.append({
                    'agent_id': agent_id,
                    'query': query,
                    'results_count': len(results),
                    'turn': turn_data['turn_id']
                })
            
            elif action == 'update':
                # Simulate update
                if len(buffer) > 0:
                    entry_id = buffer.get_all()[-1].id
                    buffer.update(entry_id, content=f"Updated by {agent_id}")
        
        # Compute metrics
        # Specialization index: measures how specialized each agent's memory contributions are
        if len(specialization_events) > 0:
            agent_counts = {}
            for event in specialization_events:
                aid = event['agent_id']
                agent_counts[aid] = agent_counts.get(aid, 0) + 1
            
            # Compute specialization as entropy-based measure
            total = sum(agent_counts.values())
            probs = [count / total for count in agent_counts.values()]
            entropy = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
            max_entropy = np.log2(agent_count) if agent_count > 1 else 1
            specialization_index = entropy / max_entropy if max_entropy > 0 else 0
        else:
            specialization_index = 0.0
        
        # Retrieval efficiency: measures how effectively agents retrieve relevant information
        if len(retrieval_events) > 0:
            successful_retrievals = sum(1 for r in retrieval_events if r['results_count'] > 0)
            retrieval_efficiency = successful_retrievals / len(retrieval_events)
        else:
            retrieval_efficiency = 1.0  # No retrievals means no failures
        
        # Validate metrics
        spec_valid = validate_specialization_index(specialization_index)
        ret_valid = validate_retrieval_efficiency(retrieval_efficiency)
        
        if not spec_valid or not ret_valid:
            logger.warning(f"Game {game_id} failed validation: spec={spec_valid}, ret={ret_valid}")
            return None
        
        return GameResult(
            game_id=game_id,
            specialization_index=specialization_index,
            retrieval_efficiency=retrieval_efficiency,
            context_condition=context_condition,
            agent_count=agent_count,
            seed=seed,
            num_turns=len(game_data['turns']),
            memory_entries=memory_entries_count
        )
        
    except Exception as e:
        logger.error(f"Error running game {game_id}: {e}")
        return None


def save_results(results: List[GameResult], output_path: Path) -> None:
    """
    Save game results to CSV file.
    
    Args:
        results: List of GameResult objects
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'game_id', 'specialization_index', 'retrieval_efficiency',
            'context_condition', 'agent_count', 'seed', 'num_turns', 'memory_entries'
        ])
        writer.writeheader()
        
        for result in results:
            writer.writerow(result.to_dict())
    
    logger.info(f"Saved {len(results)} results to {output_path}")


def run_experiment(agent_counts: List[int], games_per_config: int,
                  context_condition: str, context_tokens: int,
                  seed_base: int = 42) -> List[GameResult]:
    """
    Run the full experiment for specified configurations.
    
    Args:
        agent_counts: List of agent counts to test
        games_per_config: Number of games per agent count configuration
        context_condition: 'full' or 'limited'
        context_tokens: Context window size
        seed_base: Base seed for reproducibility
        
    Returns:
        List of all game results
    """
    all_results = []
    
    for agent_count in agent_counts:
        logger.info(f"Running experiment for {agent_count} agents ({games_per_config} games)")
        
        for game_id in range(games_per_config):
            seed = seed_base + game_id + (agent_count * 1000)
            
            result = run_single_game(
                game_id=game_id,
                agent_count=agent_count,
                context_tokens=context_tokens,
                seed=seed,
                context_condition=context_condition
            )
            
            if result is not None:
                all_results.append(result)
            
            if (game_id + 1) % 100 == 0:
                logger.info(f"  Completed {game_id + 1}/{games_per_config} games")
    
    return all_results


def main():
    """Main entry point for the experiment runner."""
    parser = argparse.ArgumentParser(description='Run social memory network experiments')
    parser.add_argument('--context', type=str, default='full',
                      choices=['full', 'limited'],
                      help='Context condition (full or limited)')
    parser.add_argument('--agents', type=str, default='5',
                      help='Agent counts (comma-separated, e.g., "3,5,7")')
    parser.add_argument('--games', type=int, default=1000,
                      help='Number of games per configuration')
    parser.add_argument('--seed', type=int, default=42,
                      help='Base random seed')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path (optional)')
    parser.add_argument('--plot', type=str, default=None,
                      choices=['scaling', None],
                      help='Generate scaling plot if "scaling"')
    
    args = parser.parse_args()
    
    # Parse agent counts
    agent_counts = parse_agent_counts(args.agents)
    
    # Set context tokens based on condition
    context_tokens = 2048 if args.context == 'full' else 256
    
    logger.info(f"Starting experiment: {args.context} context, {agent_counts} agents, {args.games} games each")
    
    # Run experiment
    start_time = time.time()
    results = run_experiment(
        agent_counts=agent_counts,
        games_per_config=args.games,
        context_condition=args.context,
        context_tokens=context_tokens,
        seed_base=args.seed
    )
    elapsed = time.time() - start_time
    
    logger.info(f"Experiment completed in {elapsed:.2f} seconds")
    logger.info(f"Valid results: {len(results)}")
    
    # Validate results
    if len(results) > 0:
        valid_count = len([r for r in results if validate_specialization_index(r.specialization_index) and 
                         validate_retrieval_efficiency(r.retrieval_efficiency)])
        validation_rate = valid_count / len(results)
        logger.info(f"Validation rate: {validation_rate:.2%}")
        
        # Compute statistics
        stats = compute_metric_statistics(results)
        logger.info(f"Specialization mean: {stats['specialization']['mean']:.4f} ± {stats['specialization']['std']:.4f}")
        logger.info(f"Retrieval mean: {stats['retrieval']['mean']:.4f} ± {stats['retrieval']['std']:.4f}")
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        suffix = f"_{args.context}"
        if len(agent_counts) > 1:
            suffix += f"_agents{','.join(map(str, agent_counts))}"
        output_path = output_dir / f"results{suffix}.csv"
    
    # Save results
    save_results(results, output_path)
    
    # Generate scaling plot if requested
    if args.plot == 'scaling' and len(agent_counts) > 1:
        logger.info("Generating scaling plot...")
        # Import scaling analysis module
        from analysis.scaling import generate_scaling_plot
        scaling_data_path = output_dir / "scaling_data.csv"
        # Save data for scaling analysis
        with open(scaling_data_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'agent_count', 'specialization_index', 'retrieval_efficiency', 'game_id'
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    'agent_count': r.agent_count,
                    'specialization_index': r.specialization_index,
                    'retrieval_efficiency': r.retrieval_efficiency,
                    'game_id': r.game_id
                })
        
        # Generate plot
        plot_path = Path(__file__).parent.parent / "results" / "scaling_plot.pdf"
        generate_scaling_plot(scaling_data_path, plot_path)
        logger.info(f"Scaling plot saved to {plot_path}")
    
    logger.info(f"Results saved to {output_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())