"""
Run the social memory network experiment.

This script orchestrates the simulation of multi-agent games,
computes metrics, and outputs results to CSV files.
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

# Import from project modules
from agent.base_agent import AgentConfig, BaseAgent
from data.loaders import (
    DatasetSpec,
    enable_synthetic_fallback,
    get_dataset,
    get_dataset_spec,
    register_dataset,
    verify_datasets,
)
from data.synthetic import generate_synthetic_dataset, save_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.retrieval import compute_retrieval_efficiency
from metrics.specialization import compute_specialization_index
from metrics.validator import validate_single_game_metrics
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    dataset_name: str
    token_limit: Optional[int] = None
    dataset_name: str = "synthetic"
    seed: int = 42
    num_games: int = 1000

@dataclass
class GameResult:
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    successful_retrievals: int
    total_queries: int
    facts_per_agent: Dict[int, int]
    checksum: str
    is_synthetic: bool = False

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_dataset_with_checksum(
    dataset_name: str,
    context_condition: str,
    token_limit: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], str, bool]:
    """
    Load dataset with checksum verification.

    Returns:
        Tuple of (data_list, checksum, is_synthetic)
    """
    # Verify datasets and enable fallback if needed
    verify_datasets()
    enable_synthetic_fallback()

    is_synthetic = False
    data_list = []
    checksum = ""

    try:
        # Try to get the dataset
        dataset_spec = get_dataset_spec(dataset_name)
        if dataset_spec is None:
            # Dataset not registered, trigger synthetic fallback
            logger.log("dataset_not_found", name=dataset_name, fallback=True)
            is_synthetic = True
            # Generate synthetic dataset
            synthetic_data = generate_synthetic_dataset(
                name=dataset_name,
                num_records=100,  # Generate enough for the experiment
                is_synthetic=True
            )
            # Save synthetic data to a temp file for checksum
            temp_path = f"/tmp/synthetic_{dataset_name}.json"
            save_synthetic_dataset(synthetic_data, temp_path)
            checksum = compute_file_checksum(temp_path)
            data_list = synthetic_data
        else:
            # Dataset is registered, try to load it
            dataset = get_dataset(dataset_name)
            if dataset is None:
                # Failed to load, trigger synthetic fallback
                logger.log("dataset_load_failed", name=dataset_name, fallback=True)
                is_synthetic = True
                synthetic_data = generate_synthetic_dataset(
                    name=dataset_name,
                    num_records=100,
                    is_synthetic=True
                )
                temp_path = f"/tmp/synthetic_{dataset_name}.json"
                save_synthetic_dataset(synthetic_data, temp_path)
                checksum = compute_file_checksum(temp_path)
                data_list = synthetic_data
            else:
                # Successfully loaded from real source
                data_list = dataset
                # If it's a file path, compute checksum
                if isinstance(dataset, str) and os.path.exists(dataset):
                    checksum = compute_file_checksum(dataset)
                else:
                    # For in-memory datasets, compute a hash of the content
                    checksum = hashlib.sha256(
                        json.dumps(data_list, sort_keys=True).encode()
                    ).hexdigest()

    except Exception as e:
        logger.log("dataset_error", error=str(e), fallback=True)
        is_synthetic = True
        # Final fallback: generate synthetic data
        synthetic_data = generate_synthetic_dataset(
            name=dataset_name,
            num_records=100,
            is_synthetic=True
        )
        temp_path = f"/tmp/synthetic_{dataset_name}.json"
        save_synthetic_dataset(synthetic_data, temp_path)
        checksum = compute_file_checksum(temp_path)
        data_list = synthetic_data

    # Apply context truncation if in limited mode
    if context_condition == "limited" and token_limit is not None:
        truncated_data = []
        for record in data_list:
            truncated_record = record.copy()
            if "context" in truncated_record:
                # Simple token limit: truncate string length proportionally
                # In real implementation, this would use a tokenizer
                max_chars = token_limit * 4  # Approximate chars per token
                truncated_record["context"] = truncated_record["context"][:max_chars]
            truncated_data.append(truncated_record)
        data_list = truncated_data

    logger.log("dataset_loaded", name=dataset_name, count=len(data_list), checksum=checksum, synthetic=is_synthetic)
    return data_list, checksum, is_synthetic

def truncate_context_to_token_limit(context: str, token_limit: int) -> str:
    """Truncate context to approximate token limit."""
    # Simple approximation: 1 token ≈ 4 characters
    max_chars = token_limit * 4
    return context[:max_chars]

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    turn_data: Dict[str, Any],
    context_condition: str,
    token_limit: Optional[int] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Simulate a single turn for an agent."""
    # Prepare prompt with context
    prompt = turn_data.get("prompt", "")
    if context_condition == "limited" and token_limit:
        prompt = truncate_context_to_token_limit(prompt, token_limit)

    # Get agent response
    response = agent.generate_response(prompt)

    # Extract memory actions from response
    memory_actions = []
    if hasattr(memory_buffer, 'extract_actions'):
        memory_actions = memory_buffer.extract_actions(response)

    return response, memory_actions

def simulate_one_game(config: GameConfig, game_id: int) -> GameResult:
    """Simulate a single game with the given configuration."""
    # Reset shared memory buffer for each game
    reset_shared_buffer()
    memory_buffer = get_shared_buffer()

    # Load dataset for this game
    dataset, checksum, is_synthetic = load_dataset_with_checksum(
        config.dataset_name,
        config.context_condition,
        config.token_limit
    )

    # Create agents
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

    # Track facts per agent and retrieval statistics
    facts_per_agent = {i: 0 for i in range(config.num_agents)}
    successful_retrievals = 0
    total_queries = 0

    # Simulate game turns
    game_data = dataset[game_id % len(dataset)] if dataset else {}

    for turn_idx, turn_data in enumerate(game_data.get("turns", [])):
        # Each agent takes a turn
        for agent_idx, agent in enumerate(agents):
            response, memory_actions = simulate_game_turn(
                agent,
                memory_buffer,
                turn_data,
                config.context_condition,
                config.token_limit
            )

            # Process memory actions
            for action in memory_actions:
                if action.get("type") == "write":
                    key = action.get("key", "")
                    value = action.get("value", "")
                    memory_buffer.write(key, value)
                    facts_per_agent[agent_idx] += 1
                elif action.get("type") == "read":
                    total_queries += 1
                    key = action.get("key", "")
                    retrieved_value = memory_buffer.read(key)
                    if retrieved_value is not None:
                        successful_retrievals += 1

    # Compute metrics
    spec_idx, _ = compute_specialization_index(facts_per_agent, num_agents=config.num_agents)
    ret_eff, _ = compute_retrieval_efficiency(
        successful_retrievals,
        total_queries,
        config.num_agents
    )

    # Validate metrics
    validation = validate_single_game_metrics(spec_idx, ret_eff)
    if not validation.is_valid:
        logger.log("validation_failed", game_id=game_id, errors=validation.errors)

    return GameResult(
        game_id=game_id,
        agent_count=config.num_agents,
        context_condition=config.context_condition,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
        successful_retrievals=successful_retrievals,
        total_queries=total_queries,
        facts_per_agent=facts_per_agent,
        checksum=checksum,
        is_synthetic=is_synthetic
    )

def run_simulation(config: GameConfig) -> List[GameResult]:
    """Run the full simulation with the given configuration."""
    results = []

    # Set random seed for reproducibility
    random.seed(config.seed)

    logger.log("simulation_start", num_games=config.num_games, config=vars(config))

    for game_id in range(config.num_games):
        try:
            result = simulate_one_game(config, game_id)
            results.append(result)
            if (game_id + 1) % 100 == 0:
                logger.log("progress", game_id=game_id + 1, total=config.num_games)
        except Exception as e:
            logger.log("game_error", game_id=game_id, error=str(e))
            # Continue with next game

    logger.log("simulation_complete", total_games=len(results))
    return results

def write_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write simulation results to CSV file."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow([
            "game_id",
            "agent_count",
            "context_condition",
            "specialization_index",
            "retrieval_efficiency",
            "successful_retrievals",
            "total_queries",
            "checksum",
            "is_synthetic"
        ])

        # Write results
        for result in results:
            writer.writerow([
                result.game_id,
                result.agent_count,
                result.context_condition,
                f"{result.specialization_index:.6f}",
                f"{result.retrieval_efficiency:.6f}",
                result.successful_retrievals,
                result.total_queries,
                result.checksum,
                result.is_synthetic
            ])

    logger.log("results_written", path=output_path, count=len(results))

def parse_agents_arg(agents_str: str) -> Union[int, List[int]]:
    """Parse agents argument which can be a single number or comma-separated list."""
    if "," in agents_str:
        return [int(x.strip()) for x in agents_str.split(",")]
    return int(agents_str)

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the experiment."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiment"
    )

    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition: full or limited"
    )

    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Number of agents (single number or comma-separated list)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset name (hanabi, coqa, or synthetic fallback)"
    )

    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate"
    )

    parser.add_argument(
        "--token-limit",
        type=int,
        default=None,
        help="Token limit for limited context mode"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path"
    )

    return parser

def main():
    """Main entry point for the experiment."""
    parser = build_parser()
    args = parser.parse_args()

    # Parse agents argument
    agent_counts = parse_agents_arg(args.agents)
    if not isinstance(agent_counts, list):
        agent_counts = [agent_counts]

    # Determine dataset name
    dataset_name = args.dataset
    if dataset_name is None:
        dataset_name = "synthetic_fallback"

    # Create output directory if needed
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    # Run simulation for each agent count
    all_results = []
    for num_agents in agent_counts:
        config = GameConfig(
            num_agents=num_agents,
            context_condition=args.context,
            dataset_name=dataset_name,
            token_limit=args.token_limit,
            seed=args.seed,
            num_games=args.games
        )

        logger.log("running_experiment", num_agents=num_agents, context=args.context)
        results = run_simulation(config)
        all_results.extend(results)

        # Determine output filename
        if args.output:
            output_path = args.output
        else:
            suffix = f"_{num_agents}agents" if len(agent_counts) > 1 else ""
            output_path = str(output_dir / f"results_{args.context}{suffix}.csv")

        write_results_csv(results, output_path)

    logger.log("all_experiments_complete", total_games=len(all_results))

if __name__ == "__main__":
    main()