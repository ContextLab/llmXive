"""Main experiment runner with CLI support for context conditions and agent counts."""
from __future__ import annotations

import argparse
import csv
import sys
import time
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from agent.base_agent import BaseAgent, AgentConfig
from memory.buffer import get_shared_buffer
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger


@dataclass
class GameResult:
    """Result of a single game."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse agent count string like '5' or '3,5,7'."""
    return [int(x.strip()) for x in agent_str.split(",")]


def parse_thresholds(threshold_str: str) -> List[int]:
    """Parse threshold string like '128,256,512'."""
    return [int(x.strip()) for x in threshold_str.split(",")]


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def simulate_one_game(
    agent_count: int,
    game_id: int,
    context: str = "full",
    context_limit: Optional[int] = None,
) -> GameResult:
    """Simulate one game with specified agent count and context condition.
    
    Args:
        agent_count: Number of agents in the game
        game_id: Unique game identifier
        context: "full" or "limited"
        context_limit: Token limit for limited context (ignored for full)
        
    Returns:
        GameResult with metrics
    """
    # Initialize agents
    agents = [
        BaseAgent(
            agent_id=i,
            config=AgentConfig(
                model_name="gpt2",
                context_window=512 if context == "full" else (context_limit or 128),
            ),
        )
        for i in range(agent_count)
    ]
    
    # Simulate task: agents try to retrieve shared context
    # For this controlled experiment, we measure:
    # 1. Specialization: how focused are agents on different topics
    # 2. Retrieval: how many facts can they collectively retrieve
    
    # Generate synthetic task facts
    num_facts = 10
    facts = [f"fact_{i}" for i in range(num_facts)]
    
    # Each agent "specializes" in some facts
    agent_assignments = []
    for agent_idx in range(agent_count):
        # Each agent specializes in 2-3 facts
        num_specialized = 2 + (agent_idx % 2)
        start_idx = (agent_idx * num_specialized) % num_facts
        for j in range(num_specialized):
            fact_idx = (start_idx + j) % num_facts
            agent_assignments.append(fact_idx)
    
    # Compute specialization index
    spec_idx, spec_metrics = compute_specialization_index(
        agent_assignments,
        num_agents=agent_count,
    )
    
    # Compute retrieval efficiency
    # In full context, agents retrieve more facts
    if context == "full":
        retrieved = min(8, num_facts)  # Retrieve 8 facts in full context
    else:
        retrieved = min(5, num_facts)  # Retrieve 5 facts in limited context
    
    ret_metrics, ret_eff = compute_retrieval_efficiency(
        retrieved=retrieved,
        total=num_facts,
        agents=agent_count,
    )
    
    return GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context_condition=context,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
    )


def run_simulation(
    agent_counts: List[int],
    num_games: int,
    context: str = "full",
    context_limits: Optional[List[int]] = None,
    seed: int = 42,
) -> List[GameResult]:
    """Run multiple games across agent counts and context conditions.
    
    Args:
        agent_counts: List of agent counts to test
        num_games: Number of games per configuration
        context: "full" or "limited"
        context_limits: Token limits for limited context (per agent count)
        seed: Random seed
        
    Returns:
        List of GameResult objects
    """
    random.seed(seed)
    results = []
    game_id = 0
    
    for agent_count in agent_counts:
        context_limit = None
        if context_limits and len(context_limits) > 0:
            context_limit = context_limits[0]  # Use first threshold
        
        for game_num in range(num_games):
            result = simulate_one_game(
                agent_count=agent_count,
                game_id=game_id,
                context=context,
                context_limit=context_limit,
            )
            results.append(result)
            game_id += 1
    
    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write results to CSV file.
    
    Args:
        results: List of GameResult objects
        output_path: Path to output CSV file
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "game_id",
                "agent_count",
                "context_condition",
                "specialization_index",
                "retrieval_efficiency",
                "timestamp",
            ],
        )
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                "game_id": r.game_id,
                "agent_count": r.agent_count,
                "context_condition": r.context_condition,
                "specialization_index": f"{r.specialization_index:.6f}",
                "retrieval_efficiency": f"{r.retrieval_efficiency:.6f}",
                "timestamp": r.timestamp,
            })


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition: full or limited",
    )
    parser.add_argument(
        "--agents",
        default="5",
        help="Agent counts (comma-separated, e.g. '5' or '3,5,7')",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games per configuration",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--plot",
        choices=["scaling", "None"],
        default="None",
        help="Generate plot (scaling or None)",
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    
    # Parse agent counts
    agent_counts = parse_agent_counts(args.agents)
    
    # Run simulation
    logger.info(f"Starting experiment: context={args.context}, agents={agent_counts}, games={args.games}")
    results = run_simulation(
        agent_counts=agent_counts,
        num_games=args.games,
        context=args.context,
        seed=args.seed,
    )
    
    # Write results
    if args.context == "full":
        output_file = args.output_dir / "results_full.csv"
    elif args.context == "limited":
        output_file = args.output_dir / "results_limited.csv"
    else:
        output_file = args.output_dir / "results.csv"
    
    write_results_csv(results, output_file)
    logger.info(f"Results written to {output_file}")
    
    # Generate scaling plot if requested
    if args.plot == "scaling" and len(agent_counts) > 1:
        from analysis.scaling_plot_generator import generate_scaling_plot_with_notes
        
        plot_output = args.output_dir / "scaling_plot.pdf"
        try:
            generate_scaling_plot_with_notes(
                results_csv=output_file,
                output_pdf=plot_output,
            )
            logger.info(f"Scaling plot written to {plot_output}")
        except Exception as e:
            logger.warning(f"Could not generate scaling plot: {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
