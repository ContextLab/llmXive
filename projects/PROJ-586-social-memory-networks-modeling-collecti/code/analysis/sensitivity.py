"""
Sensitivity analysis for token thresholds.

Sweeps token thresholds {128, 256, 512} and measures how specialization and
retrieval metrics vary under each constraint.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Local imports from the project's existing API surface
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

# Import the experiment runner components to simulate games with truncation
# Note: We import the functions directly to avoid circular issues if any
from run_experiment import truncate_context_to_token_limit, simulate_one_game, GameConfig

@dataclass
class SensitivityResult:
    """Holds the aggregated results for a single threshold."""
    threshold: int
    specialization_index: float
    retrieval_efficiency: float
    games_run: int
    failed_games: int

def run_sensitivity_analysis(
    thresholds: List[int] | None = None,
    num_games: int = 100,
    num_agents: int = 5,
    dataset: str = "synthetic",
    seed: int = 42,
    output_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
) -> List[SensitivityResult]:
    """
    Run the sensitivity analysis by sweeping token thresholds.

    For each threshold, we simulate `num_games` and compute the average
    specialization index and retrieval efficiency.

    Args:
        thresholds: List of token limits to test. Defaults to [128, 256, 512].
        num_games: Number of games to simulate per threshold.
        num_agents: Number of agents in the simulation.
        dataset: Dataset name (triggers synthetic fallback if not real).
        seed: Random seed for reproducibility.
        output_dir: Directory to write results CSV.

    Returns:
        List of SensitivityResult objects.
    """
    if thresholds is None:
        thresholds = [128, 256, 512]

    logger = get_logger(__name__)
    np.random.seed(seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "sensitivity_analysis.csv"

    results: List[SensitivityResult] = []

    logger.log("sensitivity_analysis_start", thresholds=thresholds, num_games=num_games)

    for threshold in thresholds:
        logger.log("sensitivity_threshold_start", threshold=threshold)

        spec_values = []
        ret_values = []
        failed_count = 0

        # Simulate games for this threshold
        for game_id in range(num_games):
            try:
                # Construct config with the specific truncation limit
                config = GameConfig(
                    context_limit=threshold,
                    num_agents=num_agents,
                    dataset=dataset,
                    seed=seed + game_id
                )

                # Run simulation
                result = simulate_one_game(config, game_id)

                # Compute metrics
                # Note: simulate_one_game returns a result object with facts_per_agent, etc.
                # We re-calculate metrics to ensure they are based on the actual run
                spec_idx, _ = compute_specialization_index(
                    result.facts_per_agent,
                    num_agents=num_agents
                )
                ret_eff, _ = compute_retrieval_efficiency(
                    result.successful_retrievals,
                    result.total_queries,
                    num_agents
                )

                spec_values.append(spec_idx)
                ret_values.append(ret_eff)

            except Exception as e:
                logger.log("sensitivity_game_failed", game_id=game_id, error=str(e))
                failed_count += 1
                continue

        # Aggregate metrics for this threshold
        avg_spec = float(np.mean(spec_values)) if spec_values else 0.0
        avg_ret = float(np.mean(ret_values)) if ret_values else 0.0

        res = SensitivityResult(
            threshold=threshold,
            specialization_index=avg_spec,
            retrieval_efficiency=avg_ret,
            games_run=num_games - failed_count,
            failed_games=failed_count
        )
        results.append(res)
        logger.log("sensitivity_threshold_complete", threshold=threshold, avg_spec=avg_spec, avg_ret=avg_ret)

    # Write CSV output
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "threshold", "specialization_index", "retrieval_efficiency",
            "games_run", "failed_games"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "threshold": r.threshold,
                "specialization_index": r.specialization_index,
                "retrieval_efficiency": r.retrieval_efficiency,
                "games_run": r.games_run,
                "failed_games": r.failed_games
            })

    logger.log("sensitivity_analysis_complete", output_path=str(csv_path))
    return results

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on token thresholds.")
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated list of token thresholds to test."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per threshold."
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Directory for output files."
    )
    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    thresholds = [int(x.strip()) for x in args.thresholds.split(",")]

    run_sensitivity_analysis(
        thresholds=thresholds,
        num_games=args.games,
        num_agents=args.agents,
        seed=args.seed,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()