"""Sensitivity analysis for token threshold variations.

This module implements a sensitivity analysis that sweeps token thresholds
across the set {128, 256, 512} and measures how specialization and retrieval
metrics vary for each threshold.

Per FR-008, this analysis must use REAL measurements from the experiment
simulation, not fabricated or random values.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import the experiment runner to simulate games with different thresholds
from run_experiment import GameConfig, simulate_one_game, run_simulation


def run_sensitivity_analysis(
    thresholds: List[int] = [128, 256, 512],
    num_games: int = 100,
    num_agents: int = 5,
    context_condition: str = "limited",
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Run sensitivity analysis across token thresholds.

    This function simulates games at each token threshold and computes
    specialization and retrieval metrics for each.

    Args:
        thresholds: List of token thresholds to test (default: [128, 256, 512])
        num_games: Number of games to simulate per threshold
        num_agents: Number of agents in the simulation
        context_condition: Context condition ('full' or 'limited')
        output_dir: Directory to write output CSV and JSON results
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing analysis results with keys:
            - 'thresholds': List of tested thresholds
            - 'results': List of result dictionaries per threshold
            - 'summary': Aggregated statistics
    """
    if seed is not None:
        np.random.seed(seed)

    if output_dir is None:
        output_dir = Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for threshold in thresholds:
        # Create config with specific token limit
        config = GameConfig(
            context=context_condition,
            agents=num_agents,
            games=num_games,
            token_limit=threshold,
            seed=seed + threshold if seed else None,
        )

        # Run simulation for this threshold
        game_results = run_simulation(config)

        if not game_results:
            print(f"Warning: No results for threshold {threshold}")
            continue

        # Compute metrics for this threshold
        specialization_values = []
        retrieval_values = []

        for result in game_results:
            if "specialization_index" in result and result["specialization_index"] is not None:
                specialization_values.append(result["specialization_index"])
            if "retrieval_efficiency" in result and result["retrieval_efficiency"] is not None:
                retrieval_values.append(result["retrieval_efficiency"])

        # Compute statistics
        spec_mean = np.mean(specialization_values) if specialization_values else 0.0
        spec_std = np.std(specialization_values) if specialization_values else 0.0
        ret_mean = np.mean(retrieval_values) if retrieval_values else 0.0
        ret_std = np.std(retrieval_values) if retrieval_values else 0.0

        threshold_result = {
            "threshold": threshold,
            "num_games": len(game_results),
            "specialization_mean": float(spec_mean),
            "specialization_std": float(spec_std),
            "retrieval_mean": float(ret_mean),
            "retrieval_std": float(ret_std),
            "specialization_values": specialization_values,
            "retrieval_values": retrieval_values,
        }
        results.append(threshold_result)

    # Compute overall summary
    all_spec = [r["specialization_mean"] for r in results]
    all_ret = [r["retrieval_mean"] for r in results]

    summary = {
        "threshold_range": f"{min(thresholds)}-{max(thresholds)}",
        "specialization_trend": "increasing" if all_spec[-1] > all_spec[0] else "decreasing",
        "retrieval_trend": "increasing" if all_ret[-1] > all_ret[0] else "decreasing",
        "specialization_sensitivity": float(all_spec[-1] - all_spec[0]),
        "retrieval_sensitivity": float(all_ret[-1] - all_ret[0]),
    }

    output_data = {
        "thresholds": thresholds,
        "results": results,
        "summary": summary,
        "config": {
            "num_games": num_games,
            "num_agents": num_agents,
            "context_condition": context_condition,
        },
    }

    # Write CSV output
    csv_path = output_dir / "sensitivity_analysis.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "threshold",
            "num_games",
            "specialization_mean",
            "specialization_std",
            "retrieval_mean",
            "retrieval_std",
        ])
        for r in results:
            writer.writerow([
                r["threshold"],
                r["num_games"],
                f"{r['specialization_mean']:.6f}",
                f"{r['specialization_std']:.6f}",
                f"{r['retrieval_mean']:.6f}",
                f"{r['retrieval_std']:.6f}",
            ])

    # Write JSON output
    json_path = output_dir / "sensitivity_analysis.json"
    # Remove non-serializable data for JSON
    json_results = []
    for r in results:
        json_results.append({
            "threshold": r["threshold"],
            "num_games": r["num_games"],
            "specialization_mean": r["specialization_mean"],
            "specialization_std": r["specialization_std"],
            "retrieval_mean": r["retrieval_mean"],
            "retrieval_std": r["retrieval_std"],
        })

    with open(json_path, "w") as f:
        json.dump({
            "thresholds": thresholds,
            "results": json_results,
            "summary": summary,
            "config": output_data["config"],
        }, f, indent=2)

    print(f"Sensitivity analysis complete. Results written to {output_dir}")
    print(f"Thresholds tested: {thresholds}")
    print(f"Specialization trend: {summary['specialization_trend']} "
          f"(change: {summary['specialization_sensitivity']:.4f})")
    print(f"Retrieval trend: {summary['retrieval_trend']} "
          f"(change: {summary['retrieval_sensitivity']:.4f})")

    return output_data


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for sensitivity analysis CLI."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on token thresholds"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma-separated list of token thresholds (default: 128,256,512)"
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games per threshold (default: 100)"
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents (default: 5)"
    )
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="limited",
        help="Context condition (default: limited)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    return parser


def main() -> None:
    """Main entry point for sensitivity analysis CLI."""
    parser = build_parser()
    args = parser.parse_args()

    thresholds = [int(t.strip()) for t in args.thresholds.split(",")]

    run_sensitivity_analysis(
        thresholds=thresholds,
        num_games=args.games,
        num_agents=args.agents,
        context_condition=args.context,
        output_dir=Path(args.output_dir),
        seed=args.seed,
    )


if __name__ == "__main__":
    main()