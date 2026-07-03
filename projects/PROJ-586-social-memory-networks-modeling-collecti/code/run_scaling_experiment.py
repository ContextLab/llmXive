"""
Scaling Experiment Runner.

Runs simulations for varying agent counts (3, 5, 7) and generates
a scaling plot with power-law fitting.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List

import pandas as pd

from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger
from run_experiment import simulate_one_game

logger = get_logger(__name__)

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def run_simulations_for_count(
    agent_count: int,
    games: int,
    seed: int,
    context: str = "full"
) -> List[dict]:
    """Run simulations for a single agent count."""
    results = []
    for i in range(games):
        game_id = i
        _, result = simulate_one_game(agent_count, game_id, context, seed + i)
        results.append({
            "agent_count": agent_count,
            "specialization_index": result.specialization_index,
            "retrieval_efficiency": result.retrieval_efficiency,
            "game_id": game_id
        })
    return results

def write_csv(results: List[dict], path: Path) -> None:
    """Write scaling results to CSV."""
    ensure_dir(path.parent)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["agent_count", "specialization_index", "retrieval_efficiency", "game_id"])
        writer.writeheader()
        writer.writerows(results)

def build_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Run Scaling Experiment")
    parser.add_argument("--agents", type=str, default="3,5,7", help="Agent counts")
    parser.add_argument("--games", type=int, default=100, help="Games per count")
    parser.add_argument("--seed", type=int, default=42, help="Seed")
    parser.add_argument("--context", type=str, default="full", choices=["full", "limited"])
    parser.add_argument("--output", type=Path, default=Path("results/scaling_data.csv"))
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    
    agent_counts = [int(x) for x in args.agents.split(",")]
    all_results = []
    
    for count in agent_counts:
        logger.info(f"Running scaling simulation for N={count}...")
        results = run_simulations_for_count(count, args.games, args.seed, args.context)
        all_results.extend(results)
        
    write_csv(all_results, args.output)
    logger.info(f"Scaling data written to {args.output}")
    
    # Generate plot if requested
    if hasattr(args, 'plot') and args.plot == 'scaling':
        try:
            from analysis.scaling import generate_scaling_plot
            # Load data back to generate plot
            df = pd.read_csv(args.output)
            plot_path = Path("results/scaling_plot.pdf")
            generate_scaling_plot(df, plot_path)
            logger.info(f"Scaling plot written to {plot_path}")
        except Exception as e:
            logger.warning(f"Failed to generate plot: {e}")
            
    return 0

if __name__ == "__main__":
    sys.exit(main())
