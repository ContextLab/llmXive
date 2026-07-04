"""Sensitivity analysis for token threshold variations.

Sweeps token thresholds across {128, 256, 512} and records how
specialization and retrieval metrics vary for each threshold.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import existing metrics from the project API surface
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from utils.logging import get_logger

# Import run_experiment components for simulation
from run_experiment import GameConfig, simulate_one_game

logger = get_logger(__name__)

DEFAULT_THRESHOLDS = [128, 256, 512]
DEFAULT_NUM_GAMES = 100  # Reduced for sensitivity sweep feasibility
DEFAULT_AGENTS = 5
DEFAULT_SEED = 42

def run_sensitivity_analysis(
    thresholds: List[int] = DEFAULT_THRESHOLDS,
    num_games: int = DEFAULT_NUM_GAMES,
    num_agents: int = DEFAULT_AGENTS,
    seed: int = DEFAULT_SEED,
    output_dir: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run sensitivity analysis across token thresholds.

    Args:
        thresholds: List of token thresholds to sweep (e.g., [128, 256, 512])
        num_games: Number of games to simulate per threshold
        num_agents: Number of agents per game
        seed: Random seed for reproducibility
        output_dir: Directory to write results (default: project results/)

    Returns:
        Tuple of (results_df, summary_stats)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "projects" / "PROJ-586-social-memory-networks-modeling-collecti" / "results"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.log("sensitivity_analysis_start", thresholds=thresholds, num_games=num_games, num_agents=num_agents)

    results = []
    summary_stats = {
        "thresholds": thresholds,
        "num_games_per_threshold": num_games,
        "num_agents": num_agents,
        "seed": seed,
        "results_by_threshold": {},
    }

    for threshold in thresholds:
        logger.log("sweep_threshold", threshold=threshold)
        threshold_results = []

        for game_id in range(num_games):
            # Create a game config with the specific token limit
            config = GameConfig(
                game_id=game_id,
                num_agents=num_agents,
                context_condition="limited",
                token_limit=threshold,
                seed=seed + game_id,  # Unique seed per game
            )

            try:
                # Run simulation
                result = simulate_one_game(game_id, config)

                # Extract metrics from result
                if result and "specialization_index" in result and "retrieval_efficiency" in result:
                    spec_index = result["specialization_index"]
                    ret_eff = result["retrieval_efficiency"]

                    threshold_results.append({
                        "game_id": game_id,
                        "token_threshold": threshold,
                        "specialization_index": spec_index,
                        "retrieval_efficiency": ret_eff,
                    })
            except Exception as e:
                logger.log("game_simulation_error", game_id=game_id, threshold=threshold, error=str(e))
                continue

        if threshold_results:
            df_threshold = pd.DataFrame(threshold_results)
            avg_spec = df_threshold["specialization_index"].mean()
            avg_ret = df_threshold["retrieval_efficiency"].mean()
            std_spec = df_threshold["specialization_index"].std()
            std_ret = df_threshold["retrieval_efficiency"].std()

            summary_stats["results_by_threshold"][str(threshold)] = {
                "mean_specialization": avg_spec,
                "mean_retrieval": avg_ret,
                "std_specialization": std_spec,
                "std_retrieval": std_ret,
                "num_games_completed": len(threshold_results),
            }

            results.extend(threshold_results)

    # Create final DataFrame
    if results:
        results_df = pd.DataFrame(results)
    else:
        results_df = pd.DataFrame(columns=[
            "game_id", "token_threshold", "specialization_index", "retrieval_efficiency"
        ])

    # Write CSV output
    csv_path = output_dir / "sensitivity_analysis_results.csv"
    if not results_df.empty:
        results_df.to_csv(csv_path, index=False)
        logger.log("results_csv_written", path=str(csv_path), rows=len(results_df))
    else:
        # Write empty file with headers
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["game_id", "token_threshold", "specialization_index", "retrieval_efficiency"])
        logger.log("empty_results_csv_written", path=str(csv_path))

    # Write JSON summary
    json_path = output_dir / "sensitivity_analysis_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary_stats, f, indent=2, default=str)
    logger.log("summary_json_written", path=str(json_path))

    logger.log("sensitivity_analysis_complete", num_results=len(results))

    return results_df, summary_stats

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis across token thresholds."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated list of token thresholds to sweep (default: 128,256,512)",
    )
    parser.add_argument(
        "--num-games",
        type=int,
        default=DEFAULT_NUM_GAMES,
        help=f"Number of games per threshold (default: {DEFAULT_NUM_GAMES})",
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=DEFAULT_AGENTS,
        help=f"Number of agents per game (default: {DEFAULT_AGENTS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: project results/)",
    )
    return parser

def main() -> int:
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args()

    thresholds = [int(t.strip()) for t in args.thresholds.split(",")]
    output_dir = args.output_dir if args.output_dir else None

    try:
        results_df, summary_stats = run_sensitivity_analysis(
            thresholds=thresholds,
            num_games=args.num_games,
            num_agents=args.agents,
            seed=args.seed,
            output_dir=output_dir,
        )

        print(f"Sensitivity analysis complete.")
        print(f"Results written to: {Path(output_dir or 'results') / 'sensitivity_analysis_results.csv'}")
        print(f"Summary written to: {Path(output_dir or 'results') / 'sensitivity_analysis_summary.json'}")
        print(f"\nSummary by threshold:")
        for thresh, stats in summary_stats["results_by_threshold"].items():
            print(f"  Threshold {thresh} tokens:")
            print(f"    Avg Specialization: {stats['mean_specialization']:.4f} (+/- {stats['std_specialization']:.4f})")
            print(f"    Avg Retrieval: {stats['mean_retrieval']:.4f} (+/- {stats['std_retrieval']:.4f})")
            print(f"    Games completed: {stats['num_games_completed']}")

        return 0

    except Exception as e:
        logger.log("sensitivity_analysis_failed", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())