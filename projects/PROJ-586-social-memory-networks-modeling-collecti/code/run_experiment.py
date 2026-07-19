"""
Main experiment runner for Social Memory Networks.
Orchestrates simulations across varying agent counts and context conditions.
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

# Project-relative imports based on provided API surface
from agent.base_agent import AgentConfig, BaseAgent
from analysis.scaling import PowerLawFitResult, ScalingAnalysisResult, power_law, fit_power_law
from data.loaders import load_experiment_results, save_experiment_results, verify_datasets
from data.synthetic import generate_synthetic_dataset
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics
from metrics.specialization import compute_specialization_index, SpecializationMetrics
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GameConfig:
    """Configuration for a single game simulation."""
    num_agents: int
    context_condition: str  # 'full' or 'limited'
    token_limit: Optional[int] = None
    dataset_name: str = "synthetic"
    seed: int = 42
    games_per_run: int = 100
    output_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results"


@dataclass
class GameResult:
    """Result of a single game simulation."""
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    total_turns: int
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_agents_arg(agents_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7' -> [3, 5, 7])."""
    try:
        return [int(x.strip()) for x in agents_str.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agent count format: {agents_str}")


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_data_checksum(data: List[Dict]) -> str:
    """Compute checksum of dataset content for reproducibility."""
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def load_and_verify_dataset(config: GameConfig) -> Tuple[List[Dict], str]:
    """Load dataset and verify integrity."""
    if config.dataset_name == "synthetic":
        # Generate synthetic data as fallback per FR-011
        logger.log("generate_synthetic_dataset", num_records=1000, seed=config.seed)
        dataset = generate_synthetic_dataset(
            num_records=1000,
            num_agents=config.num_agents,
            seed=config.seed
        )
        checksum = compute_data_checksum(dataset)
        logger.log("dataset_loaded", source="synthetic", checksum=checksum, count=len(dataset))
        return dataset, checksum
    else:
        # Attempt to load real dataset
        dataset_path = Path("data") / f"{config.dataset_name}.json"
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}. "
                                  "Use --dataset synthetic or provide real data.")
        
        checksum = compute_file_checksum(dataset_path)
        with open(dataset_path, "r") as f:
            dataset = json.load(f)
        
        verify_datasets([config.dataset_name])
        logger.log("dataset_loaded", source=str(dataset_path), checksum=checksum, count=len(dataset))
        return dataset, checksum


def truncate_context(context: str, token_limit: int) -> str:
    """Truncate context to token limit (simplified word-based approximation)."""
    if token_limit is None:
        return context
    
    tokens = context.split()
    if len(tokens) <= token_limit:
        return context
    
    truncated = " ".join(tokens[:token_limit])
    logger.log("context_truncated", original_tokens=len(context.split()), 
              truncated_tokens=len(tokens), limit=token_limit)
    return truncated


def simulate_game_turn(
    agent: BaseAgent,
    memory_buffer: MemoryBuffer,
    game_data: Dict[str, Any],
    config: GameConfig
) -> Tuple[str, bool]:
    """Simulate a single turn for an agent."""
    # Build context from memory buffer and game data
    memory_entries = memory_buffer.get_all_entries()
    memory_context = "\n".join([f"{e.key}: {e.value}" for e in memory_entries])
    
    # Prepare agent prompt
    if config.context_condition == "limited":
        context = truncate_context(
            f"Memory: {memory_context}\nTask: {game_data.get('task', '')}",
            config.token_limit
        )
    else:
        context = f"Memory: {memory_context}\nTask: {game_data.get('task', '')}"
    
    # Agent generates response (using base agent's CPU-only model)
    response = agent.generate(context)
    
    # Parse response for memory actions
    success = agent.parse_and_act(response, memory_buffer)
    
    return response, success


def simulate_one_game(config: GameConfig, game_id: int, dataset: List[Dict]) -> GameResult:
    """Simulate a single game with the specified configuration."""
    # Initialize shared memory buffer
    memory_buffer = get_shared_buffer()
    reset_shared_buffer()
    
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
    
    # Select game data
    if not dataset:
        raise ValueError("Dataset is empty for game simulation")
    
    game_data = dataset[game_id % len(dataset)]
    
    # Simulate turns
    total_turns = 0
    successful_retrievals = 0
    total_queries = 0
    
    facts_collected: Dict[int, List[str]] = {i: [] for i in range(config.num_agents)}
    
    for turn in range(10):  # Fixed number of turns for simulation
        for agent_idx, agent in enumerate(agents):
            response, success = simulate_game_turn(agent, memory_buffer, game_data, config)
            total_turns += 1
            
            if success:
                successful_retrievals += 1
            total_queries += 1
            
            # Track facts collected by each agent
            if "fact" in response.lower():
                facts_collected[agent_idx].append(response)
    
    # Compute metrics
    facts_list = [facts_collected[i] for i in range(config.num_agents)]
    spec_index, spec_metrics = compute_specialization_index(facts_list, num_agents=config.num_agents)
    ret_eff, ret_metrics = compute_retrieval_efficiency(successful_retrievals, total_queries, config.num_agents)
    
    # Determine success (arbitrary threshold for simulation)
    success = spec_index > 0.1 and ret_eff > 0.5
    
    result = GameResult(
        game_id=game_id,
        context_condition=config.context_condition,
        agent_count=config.num_agents,
        specialization_index=spec_index,
        retrieval_efficiency=ret_eff,
        total_turns=total_turns,
        success=success,
        metadata={
            "spec_metrics": spec_metrics,
            "ret_metrics": ret_metrics,
            "dataset_checksum": compute_data_checksum(dataset)
        }
    )
    
    logger.log("game_completed", game_id=game_id, 
              specialization=spec_index, retrieval=ret_eff, success=success)
    
    return result


def run_simulation(config: GameConfig) -> List[GameResult]:
    """Run simulation for all games in the configuration."""
    logger.log("simulation_start", 
              num_agents=config.num_agents,
              context=config.context_condition,
              games=config.games_per_run)
    
    dataset, checksum = load_and_verify_dataset(config)
    
    results = []
    for game_id in range(config.games_per_run):
        result = simulate_one_game(config, game_id, dataset)
        results.append(result)
        
        if (game_id + 1) % 10 == 0:
            logger.log("simulation_progress", 
                      completed=game_id + 1, 
                      total=config.games_per_run)
    
    logger.log("simulation_complete", total_games=len(results))
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write simulation results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "game_id", "context_condition", "agent_count", 
            "specialization_index", "retrieval_efficiency", 
            "total_turns", "success"
        ])
        
        for r in results:
            writer.writerow([
                r.game_id, r.context_condition, r.agent_count,
                f"{r.specialization_index:.6f}", f"{r.retrieval_efficiency:.6f}",
                r.total_turns, r.success
            ])
    
    logger.log("results_written", path=str(output_path), count=len(results))


def run_scaling_analysis(agent_counts: List[int], config: GameConfig) -> Dict[str, Any]:
    """Run simulation across varying agent counts and perform scaling analysis."""
    all_results = []
    metrics_by_count = {}
    
    for agent_count in agent_counts:
        logger.log("starting_agent_count", agent_count=agent_count)
        
        current_config = GameConfig(
            num_agents=agent_count,
            context_condition=config.context_condition,
            token_limit=config.token_limit,
            dataset_name=config.dataset_name,
            seed=config.seed,
            games_per_run=config.games_per_run,
            output_dir=config.output_dir
        )
        
        results = run_simulation(current_config)
        all_results.extend(results)
        
        # Aggregate metrics for this agent count
        spec_values = [r.specialization_index for r in results]
        ret_values = [r.retrieval_efficiency for r in results]
        
        metrics_by_count[agent_count] = {
            "avg_specialization": sum(spec_values) / len(spec_values),
            "avg_retrieval": sum(ret_values) / len(ret_values),
            "std_specialization": (sum((x - sum(spec_values)/len(spec_values))**2 for x in spec_values) / len(spec_values))**0.5,
            "std_retrieval": (sum((x - sum(ret_values)/len(ret_values))**2 for x in ret_values) / len(ret_values))**0.5
        }
        
        # Write per-agent-count results
        output_file = Path(config.output_dir) / f"results_agents_{agent_count}.csv"
        write_results_csv(results, output_file)
    
    # Perform power-law fitting
    agent_counts_sorted = sorted(metrics_by_count.keys())
    spec_values = [metrics_by_count[n]["avg_specialization"] for n in agent_counts_sorted]
    ret_values = [metrics_by_count[n]["avg_retrieval"] for n in agent_counts_sorted]
    
    # Fit power laws: y = a * x^b
    # Linearize: log(y) = log(a) + b * log(x)
    import math
    
    log_agents = [math.log(n) for n in agent_counts_sorted]
    log_spec = [math.log(max(v, 1e-10)) for v in spec_values]
    log_ret = [math.log(max(v, 1e-10)) for v in ret_values]
    
    # Simple linear regression for power law exponent
    def linear_fit(x_vals, y_vals):
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x * x for x in x_vals)
        
        denom = n * sum_x2 - sum_x * sum_x
        if abs(denom) < 1e-10:
            return 0, 0  # Fallback for degenerate case
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n
        return slope, intercept
    
    spec_slope, spec_intercept = linear_fit(log_agents, log_spec)
    ret_slope, ret_intercept = linear_fit(log_agents, log_ret)
    
    scaling_analysis = {
        "agent_counts": agent_counts_sorted,
        "specialization": {
            "values": spec_values,
            "std": [metrics_by_count[n]["std_specialization"] for n in agent_counts_sorted],
            "power_law_exponent": spec_slope,
            "intercept": spec_intercept
        },
        "retrieval": {
            "values": ret_values,
            "std": [metrics_by_count[n]["std_retrieval"] for n in agent_counts_sorted],
            "power_law_exponent": ret_slope,
            "intercept": ret_intercept
        },
        "note": "3 data points limit power-law reliability"
    }
    
    # Save scaling analysis
    output_file = Path(config.output_dir) / "scaling_analysis.json"
    with open(output_file, "w") as f:
        json.dump(scaling_analysis, f, indent=2)
    
    logger.log("scaling_analysis_complete", 
              file=str(output_file),
              spec_exponent=spec_slope,
              ret_exponent=ret_slope)
    
    return scaling_analysis


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the experiment."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments with varying agent counts"
    )
    
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition (full or limited)"
    )
    
    parser.add_argument(
        "--agents",
        type=parse_agents_arg,
        default="3,5,7",
        help="Comma-separated list of agent counts (e.g., '3,5,7')"
    )
    
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games per agent count"
    )
    
    parser.add_argument(
        "--dataset",
        choices=["synthetic", "hanabi", "coqa"],
        default="synthetic",
        help="Dataset to use"
    )
    
    parser.add_argument(
        "--token-limit",
        type=int,
        default=None,
        help="Token limit for limited context (default: no limit)"
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
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate scaling plot (requires matplotlib)"
    )
    
    return parser


def main():
    """Main entry point for the experiment."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Create config
    config = GameConfig(
        num_agents=args.agents[0] if len(args.agents) == 1 else args.agents[0],  # Default for single run
        context_condition=args.context,
        token_limit=args.token_limit,
        dataset_name=args.dataset,
        seed=args.seed,
        games_per_run=args.games,
        output_dir=args.output_dir
    )
    
    # Ensure output directory exists
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run simulation for single agent count or scaling analysis
    if len(args.agents) == 1:
        # Single agent count run
        results = run_simulation(config)
        output_file = Path(config.output_dir) / f"results_{args.context}_agents_{args.agents[0]}.csv"
        write_results_csv(results, output_file)
    else:
        # Scaling analysis across multiple agent counts
        scaling_analysis = run_scaling_analysis(args.agents, config)
        
        # Generate plot if requested
        if args.plot:
            try:
                import matplotlib.pyplot as plt
                
                plt.figure(figsize=(10, 6))
                
                # Plot specialization
                plt.subplot(1, 2, 1)
                plt.errorbar(
                    scaling_analysis["agent_counts"],
                    scaling_analysis["specialization"]["values"],
                    yerr=scaling_analysis["specialization"]["std"],
                    fmt='o-',
                    label='Specialization Index'
                )
                # Plot power law fit
                agent_counts = scaling_analysis["agent_counts"]
                exponent = scaling_analysis["specialization"]["power_law_exponent"]
                intercept = scaling_analysis["specialization"]["intercept"]
                fitted = [math.exp(intercept) * (n ** exponent) for n in agent_counts]
                plt.plot(agent_counts, fitted, 'r--', label=f'Power Law (exp={exponent:.3f})')
                plt.xlabel("Number of Agents")
                plt.ylabel("Specialization Index")
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Plot retrieval
                plt.subplot(1, 2, 2)
                plt.errorbar(
                    scaling_analysis["agent_counts"],
                    scaling_analysis["retrieval"]["values"],
                    yerr=scaling_analysis["retrieval"]["std"],
                    fmt='s-',
                    label='Retrieval Efficiency'
                )
                # Plot power law fit
                exponent = scaling_analysis["retrieval"]["power_law_exponent"]
                intercept = scaling_analysis["retrieval"]["intercept"]
                fitted = [math.exp(intercept) * (n ** exponent) for n in agent_counts]
                plt.plot(agent_counts, fitted, 'r--', label=f'Power Law (exp={exponent:.3f})')
                plt.xlabel("Number of Agents")
                plt.ylabel("Retrieval Efficiency")
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plot_path = Path(config.output_dir) / "scaling_plot.pdf"
                plt.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close()
                
                logger.log("scaling_plot_generated", path=str(plot_path))
                
            except ImportError:
                logger.log("plot_skipped", reason="matplotlib not installed")
    
    logger.log("experiment_complete", output_dir=config.output_dir)


if __name__ == "__main__":
    main()