"""
Main experiment runner for social memory networks.

This script orchestrates the full experiment pipeline, including
full-context and limited-context simulations, and outputs results
to CSV files.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from t015_generate_full_results import run_simulation as run_full_simulation
from utils.logging import get_logger

logger = get_logger(__name__)


def parse_agent_counts(agent_string: str) -> List[int]:
    """
    Parse agent count string (e.g., "3,5,7" or "5").

    Args:
        agent_string: Comma-separated list or single number

    Returns:
        List of agent counts
    """
    if "," in agent_string:
        return [int(x.strip()) for x in agent_string.split(",")]
    return [int(agent_string)]


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def write_results_csv(
    results: List[dict],
    output_path: Path,
    fieldnames: List[str],
) -> None:
    """Write results to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def run_simulation(
    context: str,
    agent_counts: List[int],
    games_per_config: int,
    seed: int = 42,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Run simulation for given context and agent configurations.

    Args:
        context: Context condition ("full" or "limited")
        agent_counts: List of agent counts to test
        games_per_config: Number of games per configuration
        seed: Random seed
        output_dir: Output directory for results

    Returns:
        Path to output CSV file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "results"

    ensure_dir(output_dir)

    all_results: List[dict] = []

    for agent_count in agent_counts:
        logger.info(
            "Running simulation",
            context=context,
            agents=agent_count,
            games=games_per_config,
        )

        results = run_full_simulation(
            num_games=games_per_config,
            agent_count=agent_count,
            context=context,
            seed=seed,
            output_path=None,  # We'll write manually
        )

        for result in results:
            all_results.append({
                "game_id": result.game_id,
                "specialization_index": result.specialization_index,
                "retrieval_efficiency": result.retrieval_efficiency,
                "context_condition": result.context_condition,
                "agent_count": result.agent_count,
            })

    # Determine output filename
    if context == "full":
        output_path = output_dir / "results_full.csv"
    else:
        output_path = output_dir / "results_limited.csv"

    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]

    write_results_csv(all_results, output_path, fieldnames)
    logger.info("Results written", path=str(output_path), count=len(all_results))

    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )
    parser.add_argument(
        "--context",
        type=str,
        default="full",
        choices=["full", "limited"],
        help="Context condition",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent counts (comma-separated or single number)",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Games per configuration",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory",
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    agent_counts = parse_agent_counts(args.agents)
    output_dir = Path(args.output_dir) if args.output_dir else None

    logger.info("Starting experiment", context=args.context, agents=agent_counts)

    output_path = run_simulation(
        context=args.context,
        agent_counts=agent_counts,
        games_per_config=args.games,
        seed=args.seed,
        output_dir=output_dir,
    )

    logger.info("Experiment complete", output=str(output_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())