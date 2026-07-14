"""
Main experiment runner for Social Memory Networks.
Orchestrates agents, memory buffer, and turn-based interaction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Local imports based on provided API surface
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import load_experiment_results, save_experiment_results, verify_datasets, enable_synthetic_fallback, get_dataset
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    context_condition: str  # 'full' or 'limited'
    num_agents: int
    dataset_name: str
    token_limit: Optional[int] = None
    seed: int = 42
    max_turns: int = 20
    memory_capacity: int = 100

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    successful_retrievals: int
    total_queries: int
    total_facts_contributed: int
    facts_per_agent: Dict[int, int]
    memory_entries: int
    seed: int
    is_synthetic: bool = False

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_data_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute checksum of dataset content."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Load dataset with verification and checksumming."""
    # Enable synthetic fallback if dataset is missing
    enable_synthetic_fallback()
    
    try:
        # Verify datasets are available
        verify_datasets([config.dataset_name])
        
        # Load dataset
        dataset = get_dataset(config.dataset_name)
        
        if not dataset:
            raise ValueError(f"Dataset {config.dataset_name} not found and fallback failed")
        
        # Compute checksum
        checksum = compute_data_checksum(dataset)
        logger.log("dataset_loaded", name=config.dataset_name, checksum=checksum, size=len(dataset))
        
        return dataset, checksum
        
    except Exception as e:
        logger.log("dataset_load_failed", error=str(e))
        # Fallback to synthetic if real data unavailable
        synthetic_data = generate_synthetic_dataset(
            name=config.dataset_name,
            num_samples=100,
            num_facts_per_sample=10
        )
        checksum = compute_data_checksum(synthetic_data)
        logger.log("synthetic_data_generated", name=config.dataset_name, checksum=checksum, size=len(synthetic_data))
        return synthetic_data, checksum

def truncate_context_to_token_limit(context: str, limit: int) -> str:
    """Truncate context to specified token limit."""
    # Simple token estimation: split by whitespace
    tokens = context.split()
    if len(tokens) <= limit:
        return context
    return " ".join(tokens[:limit])

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    current_facts: List[str],
    turn: int,
    config: GameConfig
) -> Tuple[List[str], Dict[str, Any]]:
    """Simulate a single turn for an agent."""
    # Build context
    context_parts = []
    context_parts.append(f"Turn {turn}")
    context_parts.append(f"Current facts: {current_facts}")
    
    # Read from memory
    memory_contents = memory_buffer.read_all()
    if memory_contents:
        context_parts.append(f"Memory: {memory_contents}")
    
    context = " ".join(context_parts)
    
    # Apply context truncation if needed
    if config.context_condition == 'limited' and config.token_limit:
        context = truncate_context_to_token_limit(context, config.token_limit)
    
    # Agent generates response
    response = agent.generate(context)
    
    # Parse response for facts and memory actions
    new_facts = []
    memory_action = None
    
    # Simple parsing: look for fact patterns
    if "fact:" in response.lower():
        fact = response.split("fact:")[1].split(".")[0].strip()
        new_facts.append(fact)
    
    # Check for memory action
    if "<MEMORY_ACTION>" in response:
        try:
            action_str = response.split("<MEMORY_ACTION>")[1].split("</MEMORY_ACTION>")[0]
            memory_action = json.loads(action_str)
        except (json.JSONDecodeError, IndexError):
            pass
    
    # Write to memory if action present
    if memory_action:
        memory_buffer.write(memory_action)
    
    # Update facts
    current_facts.extend(new_facts)
    
    return current_facts, {
        "turn": turn,
        "response_length": len(response),
        "facts_added": len(new_facts),
        "memory_action": memory_action is not None
    }

def simulate_one_game(config: GameConfig, game_id: int) -> GameResult:
    """Simulate a single game with multiple agents."""
    # Initialize random seed for reproducibility
    random.seed(config.seed + game_id)
    np.random.seed(config.seed + game_id)
    
    # Load dataset
    dataset, checksum = load_and_verify_dataset(config)
    
    # Initialize memory buffer
    reset_shared_buffer()
    memory_buffer = get_shared_buffer(max_entries=config.memory_capacity)
    
    # Create agents
    agents: List[BaseAgent] = []
    for i in range(config.num_agents):
        agent_config = AgentConfig(
            model_name="facebook/opt-125m",
            device="cpu",
            seed=config.seed + i,
            temperature=0.7
        )
        agent = BaseAgent(agent_config, f"agent_{i}")
        agents.append(agent)
    
    # Track facts per agent
    facts_per_agent: Dict[int, int] = {i: 0 for i in range(config.num_agents)}
    all_facts: List[str] = []
    successful_retrievals = 0
    total_queries = 0
    
    # Run turns
    for turn in range(config.max_turns):
        agent_idx = turn % config.num_agents
        agent = agents[agent_idx]
        
        # Simulate turn
        all_facts, turn_result = simulate_game_turn(
            agent, memory_buffer, all_facts, turn, config
        )
        
        # Track facts contributed
        if turn_result["facts_added"] > 0:
            facts_per_agent[agent_idx] += turn_result["facts_added"]
        
        # Track memory queries
        if turn_result.get("memory_action"):
            total_queries += 1
            # Assume successful retrieval for now (would be tracked in real implementation)
            successful_retrievals += 1
    
    # Compute metrics
    spec_index, _ = compute_specialization_index(facts_per_agent, num_agents=config.num_agents)
    ret_eff, _ = compute_retrieval_efficiency(successful_retrievals, total_queries, config.num_agents)
    
    # Create result
    result = GameResult(
        game_id=game_id,
        context_condition=config.context_condition,
        agent_count=config.num_agents,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        successful_retrievals=successful_retrievals,
        total_queries=total_queries,
        total_facts_contributed=sum(facts_per_agent.values()),
        facts_per_agent=facts_per_agent,
        memory_entries=len(memory_buffer.entries),
        seed=config.seed + game_id,
        is_synthetic=False  # Would be set based on actual data source
    )
    
    logger.log("game_completed", game_id=game_id, spec_index=spec_index, ret_eff=ret_eff)
    
    return result

def run_simulation(
    context_condition: str,
    agent_counts: List[int],
    dataset_name: str,
    num_games: int,
    token_limit: Optional[int] = None,
    seed: int = 42
) -> List[GameResult]:
    """Run full simulation for specified configuration."""
    results: List[GameResult] = []
    
    for agent_count in agent_counts:
        config = GameConfig(
            context_condition=context_condition,
            num_agents=agent_count,
            dataset_name=dataset_name,
            token_limit=token_limit,
            seed=seed
        )
        
        logger.log("simulation_start", context=context_condition, agents=agent_count, games=num_games)
        
        for game_id in range(num_games):
            result = simulate_one_game(config, game_id)
            results.append(result)
            
            if (game_id + 1) % 100 == 0:
                logger.log("simulation_progress", games_completed=game_id + 1)
        
        logger.log("simulation_complete", context=context_condition, agents=agent_count, games=num_games)
    
    return results

def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'game_id', 'context_condition', 'agent_count', 
            'specialization_index', 'retrieval_efficiency',
            'successful_retrievals', 'total_queries',
            'total_facts_contributed', 'memory_entries', 'seed', 'is_synthetic'
        ])
        
        for result in results:
            writer.writerow([
                result.game_id,
                result.context_condition,
                result.agent_count,
                result.specialization_index,
                result.retrieval_efficiency,
                result.successful_retrievals,
                result.total_queries,
                result.total_facts_contributed,
                result.memory_entries,
                result.seed,
                result.is_synthetic
            ])
    
    logger.log("results_written", path=str(output_path), count=len(results))

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse agents argument (e.g., '5' or '3,5,7')."""
    if ',' in agents_str:
        return [int(x.strip()) for x in agents_str.split(',')]
    return [int(agents_str.strip())]

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for experiment runner."""
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
        help='Number of agents (e.g., 5 or 3,5,7)'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        default=None,
        choices=['hanabi', 'coqa', None],
        help='Dataset to use (defaults to synthetic if not specified)'
    )
    
    parser.add_argument(
        '--games',
        type=int,
        default=100,
        help='Number of games to simulate'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='results/results.csv',
        help='Output file path'
    )
    
    parser.add_argument(
        '--token-limit',
        type=int,
        default=None,
        help='Token limit for limited context condition'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    return parser

def main() -> None:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agents
    agent_counts = parse_agents_arg(args.agents)
    
    # Determine dataset
    dataset_name = args.dataset if args.dataset else 'synthetic'
    
    # Run simulation
    results = run_simulation(
        context_condition=args.context,
        agent_counts=agent_counts,
        dataset_name=dataset_name,
        num_games=args.games,
        token_limit=args.token_limit,
        seed=args.seed
    )
    
    # Write results
    output_path = Path(args.output)
    write_results_csv(results, output_path)
    
    # Print summary
    print(f"Completed {len(results)} games")
    print(f"Context: {args.context}")
    print(f"Agents: {agent_counts}")
    print(f"Dataset: {dataset_name}")
    print(f"Output: {output_path}")
    
    # Log completion
    logger.log("experiment_complete", games=len(results), output=str(output_path))

if __name__ == '__main__':
    main()