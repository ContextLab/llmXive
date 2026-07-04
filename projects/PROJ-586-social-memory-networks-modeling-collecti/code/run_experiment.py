"""
Main experiment runner for Social Memory Networks.
Implements CLI parsing, game simulation, and metrics computation for US-1, US-2, and US-3.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import from project modules (matching API surface)
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger, log_operation
from memory.buffer import MemoryBuffer, get_shared_buffer

logger = get_logger(__name__)


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    num_facts: int = 50
    context_condition: str = "full"  # "full" or "limited"
    context_window_size: int = 512
    seed: int = 42
    game_id: str = ""


@dataclass
class ExperimentConfig:
    """Configuration for the full experiment run."""
    context: str = "full"
    agents: Union[str, List[int]] = "5"
    dataset: Optional[str] = None
    games: int = 100
    seed: int = 42
    output_dir: str = "results"
    plot_scaling: bool = False
    thresholds: List[int] = field(default_factory=lambda: [128, 256, 512])


def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse --agents argument which can be '5' or '3,5,7'."""
    if not agents_str:
        return [5]
    parts = [p.strip() for p in agents_str.split(",")]
    return [int(p) for p in parts if p]


def simulate_one_game(game_id: int, config: GameConfig) -> Dict[str, Any]:
    """
    Simulate a single transactive memory game.
    Returns a dictionary with game results and computed metrics.
    """
    random.seed(config.seed + game_id)
    
    # Generate facts for this game
    facts = [f"Fact_{i}_{random.randint(1000, 9999)}" for i in range(config.num_facts)]
    
    # Distribute facts to agents (specialization)
    agent_facts: Dict[int, List[str]] = {i: [] for i in range(config.num_agents)}
    for fact in facts:
        owner = random.randint(0, config.num_agents - 1)
        agent_facts[owner].append(fact)
    
    # Simulate retrieval attempts
    # Each agent tries to recall facts they know + some from memory buffer
    retrieved_facts: Dict[int, List[str]] = {i: [] for i in range(config.num_agents)}
    total_queries = 0
    total_retrieved = 0
    
    buffer = get_shared_buffer()
    
    for agent_id in range(config.num_agents):
        # Agent knows their own facts
        known = set(agent_facts[agent_id])
        retrieved_facts[agent_id].extend(list(known))
        
        # In limited context, agents have fewer queries
        if config.context_condition == "limited":
            queries = max(1, len(facts) // 4)
        else:
            queries = len(facts)
        
        total_queries += queries
        
        # Simulate retrieval from buffer (shared memory)
        for _ in range(queries):
            # Simulate a retrieval attempt
            target_fact = random.choice(facts)
            total_retrieved += 1
            if target_fact not in retrieved_facts[agent_id]:
                retrieved_facts[agent_id].append(target_fact)
    
    # Compute specialization index
    skill_lengths = [len(agent_facts[i]) for i in range(config.num_agents)]
    spec_index, spec_metrics = compute_specialization_index(skill_lengths, num_agents=config.num_agents)
    
    # Compute retrieval efficiency
    # Total unique facts retrieved across all agents
    all_retrieved = set()
    for agent_retrieved in retrieved_facts.values():
        all_retrieved.update(agent_retrieved)
    retrieval_eff, ret_metrics = compute_retrieval_efficiency(
        len(all_retrieved), 
        len(facts), 
        config.num_agents
    )
    
    return {
        "game_id": config.game_id or f"game_{game_id}",
        "num_agents": config.num_agents,
        "num_facts": config.num_facts,
        "context_condition": config.context_condition,
        "specialization_index": spec_index,
        "specialization_metrics": spec_metrics,
        "retrieval_efficiency": retrieval_eff,
        "retrieval_metrics": ret_metrics,
        "total_queries": total_queries,
        "total_retrieved": total_retrieved,
        "unique_facts_retrieved": len(all_retrieved),
        "seed": config.seed + game_id
    }


def run_simulation(config: ExperimentConfig) -> List[Dict[str, Any]]:
    """
    Run the full simulation for specified agent counts and game counts.
    For US-3: runs 800 games per agent count (3, 5, 7).
    """
    agent_counts = parse_agents_arg(config.agents)
    random.seed(config.seed)
    
    results = []
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine games per agent count
    # For US-3 scaling: 800 games per agent count
    # For US-1/US-2: use config.games
    games_per_count = config.games
    if len(agent_counts) > 1:
        # Scaling analysis (US-3)
        games_per_count = 800
    
    logger.log("run_simulation", 
               agent_counts=agent_counts, 
               games_per_count=games_per_count,
               context=config.context)
    
    for agent_count in agent_counts:
        logger.log("simulate_agent_count", agent_count=agent_count)
        
        for game_idx in range(games_per_count):
            game_config = GameConfig(
                num_agents=agent_count,
                num_facts=50,
                context_condition=config.context,
                seed=config.seed + game_idx,
                game_id=f"{config.context}_{agent_count}_{game_idx}"
            )
            
            result = simulate_one_game(game_idx, game_config)
            result["agent_count"] = agent_count
            results.append(result)
            
            if (game_idx + 1) % 100 == 0:
                logger.log("progress", games_completed=game_idx + 1, agent_count=agent_count)
    
    return results


def write_results_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write simulation results to CSV file."""
    if not results:
        logger.log("write_results_csv", status="empty", path=output_path)
        return
    
    # Standardize column names
    fieldnames = [
        "game_id", 
        "specialization_index", 
        "retrieval_efficiency", 
        "context_condition", 
        "agent_count",
        "num_facts",
        "total_queries",
        "unique_facts_retrieved",
        "seed"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            row = {k: result.get(k, "") for k in fieldnames}
            writer.writerow(row)
    
    logger.log("write_results_csv", 
               status="success", 
               path=output_path, 
               rows=len(results))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser with flags for US-1, US-2, and US-3."""
    parser = argparse.ArgumentParser(
        description="Social Memory Networks Experiment Runner"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: 'full' (US-1) or 'limited' (US-2)"
    )
    
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent counts: single (e.g., '5') or comma-separated (e.g., '3,5,7' for US-3)"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset name or path (optional, uses synthetic fallback if not provided)"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per agent count"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--plot-scaling",
        action="store_true",
        help="Generate scaling plot (US-3)"
    )
    
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated context window thresholds for sensitivity analysis"
    )
    
    return parser


def main() -> None:
    """Main entry point for experiment runner."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Parse thresholds
    thresholds = [int(t.strip()) for t in args.thresholds.split(",") if t.strip()]
    
    config = ExperimentConfig(
        context=args.context,
        agents=args.agents,
        dataset=args.dataset,
        games=args.games,
        seed=args.seed,
        output_dir=args.output_dir,
        plot_scaling=args.plot_scaling,
        thresholds=thresholds
    )
    
    logger.log("main_start", config=json.dumps({
        "context": config.context,
        "agents": config.agents,
        "games": config.games,
        "seed": config.seed
    }))
    
    # Run simulation
    results = run_simulation(config)
    
    # Determine output filename
    agent_counts = parse_agents_arg(config.agents)
    if len(agent_counts) == 1:
        output_filename = f"results_{config.context}.csv"
    else:
        output_filename = f"results_scaling_{config.context}.csv"
    
    output_path = os.path.join(config.output_dir, output_filename)
    
    # Write results to CSV
    write_results_csv(results, output_path)
    
    logger.log("main_complete", 
               total_results=len(results),
               output_file=output_path)
    
    # If scaling plot requested, trigger analysis
    if config.plot_scaling and len(agent_counts) > 1:
        logger.log("scaling_plot_requested", agent_counts=agent_counts)
        # This would call the scaling analysis module
        # For now, just log the request
        print(f"Scaling analysis requested for agent counts: {agent_counts}")
        print(f"Results written to: {output_path}")


if __name__ == "__main__":
    main()