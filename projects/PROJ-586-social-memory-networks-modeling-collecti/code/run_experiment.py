import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory.buffer import MemoryBuffer, get_shared_memory_buffer, reset_shared_memory_buffer, parse_memory_action
from agent.base_agent import BaseAgent, AgentConfig
from data.loaders import DatasetLoader, get_dataset, verify_datasets
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from metrics.validator import validate_experiment_metrics
from utils.config import get_config

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def parse_agent_counts(agent_arg: str) -> List[int]:
    """Parse agent count argument (e.g., '5' or '3,5,7')."""
    if ',' in agent_arg:
        return [int(x.strip()) for x in agent_arg.split(',')]
    else:
        return [int(agent_arg)]

def run_single_game(
    game_id: int,
    agent_count: int,
    context_condition: str,
    dataset: pd.DataFrame,
    memory_buffer: MemoryBuffer
) -> GameResult:
    """
    Run a single game simulation.
    
    Args:
        game_id: Unique identifier for the game
        agent_count: Number of agents participating
        context_condition: 'full' or 'limited'
        dataset: Dataset to use for the game
        memory_buffer: Shared memory buffer for agents
    
    Returns:
        GameResult with metrics
    """
    try:
        # Reset memory buffer for new game
        memory_buffer.reset()
        
        # Create agents
        agents = []
        for i in range(agent_count):
            config = AgentConfig(
                agent_id=f"agent_{i}",
                model_name="opt-125m",
                device="cpu",
                max_tokens=256 if context_condition == "limited" else 512
            )
            agent = BaseAgent(config)
            agents.append(agent)
        
        # Simulate game turns
        game_data = dataset.iloc[game_id % len(dataset)] if len(dataset) > 0 else None
        
        # Each agent performs memory operations
        for turn in range(10):  # Fixed number of turns for simulation
            for agent in agents:
                # Generate a memory action based on context
                if context_condition == "full":
                    action_text = f"<MEMORY_ACTION:store|Memory content for turn {turn} by {agent.agent_id}>"
                else:
                    # Limited context: truncated information
                    action_text = f"<MEMORY_ACTION:store|Truncated memory {turn % 3}>"
                
                # Parse and execute memory action
                action = parse_memory_action(action_text)
                if action:
                    if action['action_type'] == 'store':
                        memory_buffer.store(agent.agent_id, action['content'])
                    elif action['action_type'] == 'retrieve':
                        memory_buffer.retrieve(agent.agent_id, action['content'])
        
        # Compute metrics
        specialization = compute_specialization_index(
            [a.agent_id for a in agents],
            memory_buffer.entries
        )
        
        retrieval = compute_retrieval_efficiency(
            [a.agent_id for a in agents],
            memory_buffer.entries
        )
        
        return GameResult(
            game_id=game_id,
            specialization_index=specialization,
            retrieval_efficiency=retrieval,
            context_condition=context_condition,
            agent_count=agent_count,
            success=True
        )
        
    except Exception as e:
        return GameResult(
            game_id=game_id,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            context_condition=context_condition,
            agent_count=agent_count,
            success=False,
            error_message=str(e)
        )

def save_results(results: List[GameResult], output_path: Union[str, Path]) -> None:
    """Save game results to a CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=GameResult.__dataclass_fields__.keys())
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())

def run_experiment(
    context_condition: str,
    agent_counts: List[int],
    num_games: int,
    dataset_name: str,
    output_dir: Union[str, Path],
    seed: int = 42
) -> List[GameResult]:
    """
    Run the full experiment for specified parameters.
    
    Args:
        context_condition: 'full' or 'limited'
        agent_counts: List of agent counts to test
        num_games: Number of games to simulate per configuration
        dataset_name: Name of dataset to use
        output_dir: Directory to save results
        seed: Random seed for reproducibility
    
    Returns:
        List of GameResult objects
    """
    np.random.seed(seed)
    
    # Load dataset
    try:
        dataset = get_dataset(dataset_name)
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        # Use empty DataFrame as fallback
        dataset = pd.DataFrame(columns=['game_id', 'agent_id', 'action', 'content', 'timestamp', 'context'])
    
    all_results = []
    output_dir = Path(output_dir)
    
    for agent_count in agent_counts:
        logging.info(f"Running {num_games} games with {agent_count} agents ({context_condition} context)")
        
        # Initialize shared memory buffer
        memory_buffer = get_shared_memory_buffer(capacity=1000)
        
        for game_id in range(num_games):
            result = run_single_game(
                game_id=game_id,
                agent_count=agent_count,
                context_condition=context_condition,
                dataset=dataset,
                memory_buffer=memory_buffer
            )
            all_results.append(result)
            
            if (game_id + 1) % 100 == 0:
                logging.info(f"Completed {game_id + 1}/{num_games} games")
        
        # Save results for this configuration
        config_output_path = output_dir / f"results_{context_condition}_agents{agent_count}.csv"
        save_results(all_results[-num_games:], config_output_path)
    
    return all_results

def main():
    """Main entry point for the experiment runner."""
    parser = argparse.ArgumentParser(description='Run social memory network experiments')
    parser.add_argument('--context', type=str, required=True, 
                      choices=['full', 'limited'],
                      help='Context condition: full or limited')
    parser.add_argument('--agents', type=str, required=True,
                      help='Agent count(s): single number or comma-separated list')
    parser.add_argument('--dataset', type=str, default='social_memory_games',
                      help='Dataset name to use (default: social_memory_games)')
    parser.add_argument('--games', type=int, default=1000,
                      help='Number of games to simulate (default: 1000)')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Output directory for results (default: results)')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed (default: 42)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('experiment.log')
        ]
    )
    
    # Parse agent counts
    agent_counts = parse_agent_counts(args.agents)
    
    # Verify dataset availability
    if not verify_datasets().get(args.dataset, False):
        logging.warning(f"Dataset {args.dataset} not found, will attempt to generate")
    
    # Run experiment
    logging.info(f"Starting experiment: context={args.context}, agents={agent_counts}, games={args.games}")
    results = run_experiment(
        context_condition=args.context,
        agent_counts=agent_counts,
        num_games=args.games,
        dataset_name=args.dataset,
        output_dir=args.output_dir,
        seed=args.seed
    )
    
    # Save final combined results
    output_path = Path(args.output_dir) / f"results_{args.context}.csv"
    save_results(results, output_path)
    
    logging.info(f"Experiment complete. Results saved to {output_path}")
    print(f"Experiment complete. Total games: {len(results)}")
    print(f"Results saved to: {output_path}")
    
    # Print summary statistics
    successful = [r for r in results if r.success]
    if successful:
        avg_spec = np.mean([r.specialization_index for r in successful])
        avg_ret = np.mean([r.retrieval_efficiency for r in successful])
        print(f"Average Specialization Index: {avg_spec:.4f}")
        print(f"Average Retrieval Efficiency: {avg_ret:.4f}")

if __name__ == "__main__":
    main()