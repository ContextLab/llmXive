"""
Main experiment runner for Social Memory Networks.
Orchestrates simulations, metrics computation, and result aggregation.
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

# Local imports - using exact names from API surface
from agent.base_agent import AgentConfig, BaseAgent
from analysis.anova import run_anova_analysis
from analysis.power import run_power_analysis
from analysis.sensitivity import run_sensitivity_analysis
from data.loaders import DatasetSpec, get_dataset, load_experiment_results, save_experiment_results, verify_datasets
from data.synthetic import generate_synthetic_cue_response_pairs
from memory.buffer import MemoryBuffer, get_shared_buffer
from metrics.retrieval import compute_retrieval_efficiency
from metrics.specialization import compute_specialization_index
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    context_condition: str  # 'full' or 'limited'
    agent_count: int
    dataset_name: str
    token_limit: Optional[int] = None  # For limited context
    seed: int = 42
    max_turns: int = 50

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    token_limit: Optional[int] = None
    dataset_name: str = ""

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse agent count argument (supports single int or comma-separated list)."""
    if ',' in agents_str:
        return [int(x.strip()) for x in agents_str.split(',')]
    return [int(agents_str)]

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_verify_dataset(dataset_name: str, config: GameConfig) -> Tuple[Any, str]:
    """
    Load and verify dataset. Falls back to synthetic data if real data unavailable.
    Returns (dataset, source_url).
    """
    dataset_spec = None
    source_url = ""
    
    try:
        if dataset_name == "hanabi":
            # Try to import gymnasium and create Hanabi environment
            try:
                import gymnasium as gym
                env = gym.make('hanabi-v0')
                dataset_spec = DatasetSpec(
                    name="hanabi",
                    source_url="gymnasium://hanabi-v0",
                    loader_type="gymnasium"
                )
                source_url = "gymnasium://hanabi-v0"
                logger.log("dataset_loaded", operation="hanabi", status="verified", env=env)
                return env, source_url
            except Exception as e:
                logger.log("dataset_missing", operation="hanabi", error=str(e))
                raise RuntimeError(f"Hanabi dataset not available: {e}")
        
        elif dataset_name == "coqa":
            # Try to load CoQA from HuggingFace
            try:
                from datasets import load_dataset
                # Use streaming for large datasets
                ds = load_dataset('coqa', streaming=True)
                dataset_spec = DatasetSpec(
                    name="coqa",
                    source_url="https://huggingface.co/datasets/coqa",
                    loader_type="huggingface"
                )
                source_url = "https://huggingface.co/datasets/coqa"
                logger.log("dataset_loaded", operation="coqa", status="verified", streaming=True)
                return ds, source_url
            except Exception as e:
                logger.log("dataset_missing", operation="coqa", error=str(e))
                raise RuntimeError(f"CoQA dataset not available: {e}")
        
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
            
    except Exception as e:
        # Fallback to synthetic data - log explicitly
        logger.log("fallback_initiated", operation="synthetic", dataset=dataset_name, reason=str(e))
        
        # Generate synthetic cue-response pairs
        synthetic_records = generate_synthetic_cue_response_pairs(num_records=200)
        
        # Save synthetic data to manifest
        manifest = {
            "dataset_name": f"synthetic_{dataset_name}",
            "source_url": "synthetic://fallback",
            "sha256_hash": hashlib.sha256(json.dumps(synthetic_records).encode()).hexdigest(),
            "download_path": "data/synthetic_fallback.json",
            "fallback_reason": str(e)
        }
        
        # Write manifest
        manifest_path = Path("data/manifest.json")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.log("fallback_completed", operation="synthetic", manifest_path=str(manifest_path))
        return synthetic_records, "synthetic://fallback"

def truncate_context(context: str, token_limit: int) -> str:
    """Truncate context to token limit (approximate by word count)."""
    if token_limit is None:
        return context
    
    # Approximate: 1 token ≈ 0.75 words
    word_limit = int(token_limit * 0.75)
    words = context.split()
    if len(words) <= word_limit:
        return context
    return ' '.join(words[:word_limit])

def simulate_game_turn(
    agent: BaseAgent,
    state: Dict[str, Any],
    memory_buffer: MemoryBuffer,
    config: GameConfig
) -> Tuple[str, Dict[str, Any]]:
    """
    Simulate a single game turn for an agent.
    Returns (action, updated_state).
    """
    # Prepare context based on condition
    if config.context_condition == "limited" and config.token_limit:
        state_context = truncate_context(str(state), config.token_limit)
    else:
        state_context = str(state)
    
    # Agent generates action
    action = agent.generate_action(state_context, memory_buffer)
    
    # Update memory buffer if action contains memory operations
    if isinstance(action, dict) and 'memory_action' in action:
        memory_buffer.write(action['memory_action'])
    
    # Update state based on action
    updated_state = state.copy()
    updated_state['last_action'] = action
    
    return action, updated_state

def simulate_one_game(config: GameConfig, game_id: int, dataset: Any = None) -> GameResult:
    """
    Simulate a single game and return results.
    This is the core simulation loop.
    """
    # Initialize agents
    agents = []
    for i in range(config.agent_count):
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
    
    # Load dataset if not provided
    if dataset is None:
        dataset, _ = load_and_verify_dataset(config.dataset_name, config)
    
    # Initialize game state
    # For Hanabi: use environment state
    # For synthetic/CoQA: use synthetic records
    if hasattr(dataset, 'reset'):
        # Gymnasium environment
        state, _ = dataset.reset()
    else:
        # Synthetic or HuggingFace dataset
        if isinstance(dataset, list) and len(dataset) > 0:
            state = dataset[game_id % len(dataset)]
        else:
            state = {"turn": 0, "cards": [], "clues": []}
    
    # Game loop
    turn = 0
    successful_retrievals = 0
    total_retrievals = 0
    agent_contributions = [0] * config.agent_count
    
    while turn < config.max_turns:
        # Each agent takes a turn
        for agent_idx, agent in enumerate(agents):
            action, state = simulate_game_turn(agent, state, memory_buffer, config)
            
            # Track contributions and retrievals
            if isinstance(action, dict):
                if action.get('type') == 'play':
                    agent_contributions[agent_idx] += 1
                if action.get('type') == 'retrieve':
                    total_retrievals += 1
                    if action.get('success', False):
                        successful_retrievals += 1
            
            # Check termination condition
            if isinstance(state, dict) and state.get('game_over', False):
                break
            
            turn += 1
            if turn >= config.max_turns:
                break
        
        if turn >= config.max_turns:
            break
    
    # Compute metrics
    spec_index, _ = compute_specialization_index(agent_contributions, num_agents=config.agent_count)
    ret_eff, _ = compute_retrieval_efficiency(
        successful_retrievals, 
        total_retrievals, 
        config.agent_count
    )
    
    return GameResult(
        game_id=game_id,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        context_condition=config.context_condition,
        agent_count=config.agent_count,
        token_limit=config.token_limit,
        dataset_name=config.dataset_name
    )

def run_simulation(
    context_condition: str,
    agent_count: int,
    dataset_name: str,
    token_limits: Optional[List[int]] = None,
    game_count: int = 200,
    output_path: str = "results/results_sensitivity.csv"
) -> List[GameResult]:
    """
    Run simulation sweep over token limits and game count.
    """
    # Load dataset once
    dataset, source_url = load_and_verify_dataset(dataset_name, GameConfig(
        context_condition=context_condition,
        agent_count=agent_count,
        dataset_name=dataset_name
    ))
    
    # Save dataset manifest
    if not source_url.startswith("synthetic"):
        try:
            if hasattr(dataset, 'data_file'):
                checksum = compute_file_checksum(dataset.data_file)
            else:
                checksum = hashlib.sha256(str(dataset).encode()).hexdigest()
            
            manifest = {
                "dataset_name": dataset_name,
                "source_url": source_url,
                "sha256_hash": checksum,
                "download_path": f"data/{dataset_name}"
            }
            with open("data/manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            logger.log("manifest_write_failed", error=str(e))
    
    results = []
    
    # Determine token limits to sweep
    if token_limits is None:
        if context_condition == "limited":
            token_limits = [128, 256, 512]  # FR-008 mandated sweep
        else:
            token_limits = [None]  # Full context
    
    # Run simulation for each token limit
    for token_limit in token_limits:
        logger.log("simulation_start", token_limit=token_limit, game_count=game_count)
        
        for game_id in range(game_count):
            config = GameConfig(
                context_condition=context_condition,
                agent_count=agent_count,
                dataset_name=dataset_name,
                token_limit=token_limit,
                seed=42 + game_id,
                max_turns=50
            )
            
            result = simulate_one_game(config, game_id, dataset)
            results.append(result)
            
            if (game_id + 1) % 50 == 0:
                logger.log("simulation_progress", game_id=game_id + 1, total=game_count)
        
        logger.log("simulation_complete", token_limit=token_limit, results_count=len(results))
    
    # Write results to CSV
    write_results_csv(results, output_path)
    
    return results

def write_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write simulation results to CSV file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'token_limit', 'game_id', 'specialization_index', 
        'retrieval_efficiency', 'context_condition', 'agent_count', 'dataset_name'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'token_limit': result.token_limit if result.token_limit is not None else 'full',
                'game_id': result.game_id,
                'specialization_index': result.specialization_index,
                'retrieval_efficiency': result.retrieval_efficiency,
                'context_condition': result.context_condition,
                'agent_count': result.agent_count,
                'dataset_name': result.dataset_name
            })
    
    logger.log("results_written", path=output_path, count=len(results))

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(description="Social Memory Networks Experiment Runner")
    
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
        help="Number of agents (int or comma-separated list)"
    )
    
    parser.add_argument(
        "--dataset",
        choices=["hanabi", "coqa"],
        default="hanabi",
        help="Dataset to use"
    )
    
    parser.add_argument(
        "--token-sweep",
        action="store_true",
        help="Run systematic sweep over token limits {128, 256, 512}"
    )
    
    parser.add_argument(
        "--game-count",
        type=int,
        default=None,
        help="Number of games to simulate (default: from SIMULATION_GAME_COUNT env or 200)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path"
    )
    
    return parser

def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse agent counts
    agent_counts = parse_agents_arg(args.agents)
    
    # Get game count from env or args
    game_count = args.game_count
    if game_count is None:
        env_count = os.environ.get('SIMULATION_GAME_COUNT', '200')
        try:
            game_count = int(env_count)
            if game_count <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            raise ValueError(f"Invalid SIMULATION_GAME_COUNT: must be a positive integer")
    
    # Determine output path
    if args.output:
        output_path = args.output
    elif args.token_sweep or args.context == "limited":
        output_path = "results/results_sensitivity.csv"
    else:
        output_path = "results/results_full.csv"
    
    # Run simulation
    token_limits = None
    if args.token_sweep or args.context == "limited":
        token_limits = [128, 256, 512]
    
    results = run_simulation(
        context_condition=args.context,
        agent_count=agent_counts[0],  # Use first agent count for sweep
        dataset_name=args.dataset,
        token_limits=token_limits,
        game_count=game_count,
        output_path=output_path
    )
    
    logger.log("experiment_complete", total_results=len(results), output_path=output_path)
    print(f"Experiment complete. Results written to {output_path}")
    print(f"Total games simulated: {len(results)}")

if __name__ == "__main__":
    main()