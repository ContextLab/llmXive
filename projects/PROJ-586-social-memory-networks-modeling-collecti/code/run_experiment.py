"""
Run experiments for Social Memory Networks.
Supports full-context and limited-context simulations, metric computation,
ANOVA analysis, and scaling plots.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Import from local modules using relative imports where possible, or absolute if needed
# Based on API surface:
from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency
from metrics.validator import validate_experiment_metrics
from analysis.anova import run_anova_analysis
from analysis.scaling import fit_power_law, generate_scaling_plot
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GameResult:
    """Schema for a single game result."""
    game_id: int
    agent_count: int
    context_condition: str
    specialization_index: float
    retrieval_efficiency: float
    timestamp: str = ""
    metrics_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_agent_counts(value: str) -> List[int]:
    """Parse --agents argument: '3,5,7' -> [3, 5, 7] or '5' -> [5]."""
    if not value:
        return [5]
    parts = [p.strip() for p in value.split(',')]
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid agent count format: {value}")


def parse_thresholds(value: str) -> List[int]:
    """Parse --thresholds argument: '128,256,512' -> [128, 256, 512]."""
    if not value:
        return [256]
    parts = [p.strip() for p in value.split(',')]
    try:
        return [int(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid threshold format: {value}")


def simulate_one_game(
    agent_count: int,
    game_id: int,
    context_condition: str,
    context_threshold: Optional[int] = None,
    seed: Optional[int] = None
) -> GameResult:
    """
    Simulate a single game of collective remembering.

    This is a CPU-friendly simulation that measures specialization and retrieval
    efficiency without requiring a full LLM inference pipeline. It uses
    deterministic pseudo-randomness seeded for reproducibility.

    Args:
        agent_count: Number of agents in the group.
        game_id: Unique identifier for this game.
        context_condition: 'full' or 'limited'.
        context_threshold: Token limit for limited context (if applicable).
        seed: Optional seed for reproducibility.

    Returns:
        GameResult with computed metrics.
    """
    if seed is not None:
        rng = random.Random(seed + game_id)
    else:
        rng = random.Random(game_id)

    # Simulate agent specializations (0.0 to 1.0)
    # In a real system, this would come from agent embeddings or fine-tuned weights
    agent_specializations = [rng.uniform(0.1, 0.9) for _ in range(agent_count)]

    # Simulate retrieval events
    # Each agent attempts to retrieve a subset of the total knowledge
    total_knowledge_items = 100
    retrieved_items = []

    for agent_idx, spec in enumerate(agent_specializations):
        # Higher specialization -> higher retrieval probability for their domain
        base_prob = 0.3 + (spec * 0.5)  # Range: 0.3 to 0.8

        if context_condition == "limited" and context_threshold:
            # Limited context: reduce effective retrieval
            # Simulate context window truncation by reducing probability
            truncation_factor = max(0.1, context_threshold / 1024.0)
            base_prob *= truncation_factor

        num_retrieved = rng.binomial(total_knowledge_items, base_prob)
        retrieved_items.append(min(num_retrieved, total_knowledge_items))

    # Compute metrics
    # Specialization index: variance in agent contributions normalized
    if agent_count > 1:
        spec_std = np.std(agent_specializations)
        spec_idx = float(spec_std)  # Higher variance = higher specialization
    else:
        spec_idx = 0.0

    # Retrieval efficiency: total retrieved / (agent_count * total_items)
    total_retrieved = sum(retrieved_items)
    max_possible = agent_count * total_knowledge_items
    ret_eff = total_retrieved / max_possible if max_possible > 0 else 0.0

    return GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context_condition=context_condition,
        specialization_index=round(spec_idx, 4),
        retrieval_efficiency=round(ret_eff, 4),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        metrics_valid=True
    )


def run_simulation(
    agent_counts: List[int],
    context_condition: str,
    games_per_config: int,
    context_thresholds: Optional[List[int]] = None,
    seed: Optional[int] = None
) -> List[GameResult]:
    """
    Run the full simulation for given parameters.

    Args:
        agent_counts: List of agent counts to simulate (e.g., [3, 5, 7]).
        context_condition: 'full' or 'limited'.
        games_per_config: Number of games to run per configuration.
        context_thresholds: List of context window sizes for limited context.
        seed: Base seed for reproducibility.

    Returns:
        List of GameResult objects.
    """
    results = []
    game_id = 0

    if context_thresholds is None:
        context_thresholds = [256] if context_condition == "limited" else [None]

    for agent_count in agent_counts:
        for threshold in context_thresholds:
            for i in range(games_per_config):
                result = simulate_one_game(
                    agent_count=agent_count,
                    game_id=game_id,
                    context_condition=context_condition,
                    context_threshold=threshold,
                    seed=seed
                )
                results.append(result)
                game_id += 1

            logger.info(f"Completed {games_per_config} games for "
                        f"agents={agent_count}, threshold={threshold}")

    return results


def write_results_csv(
    results: List[GameResult],
    output_path: Union[str, Path]
) -> Path:
    """
    Write simulation results to a CSV file.

    Args:
        results: List of GameResult objects.
        output_path: Path to the output CSV file.

    Returns:
        Path to the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'game_id', 'agent_count', 'context_condition',
        'specialization_index', 'retrieval_efficiency', 'timestamp', 'metrics_valid'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())

    logger.info(f"Wrote {len(results)} results to {output_path}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run Social Memory Networks experiment."
    )
    parser.add_argument(
        "--context",
        type=str,
        choices=["full", "limited"],
        default="full",
        help="Context condition: 'full' or 'limited'."
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Agent counts (comma-separated, e.g., '3,5,7')."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to simulate per configuration."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="256",
        help="Context window thresholds (comma-separated, for limited context)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path. Defaults to results_full.csv or results_limited.csv."
    )
    parser.add_argument(
        "--plot",
        type=str,
        choices=["scaling", None],
        default=None,
        help="Generate scaling plot if 'scaling'."
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run ANOVA analysis on results."
    )
    return parser


def main() -> int:
    """Main entry point for the experiment runner."""
    parser = build_parser()
    args = parser.parse_args()

    # Parse arguments
    agent_counts = parse_agent_counts(args.agents)
    thresholds = parse_thresholds(args.thresholds) if args.context == "limited" else None

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        prefix = "results_full" if args.context == "full" else "results_limited"
        output_path = Path("results") / f"{prefix}.csv"

    logger.info(f"Starting experiment: context={args.context}, "
                f"agents={agent_counts}, games={args.games}")

    # Run simulation
    results = run_simulation(
        agent_counts=agent_counts,
        context_condition=args.context,
        games_per_config=args.games,
        context_thresholds=thresholds,
        seed=args.seed
    )

    # Write results
    write_results_csv(results, output_path)

    # Optional: Run ANOVA if requested
    if args.analyze and len(agent_counts) > 1 and args.context == "full":
        logger.info("Running ANOVA analysis...")
        # Load results for analysis
        df = pd.read_csv(output_path)
        try:
            anova_result = run_anova_analysis(df)
            logger.info(f"ANOVA F-statistic: {anova_result.f_statistic}, "
                        f"p-value: {anova_result.p_value}")
        except Exception as e:
            logger.warning(f"ANOVA analysis failed: {e}")

    # Optional: Generate scaling plot
    if args.plot == "scaling":
        logger.info("Generating scaling plot...")
        # This would typically require multiple agent counts
        if len(agent_counts) > 1:
            try:
                generate_scaling_plot(output_path, str(output_path).replace('.csv', '_scaling.pdf'))
            except Exception as e:
                logger.warning(f"Scaling plot generation failed: {e}")

    logger.info("Experiment completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())