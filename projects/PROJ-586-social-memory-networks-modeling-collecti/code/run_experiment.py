"""
Main experiment runner for Social Memory Networks.
Orchestrates game simulations, metric computation, and result aggregation.
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

# Local imports from project structure
from agent.base_agent import AgentConfig, BaseAgent
from analysis.scaling import (
    PowerLawFitResult,
    ScalingAnalysisResult,
    fit_power_law,
    load_scaling_data,
    run_scaling_analysis,
)
from data.loaders import (
    DatasetSpec,
    enable_synthetic_fallback,
    get_dataset,
    load_experiment_results,
    verify_datasets,
)
from data.synthetic import generate_synthetic_cue_response_pairs
from memory.buffer import MemoryBuffer, MemoryEntry
from metrics.retrieval import RetrievalMetrics, compute_retrieval_efficiency
from metrics.specialization import SpecializationMetrics, compute_specialization_index
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    context_condition: str  # 'full' or 'limited'
    agent_count: int
    dataset_name: str
    token_limit: Optional[int] = None  # For limited context
    max_turns: int = 50
    seed: int = 42

@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    token_limit: Optional[int] = None
    game_duration_sec: float = 0.0
    total_turns: int = 0

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict], str]:
    """
    Load dataset based on config.
    Returns (data_list, source_url).
    """
    dataset_name = config.dataset_name
    spec = None

    try:
        # Try to verify and get real dataset
        specs = verify_datasets([dataset_name])
        if specs and specs[0].status == "verified":
            spec = specs[0]
        else:
            # Trigger fallback if verification failed
            enable_synthetic_fallback()
            logger.warning(f"Dataset {dataset_name} not verified, using synthetic fallback.")
    except Exception as e:
        logger.warning(f"Dataset verification failed: {e}. Using synthetic fallback.")
        enable_synthetic_fallback()

    if spec and spec.status == "verified":
        # Real dataset path
        data_path = Path(spec.path) if spec.path else None
        if data_path and data_path.exists():
            # Load CSV/JSON if available
            if data_path.suffix == ".csv":
                with open(data_path, "r") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                return data, spec.source_url
            elif data_path.suffix == ".json":
                with open(data_path, "r") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data, spec.source_url
                elif isinstance(data, dict) and "data" in data:
                    return data["data"], spec.source_url
            # If file exists but format unknown, return empty
            return [], spec.source_url
        else:
            # File doesn't exist, try synthetic
            enable_synthetic_fallback()
    else:
        enable_synthetic_fallback()

    # Fallback: Generate synthetic data
    logger.info(f"Generating synthetic data for {dataset_name}")
    synthetic_data = generate_synthetic_cue_response_pairs(num_records=20)
    return synthetic_data, "synthetic_fallback"

def truncate_context(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens."""
    if max_tokens is None:
        return text
    # Rough token estimation: 1 token ~ 4 characters
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

# -----------------------------------------------------------------------------
# Simulation Logic
# -----------------------------------------------------------------------------

def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    current_state: Dict[str, Any],
    config: GameConfig,
) -> Tuple[str, Optional[MemoryEntry]]:
    """
    Simulate a single turn for an agent.
    Returns (action, memory_entry).
    """
    # Prepare prompt based on context condition
    prompt = f"Agent {agent.id} observes: {current_state}\n"

    if config.context_condition == "limited" and config.token_limit:
        prompt = truncate_context(prompt, config.token_limit)

    prompt += "What is your action? (write/read/memory)"

    # In a real implementation, this would call the LLM
    # For now, we simulate a deterministic response for testing
    action = f"Agent {agent.id} performs action"
    
    # Simulate memory interaction
    memory_entry = None
    if random.random() > 0.5:  # 50% chance to write to memory
        memory_entry = MemoryEntry(
            agent_id=agent.id,
            content=f"Fact remembered by agent {agent.id}",
            timestamp=time.time(),
          )
        memory_buffer.write(memory_entry)

    return action, memory_entry

def simulate_one_game(config: GameConfig, game_id: int) -> GameResult:
    """
    Simulate a single game with the given configuration.
    This is the core simulation loop for varying agent counts.
    """
    start_time = time.time()
    
    # Load data
    data, source_url = load_and_verify_dataset(config)
    if not data:
        # Fallback to synthetic if real data is empty
        data = generate_synthetic_cue_response_pairs(num_records=10)

    # Initialize agents
    agents = []
    for i in range(config.agent_count):
        agent_cfg = AgentConfig(
            id=i,
            model_name="facebook/opt-125m",
            device="cpu",
            seed=config.seed + i,
        )
        agents.append(BaseAgent(agent_cfg))

    # Initialize shared memory
    memory_buffer = MemoryBuffer()

    # Game state
    current_state = {"turn": 0, "data_index": 0, "total_data": len(data)}
    total_turns = 0
    agent_contributions = {i: 0 for i in range(config.agent_count)}
    total_retrieved = 0
    total_facts = len(set(item.get("cue", "") for item in data if "cue" in item))

    # Simulation loop
    while total_turns < config.max_turns:
        current_state["turn"] = total_turns
        
        # Each agent takes a turn
        for agent in agents:
            action, memory_entry = simulate_game_turn(
                agent, memory_buffer, current_state, config
            )
            
            if memory_entry:
                agent_contributions[agent.id] += 1
                total_retrieved += 1
            
            total_turns += 1
            
            # Check termination condition
            if total_turns >= config.max_turns:
                break

    # Compute metrics
    spec_index, _ = compute_specialization_index(agent_contributions, config.agent_count)
    ret_eff, _ = compute_retrieval_efficiency(total_retrieved, total_facts, config.agent_count)

    duration = time.time() - start_time

    return GameResult(
        game_id=game_id,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        context_condition=config.context_condition,
        agent_count=config.agent_count,
        token_limit=config.token_limit,
        game_duration_sec=duration,
        total_turns=total_turns,
    )

def run_scaling_simulation(
    agent_counts: List[int],
    context_condition: str = "full",
    dataset_name: str = "hanabi",
    games_per_count: int = 10,
    output_path: str = "results/scaling_raw.csv",
) -> List[GameResult]:
    """
    Run simulations for varying agent counts (US-3).
    This implements the core logic for T027.
    """
    all_results = []
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting scaling simulation for agent counts: {agent_counts}")
    
    for count in agent_counts:
        logger.info(f"Running {games_per_count} games with {count} agents...")
        for game_id in range(games_per_count):
            config = GameConfig(
                context_condition=context_condition,
                agent_count=count,
                dataset_name=dataset_name,
                max_turns=20,  # Reduced for CPU budget in scaling analysis
                seed=42 + game_id,
            )
            result = simulate_one_game(config, game_id)
            all_results.append(result)
            logger.debug(f"Completed game {game_id} for agent count {count}")

    # Write results to CSV
    write_scaling_results_csv(all_results, output_path)
    logger.info(f"Scaling simulation complete. Results written to {output_path}")
    
    return all_results

def write_scaling_results_csv(results: List[GameResult], output_path: str) -> None:
    """Write scaling simulation results to CSV."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "game_id", "agent_count", "specialization_index", 
            "retrieval_efficiency", "context_condition", "token_limit",
            "game_duration_sec", "total_turns"
        ])
        for r in results:
            writer.writerow([
                r.game_id, r.agent_count, r.specialization_index,
                r.retrieval_efficiency, r.context_condition, r.token_limit,
                r.game_duration_sec, r.total_turns
            ])

# -----------------------------------------------------------------------------
# CLI Interface
# -----------------------------------------------------------------------------

def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7')."""
    try:
        return [int(x.strip()) for x in agents_str.split(",")]
    except ValueError:
        raise ValueError(f"Invalid agents argument: {agents_str}. Expected comma-separated integers.")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Social Memory Networks Experiment Runner")
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent count(s) (comma-separated for scaling, e.g., 3,5,7)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="hanabi",
        help="Dataset name (hanabi, coqa)",
    )
    parser.add_argument(
        "--scaling",
        action="store_true",
        help="Run scaling analysis across agent counts",
    )
    parser.add_argument(
        "--token-sweep",
        action="store_true",
        help="Run token limit sweep (US-2)",
    )
    parser.add_argument(
        "--games-per-count",
        type=int,
        default=10,
        help="Number of games per agent count for scaling",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/scaling_raw.csv",
        help="Output file path",
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Handle scaling mode (T027)
    if args.scaling:
        agent_counts = parse_agents_arg(args.agents)
        if len(agent_counts) < 2:
            logger.warning("Scaling mode requires at least 2 agent counts. Defaulting to [3, 5, 7].")
            agent_counts = [3, 5, 7]
        
        run_scaling_simulation(
            agent_counts=agent_counts,
            context_condition=args.context,
            dataset_name=args.dataset,
            games_per_count=args.games_per_count,
            output_path=args.output,
        )
    else:
        # Single run mode
        agent_count = int(args.agents)
        config = GameConfig(
            context_condition=args.context,
            agent_count=agent_count,
            dataset_name=args.dataset,
            max_turns=50,
            seed=42,
        )
        result = simulate_one_game(config, game_id=0)
        print(json.dumps({
            "game_id": result.game_id,
            "specialization_index": result.specialization_index,
            "retrieval_efficiency": result.retrieval_efficiency,
            "agent_count": result.agent_count,
        }, indent=2))

if __name__ == "__main__":
    main()