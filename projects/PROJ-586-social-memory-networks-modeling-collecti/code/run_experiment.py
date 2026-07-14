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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from local packages
from agent.base_agent import AgentConfig, BaseAgent
from analysis.sensitivity import truncate_context_to_token_limit
from data.loaders import load_experiment_results, save_experiment_results
from data.synthetic import generate_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer
from metrics.retrieval import compute_retrieval_efficiency
from metrics.specialization import compute_specialization_index
from utils.logging import get_logger


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None  # For limited context
    seed: int = 42
    dataset_name: str = "synthetic"
    max_turns: int = 20

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: str
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    token_limit: Optional[int]
    success: bool
    error_message: Optional[str] = None


def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts or a single number."""
    try:
        if ',' in agents_str:
            return [int(x.strip()) for x in agents_str.split(',')]
        else:
            return [int(agents_str)]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agent count: {agents_str}")


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_data_checksum(config: GameConfig) -> str:
    """Compute a checksum for the dataset based on config."""
    # In a real implementation, this would checksum the actual dataset file.
    # For synthetic data, we checksum the config parameters.
    data_str = json.dumps({
        "dataset": config.dataset_name,
        "seed": config.seed,
        "num_agents": config.num_agents,
        "condition": config.context_condition
    }, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


def load_and_verify_dataset(config: GameConfig) -> List[Dict[str, Any]]:
    """Load dataset, falling back to synthetic if necessary."""
    logger = get_logger(__name__)
    
    # Try to load real dataset first
    dataset_path = Path(f"data/{config.dataset_name}.json")
    if dataset_path.exists():
        try:
            with open(dataset_path, 'r') as f:
                data = json.load(f)
            logger.log("dataset_loaded", path=str(dataset_path))
            return data
        except Exception as e:
            logger.log("dataset_load_failed", error=str(e))
    
    # Fallback to synthetic
    logger.log("using_synthetic_fallback", dataset=config.dataset_name)
    synthetic_data = generate_synthetic_dataset(
        name=config.dataset_name,
        num_samples=100,  # Small sample for simulation
        seed=config.seed
    )
    return synthetic_data


def truncate_context(context: str, token_limit: int, tokenizer: Optional[Any] = None) -> str:
    """
    Truncate context to a specified token limit.
    Uses a simple whitespace-based token approximation if no tokenizer is provided.
    """
    if token_limit is None or len(context) <= token_limit:
        return context
    
    # Simple approximation: split by whitespace and take first N tokens
    # In a real implementation, use the actual tokenizer from the model
    tokens = context.split()
    if len(tokens) <= token_limit:
        return context
    
    truncated = ' '.join(tokens[:token_limit])
    return truncated


def simulate_game_turn(
    agent: BaseAgent,
    context: str,
    memory_buffer: MemoryBuffer,
    turn: int,
    config: GameConfig
) -> Tuple[str, Dict[str, Any]]:
    """
    Simulate a single turn for an agent.
    Returns (response, metrics_dict).
    """
    # Apply context truncation if in limited mode
    if config.context_condition == "limited" and config.token_limit:
        processed_context = truncate_context(context, config.token_limit)
    else:
        processed_context = context
    
    # Agent processes context and generates response
    # In a real implementation, this would call the LLM
    response = f"Agent response at turn {turn} for context: {processed_context[:50]}..."
    
    # Record memory action
    memory_buffer.write(
        key=f"turn_{turn}_agent_{agent.config.agent_id}",
        value=response
    )
    
    metrics = {
        "turn": turn,
        "context_length": len(processed_context),
        "response_length": len(response)
    }
    
    return response, metrics


def simulate_one_game(config: GameConfig) -> GameResult:
    """
    Simulate a single game with multiple agents.
    Returns a GameResult with computed metrics.
    """
    logger = get_logger(__name__)
    game_id = f"game_{config.seed}_{config.num_agents}_{config.context_condition}"
    
    try:
        # Initialize agents
        agents = []
        for i in range(config.num_agents):
            agent_config = AgentConfig(
                agent_id=i,
                model_name="facebook/opt-125m",
                device="cpu"
            )
            agent = BaseAgent(agent_config)
            agents.append(agent)
        
        # Load dataset
        dataset = load_and_verify_dataset(config)
        
        # Initialize shared memory buffer
        memory_buffer = get_shared_buffer()
        memory_buffer.reset()
        
        # Track facts contributed by each agent
        agent_facts: Dict[int, List[str]] = {i: [] for i in range(config.num_agents)}
        successful_retrievals = 0
        total_queries = 0
        
        # Simulate turns
        for turn in range(config.max_turns):
            # Select active agent (round-robin for simplicity)
            active_agent_idx = turn % config.num_agents
            active_agent = agents[active_agent_idx]
            
            # Build context from memory and dataset
            context_parts = []
            for key, entry in memory_buffer.read_all():
                context_parts.append(f"{key}: {entry.value}")
            context = "\n".join(context_parts) if context_parts else "Initial context"
            
            # Add dataset facts to context
            if dataset and turn < len(dataset):
                context += f"\nDataset fact: {dataset[turn].get('fact', 'unknown')}"
            
            # Simulate turn
            response, turn_metrics = simulate_game_turn(
                active_agent, context, memory_buffer, turn, config
            )
            
            # Track facts contributed
            agent_facts[active_agent_idx].append(response)
            
            # Simulate retrieval attempt
            total_queries += 1
            # Simple heuristic: 70% success rate for demonstration
            if random.random() < 0.7:
                successful_retrievals += 1
        
        # Compute metrics
        facts_list = [agent_facts[i] for i in range(config.num_agents)]
        spec_index, _ = compute_specialization_index(facts_list, num_agents=config.num_agents)
        ret_eff, _ = compute_retrieval_efficiency(
            successful_retrievals, total_queries, config.num_agents
        )
        
        logger.log(
            "game_completed",
            game_id=game_id,
            specialization=spec_index,
            retrieval=ret_eff
        )
        
        return GameResult(
            game_id=game_id,
            specialization_index=spec_index,
            retrieval_efficiency=ret_eff,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            token_limit=config.token_limit,
            success=True
        )
        
    except Exception as e:
        logger.log("game_failed", game_id=game_id, error=str(e))
        return GameResult(
            game_id=game_id,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            token_limit=config.token_limit,
            success=False,
            error_message=str(e)
        )


def run_simulation(
    num_games: int,
    config: GameConfig,
    output_path: Path
) -> List[GameResult]:
    """Run multiple game simulations and save results."""
    logger = get_logger(__name__)
    results = []
    
    logger.log(
        "simulation_start",
        num_games=num_games,
        context=config.context_condition,
        agents=config.num_agents
    )
    
    for i in range(num_games):
        game_config = GameConfig(
            num_agents=config.num_agents,
            context_condition=config.context_condition,
            token_limit=config.token_limit,
            seed=config.seed + i,
            dataset_name=config.dataset_name,
            max_turns=config.max_turns
        )
        result = simulate_one_game(game_config)
        results.append(result)
        
        if i % 100 == 0:
            logger.log("progress", completed=i, total=num_games)
    
    # Write results to CSV
    write_results_csv(results, output_path)
    
    logger.log(
        "simulation_complete",
        num_games=num_games,
        output=str(output_path)
    )
    
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write game results to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'game_id', 'specialization_index', 'retrieval_efficiency',
            'context_condition', 'agent_count', 'token_limit', 'success', 'error_message'
        ])
        
        for r in results:
            writer.writerow([
                r.game_id,
                f"{r.specialization_index:.6f}",
                f"{r.retrieval_efficiency:.6f}",
                r.context_condition,
                r.agent_count,
                r.token_limit if r.token_limit else "None",
                r.success,
                r.error_message if r.error_message else ""
            ])


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the experiment."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Networks experiment"
    )
    
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition: full or limited"
    )
    
    parser.add_argument(
        "--agents",
        type=parse_agents_arg,
        default="5",
        help="Number of agents (single number or comma-separated list)"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate per configuration"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="synthetic",
        help="Dataset name (default: synthetic fallback)"
    )
    
    parser.add_argument(
        "--token-limit",
        type=int,
        default=256,
        help="Token limit for limited context condition"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated based on config)"
    )
    
    return parser


def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    logger.log("experiment_start", args=vars(args))
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        suffix = "limited" if args.context == "limited" else "full"
        output_path = Path(f"projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_{suffix}.csv")
    
    # Handle single agent count or multiple
    agent_counts = args.agents if isinstance(args.agents, list) else [args.agents]
    
    for agent_count in agent_counts:
        config = GameConfig(
            num_agents=agent_count,
            context_condition=args.context,
            token_limit=args.token_limit if args.context == "limited" else None,
            seed=args.seed,
            dataset_name=args.dataset,
            max_turns=20
        )
        
        run_simulation(
            num_games=args.games,
            config=config,
            output_path=output_path
        )
    
    logger.log("experiment_complete", output=str(output_path))


if __name__ == "__main__":
    main()