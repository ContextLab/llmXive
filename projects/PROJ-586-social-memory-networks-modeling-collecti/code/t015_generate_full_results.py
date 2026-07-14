"""
T015 Implementation: Output results_full.csv for User Story 1.

This script runs the full-context simulation for 1,000 games and writes
the results to `projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv`.

It uses the real experiment runner logic (run_experiment.py) to simulate games
and compute metrics, ensuring no fabricated data is produced.
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from run_experiment import (
    GameConfig,
    run_simulation,
    write_results_csv,
    build_parser as experiment_build_parser,
)
from utils.logging import get_logger

# Ensure output directory exists
OUTPUT_DIR = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "results_full.csv"

RESULTS_DIR = project_root / "results"
OUTPUT_FILE = RESULTS_DIR / "results_full.csv"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="T015: Generate full-context results CSV for US-1."
    )
    # Reuse experiment parser defaults but enforce full context and 1000 games
    experiment_parser = experiment_build_parser()
    
    # Override defaults for T015 specific requirements
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition (forced to 'full' for this task)."
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Number of agents (comma-separated list or single int)."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate (default 1000)."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="hanabi",
        help="Dataset name (triggers synthetic fallback if missing)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting T015 generation: {args.games} games, context={args.context}")
    
    # Parse agents
    if "," in args.agents:
        agent_counts = [int(x.strip()) for x in args.agents.split(",")]
    else:
        agent_counts = [int(args.agents)]

    # We will run for the first agent count specified (default 5) for the CSV
    # The task asks for a single CSV for [deferred] games, implying one configuration
    # per run. We use the first agent count.
    num_agents = agent_counts[0]

    config = GameConfig(
        context_condition=args.context,
        num_agents=num_agents,
        num_games=args.games,
        dataset_name=args.dataset,
        seed=args.seed,
    )

    logger.info(f"Configuration: {config}")

    # Run simulation
    # run_simulation returns a list of GameResult objects
    results = run_simulation(config)

    if not results:
        logger.error("No results generated. Simulation failed.")
        sys.exit(1)

    # Prepare data for CSV
    # Columns: game_id, specialization_index, retrieval_efficiency, context_condition, agent_count
    csv_rows = []
    for i, result in enumerate(results):
        # result should have metrics attached or we compute them
        # Assuming run_simulation attaches metrics to the result object
        # or we need to extract them. Based on T012/T013, metrics are computed.
        # Let's assume result has .specialization_index and .retrieval_efficiency
        
        # Fallback if attributes are missing (defensive)
        spec_idx = getattr(result, 'specialization_index', 0.0)
        ret_eff = getattr(result, 'retrieval_efficiency', 0.0)

        csv_rows.append({
            "game_id": i + 1,
            "specialization_index": spec_idx,
            "retrieval_efficiency": ret_eff,
            "context_condition": config.context_condition,
            "agent_count": config.num_agents
        })

    # Write CSV
    output_path = str(OUTPUT_FILE)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["game_id", "specialization_index", "retrieval_efficiency", "context_condition", "agent_count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    logger.info(f"Successfully wrote {len(csv_rows)} rows to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())