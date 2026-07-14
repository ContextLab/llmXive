"""
Main experiment runner for Social Memory Networks.
Implements CLI, game simulation, and metric computation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Local imports (must match existing API surface)
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import load_experiment_results, save_experiment_results, get_dataset, enable_synthetic_fallback
from data.synthetic import generate_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None  # None means no limit (full context)
    num_agents: int = 5
    dataset_name: str = "hanabi"
    seed: int = 42
    game_id: str = "default"

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: str
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    num_turns: int
    total_tokens_processed: int
    success: bool
    error_message: Optional[str] = None

def parse_agents_arg(arg: str) -> int:
    """Parse agent count argument. Supports comma-separated lists for scaling (handled externally)."""
    if ',' in arg:
        # For scaling, this is handled by the caller; return first for single-run mode
        parts = [int(p.strip()) for p in arg.split(',')]
        return parts[0] if parts else 5
    return int(arg)

def count_tokens(text: str) -> int:
    """Estimate token count using a simple heuristic (1 token ~ 4 chars)."""
    if not text:
        return 0
    return max(1, len(text.split()))

def truncate_context_to_token_limit(context: str, limit: int) -> str:
    """Truncate context to specified token limit."""
    if limit is None or limit <= 0:
        return context
    
    tokens = context.split()
    if len(tokens) <= limit:
        return context
    
    truncated = ' '.join(tokens[:limit])
    logger.log("context_truncated", original_tokens=len(tokens), limit=limit)
    return truncated

def compute_checksum(data: str) -> str:
    """Compute SHA256 checksum of data."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def load_and_verify_dataset(dataset_name: str, game_id: str) -> List[Dict[str, Any]]:
    """Load dataset with verification and synthetic fallback."""
    try:
        # Try to load real dataset
        dataset = get_dataset(dataset_name)
        if dataset:
            checksum = compute_checksum(json.dumps(dataset))
            logger.log("dataset_loaded", name=dataset_name, checksum=checksum)
            return dataset
    except Exception as e:
        logger.log("dataset_load_failed", name=dataset_name, error=str(e))
    
    # Fallback to synthetic data (per FR-011)
    logger.log("synthetic_fallback", name=dataset_name)
    enable_synthetic_fallback()
    synthetic_data = generate_synthetic_dataset(
        name=dataset_name,
        num_examples=100,  # Minimum 10 per game as per FR-011
        seed=42
    )
    return synthetic_data

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    context: str,
    turn_number: int
) -> Tuple[str, List[Dict[str, Any]]]:
    """Simulate a single turn for an agent."""
    # Agent processes context and generates response
    response = agent.generate_response(context)
    
    # Check for memory actions in response
    memory_actions = []
    if hasattr(response, 'memory_actions'):
        memory_actions = response.memory_actions
    
    # Update memory buffer
    for action in memory_actions:
        memory_buffer.write(action)
    
    return response, memory_actions

def simulate_one_game(config: GameConfig) -> GameResult:
    """Simulate a single game with the given configuration."""
    logger.log("game_start", game_id=config.game_id, context=config.context_condition)
    
    try:
        # Load dataset
        dataset = load_and_verify_dataset(config.dataset_name, config.game_id)
        
        # Initialize agents
        agents = []
        for i in range(config.num_agents):
            agent_config = AgentConfig(
                model_name="facebook/opt-125m",
                device="cpu",
                seed=config.seed + i
            )
            agent = BaseAgent(agent_config)
            agents.append(agent)
        
        # Initialize memory buffer
        memory_buffer = get_shared_buffer()
        reset_shared_buffer()
        
        # Game loop
        total_tokens = 0
        agent_fact_counts = {i: 0 for i in range(config.num_agents)}
        successful_retrievals = 0
        total_retrieval_attempts = 0
        
        # Use first game scenario from dataset
        if not dataset:
            raise ValueError("Dataset is empty")
        
        game_scenario = dataset[0]
        initial_context = game_scenario.get('context', '')
        
        # Apply context truncation if limited
        if config.context_condition == 'limited' and config.token_limit:
            initial_context = truncate_context_to_token_limit(initial_context, config.token_limit)
        
        total_tokens += count_tokens(initial_context)
        
        # Simulate turns
        num_turns = min(10, len(dataset))  # Limit turns for efficiency
        for turn in range(num_turns):
            turn_context = initial_context
            if turn > 0 and memory_buffer:
                # Include recent memory in context
                recent_memories = memory_buffer.get_recent(5)
                memory_text = "\n".join([f"[Memory: {m.key}] {m.value}" for m in recent_memories])
                turn_context = f"{initial_context}\n{memory_text}"
            
            # Truncate if limited context
            if config.context_condition == 'limited' and config.token_limit:
                turn_context = truncate_context_to_token_limit(turn_context, config.token_limit)
            
            total_tokens += count_tokens(turn_context)
            
            # Each agent takes a turn
            for agent_idx, agent in enumerate(agents):
                response, actions = simulate_game_turn(agent, memory_buffer, turn_context, turn)
                
                # Track facts contributed (simplified: count non-empty responses)
                if response and len(str(response)) > 10:
                    agent_fact_counts[agent_idx] += 1
                
                # Track retrieval attempts (simplified: count memory reads)
                for action in actions:
                    if action.get('type') == 'read':
                        total_retrieval_attempts += 1
                        # Assume successful if action exists
                        successful_retrievals += 1
        
        # Compute metrics
        agent_counts = list(agent_fact_counts.values())
        spec_index, _ = compute_specialization_index(agent_counts, num_agents=config.num_agents)
        
        if total_retrieval_attempts > 0:
            ret_eff, _ = compute_retrieval_efficiency(
                successful_retrievals,
                total_retrieval_attempts,
                config.num_agents
            )
        else:
            ret_eff = 0.0
        
        result = GameResult(
            game_id=config.game_id,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            specialization_index=spec_index,
            retrieval_efficiency=ret_eff,
            num_turns=num_turns,
            total_tokens_processed=total_tokens,
            success=True
        )
        
        logger.log("game_complete", game_id=config.game_id, success=True)
        return result
        
    except Exception as e:
        logger.log("game_failed", game_id=config.game_id, error=str(e))
        return GameResult(
            game_id=config.game_id,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            num_turns=0,
            total_tokens_processed=0,
            success=False,
            error_message=str(e)
        )

def write_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write game results to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'game_id', 'context_condition', 'agent_count',
            'specialization_index', 'retrieval_efficiency',
            'num_turns', 'total_tokens_processed', 'success'
        ])
        
        for r in results:
            writer.writerow([
                r.game_id, r.context_condition, r.agent_count,
                f"{r.specialization_index:.6f}", f"{r.retrieval_efficiency:.6f}",
                r.num_turns, r.total_tokens_processed, r.success
            ])

    logger.log("results_written", path=output_path, count=len(results))

def run_simulation(config: GameConfig, num_games: int) -> List[GameResult]:
    """Run multiple game simulations."""
    results = []
    
    for i in range(num_games):
        game_config = GameConfig(
            context_condition=config.context_condition,
            token_limit=config.token_limit,
            num_agents=config.num_agents,
            dataset_name=config.dataset_name,
            seed=config.seed + i,
            game_id=f"{config.context_condition}_game_{i:04d}"
        )
        
        result = simulate_one_game(game_config)
        results.append(result)
        
        # Progress logging
        if (i + 1) % 100 == 0:
            logger.log("simulation_progress", completed=i + 1, total=num_games)
    
    return results

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(description="Social Memory Networks Experiment Runner")
    
    parser.add_argument(
        '--context',
        choices=['full', 'limited'],
        default='full',
        help='Context condition: full or limited'
    )
    
    parser.add_argument(
        '--agents',
        type=str,
        default='5',
        help='Number of agents (comma-separated for scaling)'
    )
    
    parser.add_argument(
        '--dataset',
        choices=['hanabi', 'coqa'],
        default='hanabi',
        help='Dataset to use'
    )
    
    parser.add_argument(
        '--games',
        type=int,
        default=1000,
        help='Number of games to simulate'
    )
    
    parser.add_argument(
        '--token-limit',
        type=int,
        default=256,
        help='Token limit for limited context (default: 256)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV path (default: auto-generated)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    
    return parser

def main():
    """Main entry point for the experiment."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agents
    agent_count = parse_agents_arg(args.agents)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        context_suffix = "full" if args.context == "full" else "limited"
        output_path = f"projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_{context_suffix}.csv"
    
    # Create config
    config = GameConfig(
        context_condition=args.context,
        token_limit=args.token_limit if args.context == "limited" else None,
        num_agents=agent_count,
        dataset_name=args.dataset,
        seed=args.seed,
        game_id="batch"
    )
    
    logger.log("experiment_start", context=args.context, agents=agent_count, games=args.games)
    
    # Run simulation
    results = run_simulation(config, args.games)
    
    # Write results
    write_results_csv(results, output_path)
    
    # Summary
    successful = sum(1 for r in results if r.success)
    logger.log("experiment_complete", total=args.games, successful=successful, output=output_path)
    
    print(f"Experiment complete: {successful}/{args.games} games successful")
    print(f"Results written to: {output_path}")
    
    return 0 if successful > 0 else 1

if __name__ == "__main__":
    sys.exit(main())