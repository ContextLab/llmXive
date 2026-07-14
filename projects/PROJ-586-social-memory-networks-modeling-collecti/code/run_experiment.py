"""
Main experiment runner for Social Memory Networks.
Orchestrates agents, memory buffer, and turn-based interaction for game simulation.
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

# Local imports based on API surface
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import get_dataset, enable_synthetic_fallback, verify_datasets
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index, SpecializationMetrics
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics
from metrics.validator import validate_single_game_metrics, ValidationResult
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    dataset_name: str = "synthetic"
    seed: int = 42
    max_turns: int = 50

@dataclass
class GameResult:
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    total_turns: int
    success: bool
    error_message: Optional[str] = None

def parse_agents_arg(agents_str: str) -> int:
    """Parse agents argument (single int or comma-separated list for scaling)."""
    parts = [int(x.strip()) for x in agents_str.split(',')]
    if len(parts) == 1:
        return parts[0]
    # For scaling analysis, return the first one for single game run,
    # or handle as list in the main runner
    return parts[0]

def count_tokens(text: str) -> int:
    """Simple token count approximation (split by whitespace)."""
    return len(text.split())

def truncate_context_to_token_limit(text: str, limit: int) -> str:
    """Truncate text to a token limit."""
    tokens = text.split()
    if len(tokens) <= limit:
        return text
    return ' '.join(tokens[:limit])

def compute_checksum(data: str) -> str:
    """Compute SHA256 checksum of data string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict[str, Any]], str]:
    """
    Load dataset with verification and synthetic fallback.
    Returns (data_list, checksum).
    """
    enable_synthetic_fallback()
    
    # Verify datasets
    try:
        verify_datasets()
    except Exception as e:
        logger.log("dataset_verification_failed", error=str(e))
        # Fallback will be triggered by get_dataset

    # Load dataset
    dataset_data = get_dataset(config.dataset_name)
    
    if not dataset_data:
        # Generate synthetic if empty
        logger.log("generating_synthetic_dataset", agents=config.num_agents)
        synthetic_spec = {
            'num_facts': config.num_agents * 10,
            'num_agents': config.num_agents,
            'max_turns': config.max_turns
        }
        dataset_data = generate_synthetic_dataset(synthetic_spec)
        if dataset_data:
            # Save for reproducibility
            save_synthetic_dataset(dataset_data, f"data/synthetic_{config.dataset_name}.json")

    # Compute checksum
    data_str = json.dumps(dataset_data, sort_keys=True)
    checksum = compute_checksum(data_str)
    
    logger.log("dataset_loaded", 
              dataset=config.dataset_name, 
              records=len(dataset_data), 
              checksum=checksum[:16])
    
    return dataset_data, checksum

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    turn_data: Dict[str, Any],
    context_condition: str,
    token_limit: Optional[int] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Simulate a single turn for an agent.
    Returns (agent_response, memory_actions).
    """
    # Prepare context
    context_parts = []
    
    # Add turn data
    context_parts.append(f"Turn: {turn_data.get('turn_number', 0)}")
    context_parts.append(f"Fact: {turn_data.get('fact', 'N/A')}")
    
    # Read from memory buffer
    recent_entries = list(memory_buffer.read_recent(5))
    if recent_entries:
        context_parts.append("Memory Context:")
        for entry in recent_entries:
            context_parts.append(f"  - {entry.get('value', '')}")
    
    full_context = '\n'.join(context_parts)
    
    # Apply context window truncation if limited
    if context_condition == 'limited' and token_limit:
        full_context = truncate_context_to_token_limit(full_context, token_limit)
    
    # Agent processes context
    response, actions = agent.step(full_context, turn_data)
    
    return response, actions

def simulate_one_game(config: GameConfig, game_id: int) -> GameResult:
    """
    Orchestrate agents, memory buffer, and turn-based interaction for a single game.
    Implements the core simulation loop for T011b.
    """
    logger.log("game_start", game_id=game_id, agents=config.num_agents)
    
    try:
        # Reset shared memory buffer for this game
        reset_shared_buffer()
        memory_buffer = get_shared_buffer()
        
        # Load dataset
        dataset_data, checksum = load_and_verify_dataset(config)
        
        if not dataset_data:
            raise ValueError("Failed to load or generate dataset")
        
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
        
        # Game state tracking
        agent_facts: Dict[int, List[str]] = {i: [] for i in range(config.num_agents)}
        successful_retrievals = 0
        total_queries = 0
        
        # Distribute facts among agents (specialization setup)
        facts = dataset_data[:config.num_agents * 10]  # Use subset
        for idx, fact in enumerate(facts):
            agent_id = idx % config.num_agents
            agent_facts[agent_id].append(fact.get('fact_text', str(fact)))
        
        # Simulation loop
        max_turns = min(config.max_turns, len(facts) * 2)
        actual_turns = 0
        
        for turn in range(max_turns):
            actual_turns = turn + 1
            turn_data = {
                'turn_number': turn,
                'fact': facts[turn % len(facts)] if facts else {}
            }
            
            # Each agent takes a turn
            for agent_idx, agent in enumerate(agents):
                # Agent queries memory
                query = f"Retrieve facts about {turn_data['fact'].get('topic', 'unknown')}"
                total_queries += 1
                
                # Attempt retrieval from buffer
                retrieved = memory_buffer.read(query)
                if retrieved:
                    successful_retrievals += 1
                
                # Agent processes turn
                response, actions = simulate_game_turn(
                    agent, 
                    memory_buffer, 
                    turn_data,
                    config.context_condition,
                    config.token_limit
                )
                
                # Process memory actions
                for action in actions:
                    if action.get('type') == 'write':
                        memory_buffer.write(
                            key=action.get('key', f"fact_{turn}_{agent_idx}"),
                            value=action.get('value', response)
                        )
                
                # Track facts known by this agent
                if response and len(response) > 10:
                    agent_facts[agent_idx].append(response[:100])  # Truncate for storage
            
            # Early termination if memory is saturated
            if memory_buffer.size() > 1000:
                break
        
        # Compute metrics
        facts_per_agent = [len(agent_facts[i]) for i in range(config.num_agents)]
        
        spec_index, spec_metrics = compute_specialization_index(
            facts_per_agent, 
            num_agents=config.num_agents
        )
        
        ret_eff, ret_metrics = compute_retrieval_efficiency(
            successful_retrievals,
            total_queries,
            config.num_agents
        )
        
        # Validate metrics
        validation = validate_single_game_metrics(
            specialization=spec_index,
            retrieval=ret_eff,
            agent_count=config.num_agents
        )
        
        if not validation.is_valid:
            logger.log("game_validation_failed", 
                      game_id=game_id,
                      errors=validation.errors)
        
        logger.log("game_complete", 
                  game_id=game_id,
                  spec_index=spec_index,
                  ret_eff=ret_eff,
                  turns=actual_turns)
        
        return GameResult(
            game_id=game_id,
            specialization_index=spec_index,
            retrieval_efficiency=ret_eff,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            total_turns=actual_turns,
            success=True
        )
        
    except Exception as e:
        logger.log("game_error", game_id=game_id, error=str(e))
        return GameResult(
            game_id=game_id,
            specialization_index=0.0,
            retrieval_efficiency=0.0,
            context_condition=config.context_condition,
            agent_count=config.num_agents,
            total_turns=0,
            success=False,
            error_message=str(e)
        )

def write_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write game results to CSV file."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['game_id', 'specialization_index', 'retrieval_efficiency', 
                       'context_condition', 'agent_count', 'total_turns', 'success'])
        
        for r in results:
            writer.writerow([
                r.game_id,
                f"{r.specialization_index:.6f}",
                f"{r.retrieval_efficiency:.6f}",
                r.context_condition,
                r.agent_count,
                r.total_turns,
                r.success
            ])
    
    logger.log("results_written", path=output_path, count=len(results))

def run_simulation(config: GameConfig, num_games: int) -> List[GameResult]:
    """Run multiple game simulations."""
    results = []
    
    logger.log("simulation_start", 
              num_games=num_games, 
              agents=config.num_agents,
              context=config.context_condition)
    
    for game_id in range(num_games):
        result = simulate_one_game(config, game_id)
        results.append(result)
        
        # Progress logging
        if (game_id + 1) % 100 == 0:
            logger.log("simulation_progress", 
                      completed=game_id + 1, 
                      total=num_games)
    
    # Summary statistics
    successful = sum(1 for r in results if r.success)
    avg_spec = sum(r.specialization_index for r in results) / len(results) if results else 0
    avg_ret = sum(r.retrieval_efficiency for r in results) / len(results) if results else 0
    
    logger.log("simulation_complete",
              total=num_games,
              successful=successful,
              avg_specialization=avg_spec,
              avg_retrieval=avg_ret)
    
    return results

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the experiment."""
    parser = argparse.ArgumentParser(description='Social Memory Networks Experiment')
    
    parser.add_argument('--context', 
                      choices=['full', 'limited'], 
                      default='full',
                      help='Context condition: full or limited')
    
    parser.add_argument('--agents', 
                      type=str, 
                      default='5',
                      help='Number of agents (single int or comma-separated list for scaling)')
    
    parser.add_argument('--dataset', 
                      type=str, 
                      default='synthetic',
                      choices=['hanabi', 'coqa', 'synthetic'],
                      help='Dataset to use')
    
    parser.add_argument('--games', 
                      type=int, 
                      default=1000,
                      help='Number of games to simulate')
    
    parser.add_argument('--output', 
                      type=str, 
                      default='results/results.csv',
                      help='Output CSV file path')
    
    parser.add_argument('--seed', 
                      type=int, 
                      default=42,
                      help='Random seed')
    
    parser.add_argument('--token-limit', 
                      type=int, 
                      default=None,
                      help='Token limit for limited context')
    
    return parser

def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agents
    agent_counts = [int(x) for x in args.agents.split(',')]
    
    # Handle single agent count vs scaling
    if len(agent_counts) == 1:
        agent_counts = agent_counts
    else:
        # For scaling, we would run multiple experiments
        # For now, run with the first configuration
        agent_counts = [agent_counts[0]]
    
    # Run experiments
    all_results = []
    
    for agent_count in agent_counts:
        config = GameConfig(
            num_agents=agent_count,
            context_condition=args.context,
            token_limit=args.token_limit if args.context == 'limited' else None,
            dataset_name=args.dataset,
            seed=args.seed,
            max_turns=50
        )
        
        results = run_simulation(config, args.games)
        all_results.extend(results)
        
        # Write results for this configuration
        output_suffix = f"_{agent_count}agents" if len(agent_counts) > 1 else ""
        output_path = args.output.replace('.csv', f'{output_suffix}.csv')
        write_results_csv(results, output_path)
    
    # Aggregate results if multiple configurations
    if len(agent_counts) > 1:
        write_results_csv(all_results, args.output)
    
    logger.log("experiment_finished", 
              total_games=len(all_results),
              output=args.output)

    logger.log("experiment_complete", output=str(output_path))

if __name__ == "__main__":
    main()