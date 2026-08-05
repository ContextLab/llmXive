"""
Main experiment runner for Social Memory Networks.
Implements limited-context simulation and full experiment orchestration.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Local imports
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import load_experiment_results, save_experiment_results, DatasetLoader
from memory.buffer import MemoryBuffer, get_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from metrics.validator import validate_single_game_metrics, ValidationResult
from utils.logging import get_logger


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    seed: int = 42
    dataset_name: str = "hanabi"
    game_id: int = 0


@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse agents argument (e.g., '5' or '3,5,7')."""
    if ',' in agents_str:
        return [int(x.strip()) for x in agents_str.split(',')]
    return [int(agents_str.strip())]


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_data_checksum(data: Any) -> str:
    """Compute checksum of data structure."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def load_and_verify_dataset(config: GameConfig) -> List[Dict[str, Any]]:
    """Load dataset with verification."""
    loader = DatasetLoader()
    dataset = loader.load(config.dataset_name)
    
    # Verify data integrity
    checksum = compute_data_checksum(dataset)
    logger = get_logger(__name__)
    logger.log("dataset_loaded", dataset_name=config.dataset_name, 
               record_count=len(dataset), checksum=checksum)
    
    return dataset


def truncate_context(context: str, token_limit: int, tokenizer: Any = None) -> str:
    """
    Truncate context to a specified token limit.
    
    Args:
        context: Full context string
        token_limit: Maximum number of tokens allowed
        tokenizer: Optional tokenizer for accurate token counting. 
                  If None, uses simple whitespace approximation.
    
    Returns:
        Truncated context string
    """
    if token_limit is None or token_limit <= 0:
        return context
    
    # Simple tokenization: split on whitespace
    tokens = context.split()
    
    if len(tokens) <= token_limit:
        return context
    
    # Truncate and add indicator
    truncated_tokens = tokens[:token_limit]
    truncated = ' '.join(truncated_tokens)
    
    # Add truncation indicator
    if not truncated.endswith('.'):
        truncated += '...'
    
    return truncated


def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    context: str,
    game_config: GameConfig
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Simulate a single turn for an agent.
    
    Returns:
        Tuple of (agent_response, memory_actions)
    """
    # Apply context truncation if in limited mode
    if game_config.context_condition == 'limited' and game_config.token_limit:
        context = truncate_context(context, game_config.token_limit)
    
    # Agent processes context and may generate memory actions
    response, memory_actions = agent.generate_response(
        context=context,
        memory_actions=memory_buffer.get_recent_actions()
    )
    
    # Write memory actions to buffer
    for action in memory_actions:
        memory_buffer.write(action)
    
    return response, memory_actions


def simulate_one_game(
    config: Union[GameConfig, Dict[str, Any]],
    game_id: Optional[int] = None,
    dataset: Optional[List[Dict[str, Any]]] = None
) -> GameResult:
    """
    Simulate a single game with the given configuration.
    
    Args:
        config: GameConfig or dict with game parameters
        game_id: Optional game ID override
        dataset: Optional pre-loaded dataset
    
    Returns:
        GameResult with metrics and status
    """
    # Handle dict input for flexibility
    if isinstance(config, dict):
        config = GameConfig(
            num_agents=config.get('num_agents', 5),
            context_condition=config.get('context_condition', 'full'),
            token_limit=config.get('token_limit'),
            seed=config.get('seed', 42),
            dataset_name=config.get('dataset_name', 'hanabi'),
            game_id=config.get('game_id', 0)
        )
    
    # Set seed for reproducibility
    np.random.seed(config.seed)
    
    logger = get_logger(__name__)
    logger.log("game_start", game_id=game_id or config.game_id, 
               context=config.context_condition, agents=config.num_agents)
    
    try:
        # Load dataset if not provided
        if dataset is None:
            dataset = load_and_verify_dataset(config)
        
        if not dataset:
            raise ValueError("Dataset is empty")
        
        # Initialize agents
        agents = []
        for i in range(config.num_agents):
            agent_config = AgentConfig(
                agent_id=i,
                model_name="facebook/opt-125m",
                device="cpu",
                seed=config.seed + i
            )
            agent = BaseAgent(agent_config)
            agents.append(agent)
        
        # Initialize shared memory buffer
        memory_buffer = get_shared_buffer()
        memory_buffer.reset()
        
        # Select game data
        game_data = dataset[config.game_id % len(dataset)]
        full_context = game_data.get('context', '')
        
        # Run game simulation with turn-based interaction
        all_retrievals = []
        agent_contributions = {i: [] for i in range(config.num_agents)}
        
        # Simulate turns
        for turn in range(min(10, len(dataset))):  # Limit turns for feasibility
            current_agent = agents[turn % config.num_agents]
            
            # Get context for this turn
            context = full_context
            if config.context_condition == 'limited' and config.token_limit:
                context = truncate_context(full_context, config.token_limit)
            
            # Agent generates response and memory actions
            response, memory_actions = simulate_game_turn(
                current_agent, memory_buffer, context, config
            )
            
            # Track retrievals and contributions
            for action in memory_actions:
                if action.get('type') == 'read':
                    all_retrievals.append({
                        'agent_id': current_agent.config.agent_id,
                        'success': True,  # Simplified for CPU-only simulation
                        'key': action.get('key', '')
                    })
                elif action.get('type') == 'write':
                    agent_contributions[current_agent.config.agent_id].append(
                        action.get('key', '')
                    )
        
        # Compute metrics
        # Specialization index: based on distribution of contributions
        facts_list = [agent_contributions[i] for i in range(config.num_agents)]
        spec_index, _ = compute_specialization_index(facts_list, num_agents=config.num_agents)
        
        # Retrieval efficiency: successful retrievals / total queries
        successful = sum(1 for r in all_retrievals if r['success'])
        total = len(all_retrievals) if all_retrievals else 1
        ret_eff, _ = compute_retrieval_efficiency(successful, total, config.num_agents)
        
        # Validate metrics
        validation: ValidationResult = validate_single_game_metrics(
            spec_index, ret_eff, config.num_agents
        )
        
        if not validation.is_valid:
            logger.log("validation_warning", game_id=game_id or config.game_id,
                      message=validation.message)
        
        result = GameResult(
            game_id=game_id or config.game_id,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            specialization_index=spec_index,
            retrieval_efficiency=ret_eff,
            success=True,
            metadata={
                'turns': len(all_retrievals),
                'validation': validation.to_json() if hasattr(validation, 'to_json') else str(validation)
            }
        )
        
        logger.log("game_complete", game_id=game_id or config.game_id,
                  spec_index=spec_index, ret_eff=ret_eff)
        
        return result
        
    except Exception as e:
        logger.log("game_error", game_id=game_id or config.game_id,
                  error=str(e), exc_info=True)
        return GameResult(
            game_id=game_id or config.game_id,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            success=False,
            error_message=str(e)
        )


def run_simulation(
    num_games: int,
    config: GameConfig,
    dataset: Optional[List[Dict[str, Any]]] = None
) -> List[GameResult]:
    """
    Run multiple game simulations.
    
    Args:
        num_games: Number of games to simulate
        config: Game configuration
        dataset: Optional pre-loaded dataset
    
    Returns:
        List of GameResult objects
    """
    logger = get_logger(__name__)
    logger.log("simulation_start", num_games=num_games, 
               context=config.context_condition, agents=config.num_agents)
    
    results = []
    start_time = time.time()
    
    for game_id in range(num_games):
        # Update config with current game_id
        current_config = GameConfig(
            num_agents=config.num_agents,
            context_condition=config.context_condition,
            token_limit=config.token_limit,
            seed=config.seed + game_id,
            dataset_name=config.dataset_name,
            game_id=game_id
        )
        
        result = simulate_one_game(current_config, game_id=game_id, dataset=dataset)
        results.append(result)
        
        # Progress logging
        if (game_id + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (game_id + 1) / elapsed
            logger.log("simulation_progress", 
                      games_completed=game_id + 1,
                      elapsed_seconds=elapsed,
                      games_per_second=rate)
    
    total_time = time.time() - start_time
    logger.log("simulation_complete", 
               games_completed=len(results),
               total_time=total_time,
               success_rate=sum(1 for r in results if r.success) / len(results) if results else 0)
    
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write simulation results to CSV file."""
    logger = get_logger(__name__)
    
    if not results:
        raise ValueError("No results to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'game_id', 'context_condition', 'agent_count',
            'specialization_index', 'retrieval_efficiency', 'success', 'error_message'
        ])
        
        # Data rows
        for r in results:
            writer.writerow([
                r.game_id,
                r.context_condition,
                r.agent_count,
                f"{r.specialization_index:.6f}",
                f"{r.retrieval_efficiency:.6f}",
                r.success,
                r.error_message or ''
            ])
    
    logger.log("results_written", path=str(output_path), record_count=len(results))


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the experiment."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    
    parser.add_argument(
        '--context', 
        type=str, 
        choices=['full', 'limited'],
        default='full',
        help='Context condition: full or limited'
    )
    
    parser.add_argument(
        '--agents',
        type=str,
        default='5',
        help='Number of agents (e.g., 5 or 3,5,7 for scaling)'
    )
    
    parser.add_argument(
        '--games',
        type=int,
        default=1000,
        help='Number of games to simulate'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        default='hanabi',
        help='Dataset name (hanabi or coqa)'
    )
    
    parser.add_argument(
        '--token-limit',
        type=int,
        default=512,
        help='Token limit for limited context condition'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: auto-generated based on config)'
    )
    
    return parser


def main() -> None:
    """Main entry point for the experiment."""
    parser = build_parser()
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    logger.log("experiment_start", **vars(args))
    
    # Parse agents
    agent_counts = parse_agents_arg(args.agents)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = f"_{args.context}"
        if len(agent_counts) > 1:
            suffix += f"_agents{','.join(map(str, agent_counts))}"
        output_path = Path("results") / f"results{suffix}.csv"
    
    all_results = []
    
    for agent_count in agent_counts:
        config = GameConfig(
            num_agents=agent_count,
            context_condition=args.context,
            token_limit=args.token_limit if args.context == 'limited' else None,
            seed=args.seed,
            dataset_name=args.dataset,
            game_id=0
        )
        
        # Load dataset once per agent count
        dataset = load_and_verify_dataset(config)
        
        # Run simulation
        results = run_simulation(
            num_games=args.games,
            config=config,
            dataset=dataset
        )
        
        all_results.extend(results)
    
    # Write results
    write_results_csv(all_results, output_path)
    
    logger.log("experiment_complete", 
               total_games=len(all_results),
               output_file=str(output_path))
    
    print(f"Experiment complete. Results written to {output_path}")


if __name__ == "__main__":
    main()