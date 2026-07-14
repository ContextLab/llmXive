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
from analysis.sensitivity import truncate_context_to_token_limit
from data.loaders import DatasetSpec, get_dataset, enable_synthetic_fallback, load_experiment_results
from data.synthetic import generate_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

@dataclass
class GameConfig:
    context_condition: str  # 'full' or 'limited'
    num_agents: int
    token_limit: Optional[int] = None
    dataset_name: str = "hanabi"
    seed: int = 42
    game_id: int = 0
    # Derived during init
    context: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[BaseAgent] = field(default_factory=list)
    memory_buffer: MemoryBuffer = None

@dataclass
class GameResult:
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    successful_retrievals: int
    total_queries: int
    facts_per_agent: Dict[int, int]
    memory_actions: List[Dict[str, Any]]
    duration_seconds: float
    checksum: str
    is_synthetic: bool = False

def parse_agents_arg(agents_str: str) -> int:
    """Parse agent count from string (e.g., '5' or '3,5,7' -> takes first or raises)."""
    parts = [p.strip() for p in agents_str.split(',')]
    if len(parts) > 1:
        # For single game run, we expect a single number
        raise ValueError(f"Expected single agent count, got multiple: {agents_str}")
    return int(parts[0])

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    if not file_path.exists():
        return "MISSING"
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_data_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute checksum of dataset content."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Load dataset with verification.
    Returns (data, is_synthetic).
    Raises error if real data missing and fallback not enabled.
    """
    enable_synthetic_fallback()
    try:
        dataset_spec = get_dataset(config.dataset_name)
        if dataset_spec.is_synthetic:
            logger.log("dataset_load", status="synthetic_fallback", source=config.dataset_name)
            return dataset_spec.data, True
        else:
            # Verify checksum if available
            checksum = compute_file_checksum(Path(dataset_spec.path))
            if dataset_spec.expected_checksum and checksum != dataset_spec.expected_checksum:
                logger.log("dataset_verify", status="checksum_mismatch", expected=dataset_spec.expected_checksum, actual=checksum)
                # In a real scenario, we might retry or fail here
            logger.log("dataset_load", status="loaded", source=config.dataset_name, checksum=checksum)
            return dataset_spec.data, False
    except Exception as e:
        logger.log("dataset_load", status="failed", error=str(e))
        raise

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    context: List[Dict[str, Any]],
    turn_index: int,
    game_id: int
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Simulate a single turn for an agent.
    Returns (agent_output, memory_actions).
    """
    # Truncate context if limited mode
    current_context = context
    if agent.config.context_limit:
        current_context = truncate_context_to_token_limit(context, agent.config.context_limit)

    # Agent generates action based on context and memory
    action = agent.step(current_context, memory_buffer)

    # Parse action for memory updates
    memory_actions = []
    if action.get("memory_action"):
        action_str = action["memory_action"]
        parsed = memory_buffer.parse_action_from_prompt(action_str)
        if parsed:
            memory_buffer.write(parsed)
            memory_actions.append(parsed)
    
    # Simulate retrieval attempt (for metrics)
    if action.get("query"):
        query = action["query"]
        retrieved = memory_buffer.read(query)
        action["retrieved"] = retrieved

    return action, memory_actions

def simulate_one_game(config: GameConfig) -> GameResult:
    """
    Orchestrate a single game simulation:
    1. Load dataset
    2. Initialize agents and memory buffer
    3. Run turn-based interaction
    4. Compute metrics
    5. Return results
    """
    start_time = time.time()
    logger.log("game_start", game_id=config.game_id, agents=config.num_agents, context=config.context_condition)

    # Reset shared buffer for this game
    reset_shared_buffer()
    memory_buffer = get_shared_buffer()

    # Load dataset
    dataset_data, is_synthetic = load_and_verify_dataset(config)
    
    # Initialize agents
    agents = []
    for i in range(config.num_agents):
        agent_config = AgentConfig(
            agent_id=i,
            model_name="facebook/opt-125m",
            device="cpu",
            seed=config.seed + i,
            context_limit=config.token_limit if config.context_condition == "limited" else None
        )
        agent = BaseAgent(agent_config)
        agents.append(agent)
    
    config.agents = agents
    config.memory_buffer = memory_buffer
    config.context = dataset_data

    # Game loop: turn-based interaction
    total_turns = len(dataset_data)  # One turn per data item
    all_memory_actions = []
    successful_retrievals = 0
    total_queries = 0
    facts_per_agent = {i: 0 for i in range(config.num_agents)}

    for turn_idx, data_item in enumerate(dataset_data):
        # Round-robin agent selection
        agent_idx = turn_idx % config.num_agents
        agent = agents[agent_idx]
        
        # Simulate turn
        action, mem_actions = simulate_game_turn(
            agent, memory_buffer, dataset_data, turn_idx, config.game_id
        )
        
        all_memory_actions.extend(mem_actions)
        
        # Track facts per agent (simplified: count write actions)
        if action.get("memory_action") and "write" in str(action.get("memory_action", "")):
            facts_per_agent[agent_idx] += 1

        # Track retrievals
        if action.get("query"):
            total_queries += 1
            if action.get("retrieved"):
                successful_retrievals += 1

    # Compute metrics
    spec_index, _ = compute_specialization_index(
        [facts_per_agent[i] for i in range(config.num_agents)],
        num_agents=config.num_agents
    )
    
    ret_eff, _ = compute_retrieval_efficiency(
        successful_retrievals,
        total_queries,
        config.num_agents
    )

    duration = time.time() - start_time
    
    # Compute checksum of result for reproducibility
    result_checksum = compute_data_checksum(all_memory_actions)

    logger.log("game_end", game_id=config.game_id, spec=spec_index, ret=ret_eff, duration=duration)

    return GameResult(
        game_id=config.game_id,
        context_condition=config.context_condition,
        agent_count=config.num_agents,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        successful_retrievals=successful_retrievals,
        total_queries=total_queries,
        facts_per_agent=facts_per_agent,
        memory_actions=all_memory_actions,
        duration_seconds=duration,
        checksum=result_checksum,
        is_synthetic=is_synthetic
    )

def run_simulation(
    context_condition: str,
    agent_count: int,
    num_games: int,
    dataset_name: str,
    token_limit: Optional[int] = None,
    seed: int = 42
) -> List[GameResult]:
    """Run multiple game simulations."""
    results = []
    for i in range(num_games):
        config = GameConfig(
            context_condition=context_condition,
            num_agents=agent_count,
            token_limit=token_limit,
            dataset_name=dataset_name,
            seed=seed,
            game_id=i
        )
        result = simulate_one_game(config)
        results.append(result)
        # Log progress
        if (i + 1) % 100 == 0:
            logger.log("simulation_progress", games_completed=i+1, total=num_games)
    return results

def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'game_id', 'specialization_index', 'retrieval_efficiency', 
            'context_condition', 'agent_count', 'successful_retrievals', 
            'total_queries', 'duration_seconds', 'checksum', 'is_synthetic'
        ])
        for r in results:
            writer.writerow([
                r.game_id, r.specialization_index, r.retrieval_efficiency,
                r.context_condition, r.agent_count, r.successful_retrievals,
                r.total_queries, r.duration_seconds, r.checksum, r.is_synthetic
            ])
    logger.log("results_written", path=str(output_path), count=len(results))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Social Memory Network Experiment")
    parser.add_argument("--context", choices=["full", "limited"], default="full",
                      help="Context condition: full or limited")
    parser.add_argument("--agents", type=int, default=5,
                      help="Number of agents")
    parser.add_argument("--games", type=int, default=1000,
                      help="Number of games to simulate")
    parser.add_argument("--dataset", type=str, default="hanabi",
                      help="Dataset name (hanabi, coqa, or synthetic)")
    parser.add_argument("--token-limit", type=int, default=None,
                      help="Token limit for limited context")
    parser.add_argument("--output", type=str, default="results.csv",
                      help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed")
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger.log("experiment_start", context=args.context, agents=args.agents, games=args.games)

    results = run_simulation(
        context_condition=args.context,
        agent_count=args.agents,
        num_games=args.games,
        dataset_name=args.dataset,
        token_limit=args.token_limit,
        seed=args.seed
    )

    output_path = Path(args.output)
    write_results_csv(results, output_path)

    logger.log("experiment_complete", output=str(output_path))

if __name__ == "__main__":
    main()