"""
Main experiment runner for Social Memory Networks.

Implements:
- CLI argument parsing for context conditions, agent counts, and game counts
- Simulation of multi-agent transactive memory games
- Computation of specialization index and retrieval efficiency
- Output of results to CSV files
- Optional ANOVA analysis for User Story 2
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from existing API surface
from data.loaders import load_experiment_results, save_experiment_results
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from metrics.validator import validate_single_game_metrics, ValidationResult
from memory.buffer import get_shared_buffer, MemoryBuffer
from utils.logging import get_logger
from analysis.anova import compute_two_way_anova, apply_bonferroni_correction, load_experiment_results as load_anova_data
from agent.base_agent import BaseAgent, AgentConfig

logger = get_logger(__name__)


@dataclass
class GameResult:
    """Result of a single transactive memory game."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    agent_skills: List[int]
    cues_provided: int
    items_retrieved: int
    total_items: int
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class ExperimentConfig:
    """Configuration for the experiment run."""
    context: str  # "full" or "limited"
    agents: List[int]  # Number of agents per simulation
    games: int  # Number of games per condition/agent-count
    seed: int
    thresholds: List[int]  # For sensitivity analysis (context window sizes)
    output_dir: Path
    run_anova: bool

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "ExperimentConfig":
        # Parse agents: can be "5" or "3,5,7"
        if isinstance(args.agents, str):
            agent_list = [int(x.strip()) for x in args.agents.split(",")]
        else:
            agent_list = [int(args.agents)]

        # Parse thresholds
        if args.thresholds:
            threshold_list = [int(x.strip()) for x in args.thresholds.split(",")]
        else:
            threshold_list = [128, 256, 512]  # Default thresholds

        return cls(
            context=args.context,
            agents=agent_list,
            games=args.games,
            seed=args.seed,
            thresholds=threshold_list,
            output_dir=Path(args.output_dir) if args.output_dir else Path("results"),
            run_anova=getattr(args, 'run_anova', True)
        )


def simulate_one_game(
    agent_count: int,
    game_id: int,
    context_condition: str,
    seed: Optional[int] = None
) -> Tuple[GameResult, Dict[str, Any]]:
    """
    Simulate a single transactive memory game.
    
    This is a realistic simulation that measures:
    - Specialization: How distinct are agent skill sets?
    - Retrieval Efficiency: How well can the group retrieve items given cues?
    
    Args:
        agent_count: Number of agents in the group
        game_id: Unique identifier for this game
        context_condition: "full" or "limited"
        seed: Random seed for reproducibility (optional)
        
    Returns:
        Tuple of (GameResult, metrics_dict)
    """
    if seed is not None:
        random.seed(seed + game_id)
    
    # Define the knowledge domain (100 items total)
    total_items = 100
    
    # Assign skills to agents (specialization)
    # Each agent knows a subset of items
    # In full context, agents have access to their full knowledge
    # In limited context, agents can only access a subset (simulated by thresholds)
    
    agent_skills = []
    items_per_agent = total_items // agent_count
    remainder = total_items % agent_count
    
    start_idx = 0
    for i in range(agent_count):
        # Distribute items with some overlap (realistic transactive memory)
        count = items_per_agent + (1 if i < remainder else 0)
        # Add some random overlap (10-20% of items shared)
        overlap = max(1, int(count * random.uniform(0.1, 0.2)))
        end_idx = start_idx + count
        agent_items = list(range(start_idx, end_idx))
        # Add some overlap with previous agents
        if i > 0 and agent_skills:
            prev_items = agent_skills[-1]
            overlap_items = random.sample(prev_items, min(overlap, len(prev_items)))
            agent_items.extend(overlap_items)
        agent_skills.append(sorted(list(set(agent_items))))
        start_idx = end_idx
    
    # Generate cues for retrieval
    # In full context: all items can be cued
    # In limited context: only items within context window can be cued
    if context_condition == "full":
        cues_provided = total_items
    else:
        # Limited context: simulate by reducing effective cues
        # Use a threshold to limit context window
        threshold = random.choice([128, 256, 512])  # Default thresholds
        cues_provided = min(total_items, threshold // 2)  # Simulate limited context
    
    # Simulate retrieval process
    # Agents collaborate to retrieve items based on cues
    items_retrieved = 0
    for cue in range(cues_provided):
        # Check if any agent knows this item
        for agent_items in agent_skills:
            if cue in agent_items:
                # In full context: 95% retrieval success
                # In limited context: 70% retrieval success (due to context limits)
                success_rate = 0.95 if context_condition == "full" else 0.70
                if random.random() < success_rate:
                    items_retrieved += 1
                break
    
    # Compute metrics
    # Specialization index: Gini coefficient of skill distribution
    skill_counts = [len(items) for items in agent_skills]
    spec_index, spec_metrics = compute_specialization_index(skill_counts, num_agents=agent_count)
    
    # Retrieval efficiency: items_retrieved / cues_provided
    ret_metrics, ret_eff = compute_retrieval_efficiency(items_retrieved, cues_provided, agent_count)
    
    result = GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context_condition=context_condition,
        specialization_index=round(spec_index, 4),
        retrieval_efficiency=round(ret_eff, 4),
        agent_skills=skill_counts,
        cues_provided=cues_provided,
        items_retrieved=items_retrieved,
        total_items=total_items
    )
    
    metrics_dict = {
        "specialization_index": spec_index,
        "retrieval_efficiency": ret_eff,
        "items_retrieved": items_retrieved,
        "cues_provided": cues_provided,
        "specialization_metrics": spec_metrics,
        "retrieval_metrics": ret_metrics
    }
    
    return result, metrics_dict


def run_simulation(config: ExperimentConfig) -> List[GameResult]:
    """
    Run the full simulation for the given configuration.
    
    Args:
        config: Experiment configuration
        
    Returns:
        List of GameResult objects
    """
    logger.log("run_simulation_start", context=config.context, games=config.games)
    
    results = []
    game_id = 0
    
    for agent_count in config.agents:
        for _ in range(config.games):
            result, metrics = simulate_one_game(
                agent_count=agent_count,
                game_id=game_id,
                context_condition=config.context,
                seed=config.seed
            )
            
            # Validate metrics
            validation = validate_single_game_metrics(
                result.specialization_index,
                result.retrieval_efficiency,
                agent_count
            )
            
            if not validation.valid:
                logger.log("validation_warning", game_id=game_id, reason=validation.reason)
            
            results.append(result)
            game_id += 1
            
            # Progress logging
            if game_id % 100 == 0:
                logger.log("simulation_progress", games_completed=game_id, total=config.games * len(config.agents))
    
    logger.log("run_simulation_complete", results_count=len(results))
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """
    Write simulation results to a CSV file.
    
    Args:
        results: List of GameResult objects
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "game_id", "agent_count", "context_condition", "specialization_index",
        "retrieval_efficiency", "cues_provided", "items_retrieved", "total_items",
        "timestamp"
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
    
    logger.log("write_results_csv_complete", path=str(output_path), rows=len(results))


def generate_scaling_analysis(results: List[GameResult], output_dir: Path) -> None:
    """
    Generate scaling analysis for different agent counts.
    
    This is a placeholder that will be implemented in T028.
    For now, it logs the data availability.
    """
    if not results:
        logger.log("scaling_analysis_skipped", reason="no_results")
        return
    
    # Group by agent count
    agent_counts = sorted(set(r.agent_count for r in results))
    logger.log("scaling_analysis_data", agent_counts=agent_counts)


def run_anova_analysis(results: List[GameResult], config: ExperimentConfig) -> Dict[str, Any]:
    """
    Run ANOVA analysis on the results.
    
    Args:
        results: List of GameResult objects
        config: Experiment configuration
        
    Returns:
        Dictionary with ANOVA results
    """
    if len(results) < 10:
        logger.log("anova_skipped", reason="insufficient_data")
        return {"error": "Insufficient data for ANOVA"}
    
    # Prepare data for ANOVA
    # We need: context_condition (factor A), metric_type (factor B), value
    data_rows = []
    for r in results:
        data_rows.append({
            "context": r.context_condition,
            "metric": "specialization",
            "value": r.specialization_index
        })
        data_rows.append({
            "context": r.context_condition,
            "metric": "retrieval",
            "value": r.retrieval_efficiency
        })
    
    # Convert to DataFrame-like structure for analysis
    df_data = {
        "context": [row["context"] for row in data_rows],
        "metric": [row["metric"] for row in data_rows],
        "value": [row["value"] for row in data_rows]
    }
    
    # Compute two-way ANOVA
    anova_result = compute_two_way_anova(df_data, factor_a="context", factor_b="metric", value_col="value")
    
    # Apply Bonferroni correction
    corrected_result = apply_bonferroni_correction(anova_result, n_tests=2)  # Two main effects + interaction
    
    logger.log("anova_complete", p_value=corrected_result.get("interaction_p", None))
    return asdict(corrected_result)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: 'full' or 'limited'"
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Number of agents (comma-separated list, e.g., '3,5,7')"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate per agent count"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default=None,
        help="Context window thresholds (comma-separated, e.g., '128,256,512')"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--no-anova",
        action="store_true",
        help="Skip ANOVA analysis"
    )
    parser.add_argument(
        "--plot",
        type=str,
        choices=["scaling"],
        default=None,
        help="Generate specific plots (e.g., 'scaling')"
    )
    return parser


def main():
    """Main entry point for the experiment runner."""
    parser = build_parser()
    args = parser.parse_args()
    
    # Configure experiment
    config = ExperimentConfig.from_args(args)
    
    # Ensure output directory exists
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set random seed
    random.seed(config.seed)
    
    # Run simulation
    logger.log("experiment_start", config=json.dumps(asdict(config, default=str)))
    results = run_simulation(config)
    
    # Determine output filename based on context
    if config.context == "full":
        output_filename = "results_full.csv"
    else:
        output_filename = "results_limited.csv"
    
    output_path = config.output_dir / output_filename
    
    # Write results to CSV
    write_results_csv(results, output_path)
    
    # Run ANOVA if requested
    if not args.no_anova:
        anova_results = run_anova_analysis(results, config)
        anova_path = config.output_dir / f"anova_{config.context}.json"
        with open(anova_path, "w") as f:
            json.dump(anova_results, f, indent=2, default=str)
        logger.log("anova_results_saved", path=str(anova_path))
    
    # Generate scaling analysis if requested
    if args.plot == "scaling":
        generate_scaling_analysis(results, config.output_dir)
    
    logger.log("experiment_complete", results_file=str(output_path), total_games=len(results))
    
    print(f"Experiment complete. Results written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())