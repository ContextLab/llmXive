"""
Main experiment runner for Social Memory Networks.
Orchestrates simulations across varying agent counts for scaling analysis (US-3).
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
from typing import Any, Dict, List, Optional, Tuple, Union

# Import from existing project modules
from agent.base_agent import AgentConfig, BaseAgent
from analysis.sensitivity import truncate_context_to_token_limit
from data.loaders import load_experiment_results, verify_datasets, DatasetLoader
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.retrieval import compute_retrieval_efficiency
from metrics.specialization import compute_specialization_index
from metrics.validator import validate_single_game_metrics, ValidationResult
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

# Default configuration
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cpu"
DEFAULT_MODEL_NAME = "facebook/opt-125m"
DEFAULT_NUM_AGENTS = 5
DEFAULT_GAMES = 1000
DEFAULT_DATASET = "hanabi"

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    dataset: str = DEFAULT_DATASET
    seed: int = DEFAULT_SEED
    game_id: str = ""
    model_name: str = DEFAULT_MODEL_NAME
    device: str = DEFAULT_DEVICE

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: str
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    validation_status: str
    metrics_details: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7' or '5')."""
    try:
        return [int(x.strip()) for x in agents_str.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agent count format: {agents_str}")

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_data_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute checksum of dataset content for reproducibility."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict[str, Any]], str]:
    """
    Load dataset with verification and synthetic fallback.
    Returns (data, checksum).
    """
    logger.log("load_dataset", dataset=config.dataset, condition=config.context_condition)
    
    # Verify datasets against whitelist
    try:
        verify_datasets([config.dataset])
    except ValueError as e:
        logger.log("dataset_verification_failed", error=str(e))
        # Trigger synthetic fallback
        logger.log("triggering_synthetic_fallback", reason="dataset_not_verified")
        synthetic_data = generate_synthetic_dataset(
            num_samples=100,
            seed=config.seed,
            dataset_type=config.dataset
        )
        checksum = compute_data_checksum(synthetic_data)
        return synthetic_data, checksum

    # Attempt to load real dataset
    loader = DatasetLoader()
    try:
        data = loader.load(config.dataset)
        checksum = compute_data_checksum(data)
        logger.log("dataset_loaded", count=len(data), checksum=checksum[:8])
        return data, checksum
    except Exception as e:
        logger.log("real_dataset_load_failed", error=str(e))
        # Fallback to synthetic
        synthetic_data = generate_synthetic_dataset(
            num_samples=100,
            seed=config.seed,
            dataset_type=config.dataset
        )
        checksum = compute_data_checksum(synthetic_data)
        return synthetic_data, checksum

def truncate_context(context: str, token_limit: int) -> str:
    """Truncate context to token limit (simple word-based approximation)."""
    if token_limit is None:
        return context
    
    words = context.split()
    if len(words) <= token_limit:
        return context
    
    truncated = " ".join(words[:token_limit]) + "..."
    logger.log("context_truncated", original_len=len(words), new_len=token_limit)
    return truncated

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    current_context: str,
    game_id: str,
    turn: int
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Simulate a single turn for an agent.
    Returns (response, memory_actions).
    """
    # Prepare prompt with context
    prompt = f"[Game: {game_id}, Turn: {turn}]\nContext: {current_context}\nAgent Response:"
    
    # Truncate if needed
    if agent.config.token_limit:
        prompt = truncate_context(prompt, agent.config.token_limit)
    
    # Get response from agent (CPU-only, no CUDA)
    try:
        response = agent.generate(prompt)
    except Exception as e:
        logger.log("agent_generation_failed", error=str(e))
        response = f"[Error: {str(e)}]"
    
    # Parse memory actions from response
    memory_actions = []
    if "<MEMORY_ACTION>" in response:
        # Simple parsing for demonstration
        import re
        pattern = r"<MEMORY_ACTION>(.*?)</MEMORY_ACTION>"
        matches = re.findall(pattern, response, re.DOTALL)
        for match in matches:
            try:
                action_data = json.loads(match)
                memory_actions.append(action_data)
            except json.JSONDecodeError:
                logger.log("memory_action_parse_failed", content=match[:50])
    
    return response, memory_actions

def simulate_one_game(config: GameConfig) -> GameResult:
    """
    Simulate a single game with N agents and return metrics.
    This is the core simulation loop for scaling analysis.
    """
    logger.log("start_game", game_id=config.game_id, agents=config.num_agents, 
              condition=config.context_condition)
    
    # Reset shared memory buffer
    reset_shared_buffer()
    memory_buffer = get_shared_buffer()
    
    # Load dataset
    dataset, data_checksum = load_and_verify_dataset(config)
    
    # Initialize agents
    agents = []
    for i in range(config.num_agents):
        agent_config = AgentConfig(
            name=f"agent_{i}",
            model_name=config.model_name,
            device=config.device,
            seed=config.seed + i,
            token_limit=config.token_limit
        )
        agent = BaseAgent(agent_config)
        agents.append(agent)
    
    # Game state
    facts_contributed = {i: [] for i in range(config.num_agents)}
    successful_retrievals = 0
    total_queries = 0
    
    # Simulate turns (simplified for CPU feasibility)
    num_turns = min(10, len(dataset))  # Limit turns for CPU feasibility
    for turn in range(num_turns):
        if turn >= len(dataset):
            break
            
        current_item = dataset[turn]
        context_span = current_item.get("context", f"Fact {turn}")
        
        # Distribute to agents in round-robin
        agent_idx = turn % config.num_agents
        agent = agents[agent_idx]
        
        # Agent processes context
        response, actions = simulate_game_turn(
            agent, memory_buffer, context_span, config.game_id, turn
        )
        
        # Record fact contribution
        facts_contributed[agent_idx].append({
            "turn": turn,
            "content": context_span,
            "response": response[:100]  # Truncate for storage
        })
        
        # Process memory actions
        for action in actions:
            memory_buffer.write(action.get("key", f"key_{turn}_{agent_idx}"), 
                              action.get("value", response))
        
        # Simulate retrieval attempts (every 3 turns)
        if turn > 0 and turn % 3 == 0:
            total_queries += 1
            # Try to retrieve from memory
            query_key = f"key_{turn-1}_{(agent_idx-1) % config.num_agents}"
            retrieved = memory_buffer.read(query_key)
            if retrieved is not None:
                successful_retrievals += 1
    
    # Compute metrics
    facts_list = [
        {"agent_id": k, "facts": v} for k, v in facts_contributed.items()
    ]
    
    try:
        spec_index, spec_details = compute_specialization_index(
            facts_list, num_agents=config.num_agents
        )
    except Exception as e:
        logger.log("specialization_compute_failed", error=str(e))
        spec_index = 0.0
        spec_details = {}
    
    try:
        ret_eff, ret_details = compute_retrieval_efficiency(
            successful_retrievals, total_queries, config.num_agents
        )
    except Exception as e:
        logger.log("retrieval_compute_failed", error=str(e))
        ret_eff = 0.0
        ret_details = {}
    
    # Validate results
    validation = validate_single_game_metrics(
        spec_index, ret_eff, config.num_agents
    )
    
    result = GameResult(
        game_id=config.game_id,
        context_condition=config.context_condition,
        agent_count=config.num_agents,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        validation_status=validation.status,
        metrics_details={
            "specialization": spec_details,
            "retrieval": ret_details,
            "data_checksum": data_checksum
        },
        is_valid=validation.is_valid
    )
    
    logger.log("game_complete", 
              game_id=config.game_id,
              specialization=spec_index,
              retrieval=ret_eff,
              valid=validation.is_valid)
    
    return result

def run_simulation(
    agent_counts: List[int],
    context_condition: str,
    games_per_count: int,
    dataset: str,
    seed: int,
    output_path: Path
) -> List[GameResult]:
    """
    Run simulation for multiple agent counts (US-3 scaling analysis).
    """
    all_results = []
    
    for agent_count in agent_counts:
        logger.log("starting_agent_batch", agent_count=agent_count, 
                  games=games_per_count, condition=context_condition)
        
        for game_idx in range(games_per_count):
            game_id = f"{context_condition}_agents{agent_count}_game{game_idx}_{seed}"
            
            config = GameConfig(
                num_agents=agent_count,
                context_condition=context_condition,
                dataset=dataset,
                seed=seed,
                game_id=game_id,
                device=DEFAULT_DEVICE,
                model_name=DEFAULT_MODEL_NAME
            )
            
            result = simulate_one_game(config)
            all_results.append(result)
            
            # Progress logging
            if (game_idx + 1) % 10 == 0:
                logger.log("progress", 
                          agent_count=agent_count,
                          completed=game_idx + 1,
                          total=games_per_count)
    
    return all_results

def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "game_id", "context_condition", "agent_count",
            "specialization_index", "retrieval_efficiency",
            "validation_status", "is_valid"
        ])
        
        for r in results:
            writer.writerow([
                r.game_id, r.context_condition, r.agent_count,
                f"{r.specialization_index:.6f}", f"{r.retrieval_efficiency:.6f}",
                r.validation_status, r.is_valid
            ])
    
    logger.log("results_written", path=str(output_path), count=len(results))

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Networks experiment with scaling analysis"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: full or limited"
    )
    
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent counts (comma-separated, e.g., '3,5,7' for scaling)"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games per agent count"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default=DEFAULT_DATASET,
        choices=["hanabi", "coqa", "synthetic"],
        help="Dataset to use"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_results.csv",
        help="Output CSV path"
    )
    
    parser.add_argument(
        "--token-limit",
        type=int,
        default=None,
        help="Token limit for limited context (default: no limit)"
    )
    
    return parser

def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agent counts
    agent_counts = parse_agents_arg(args.agents)
    
    # Setup output path
    output_path = Path(args.output)
    
    logger.log("experiment_start", 
              agent_counts=agent_counts,
              games_per_count=args.games,
              context=args.context,
              dataset=args.dataset)
    
    # Run simulation
    results = run_simulation(
        agent_counts=agent_counts,
        context_condition=args.context,
        games_per_count=args.games,
        dataset=args.dataset,
        seed=args.seed,
        output_path=output_path
    )
    
    # Write results
    write_results_csv(results, output_path)
    
    # Summary
    valid_count = sum(1 for r in results if r.is_valid)
    logger.log("experiment_complete", 
              total=len(results),
              valid=valid_count,
              output=str(output_path))
    
    print(f"Experiment complete. Results written to {output_path}")
    print(f"Total games: {len(results)}, Valid: {valid_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())