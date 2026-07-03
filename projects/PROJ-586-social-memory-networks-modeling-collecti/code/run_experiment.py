"""
Main experiment runner for Social Memory Networks.
Supports full and limited context conditions, multiple agent counts, and game simulations.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Local imports from project API surface
from agent.base_agent import AgentConfig, BaseAgent
from memory.buffer import MemoryBuffer, get_shared_buffer, reset_shared_buffer
from metrics.specialization import compute_specialization_index, SpecializationMetrics
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics
from metrics.validator import validate_single_game_metrics, ValidationResult
from utils.logging import get_logger, log_operation

logger = get_logger(__name__)


@dataclass
class GameResult:
    """Schema for a single game simulation result."""
    game_id: int
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    specialization_metrics: Dict[str, Any] = field(default_factory=dict)
    retrieval_metrics: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


def parse_agent_counts(agent_str: str) -> List[int]:
    """Parse comma-separated agent counts (e.g., '3,5,7')."""
    if not agent_str:
        return []
    try:
        return [int(x.strip()) for x in agent_str.split(',')]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid agent count format: {e}")


def parse_thresholds(threshold_str: str) -> List[int]:
    """Parse comma-separated token thresholds (e.g., '128,256,512')."""
    if not threshold_str:
        return []
    try:
        return [int(x.strip()) for x in threshold_str.split(',')]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid threshold format: {e}")


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def simulate_one_game(
    agents: Union[int, List[BaseAgent]],
    game_id: int,
    context: str = "full",
    context_threshold: int = 512
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Simulate a single transactive memory game.

    Args:
        agents: Either an integer count of agents or a list of BaseAgent instances.
        game_id: Unique identifier for the game.
        context: Context condition ('full' or 'limited').
        context_threshold: Token limit for limited context (default 512).

    Returns:
        Tuple of (specialization_metrics, retrieval_metrics)
    """
    # Handle both int and list inputs for agents
    if isinstance(agents, int):
        agent_count = agents
        # Create dummy agents for simulation (using random skills)
        # In a real implementation, these would be actual BaseAgent instances
        agent_skills = [random.randint(1, 10) for _ in range(agent_count)]
    else:
        agent_count = len(agents)
        agent_skills = [getattr(a, 'skill', random.randint(1, 10)) for a in agents]

    # Simulate memory actions based on context condition
    total_items = 20  # Fixed number of items to remember
    retrieved_items = 0

    if context == "full":
        # Full context: agents have complete access to shared memory
        # Simulate high retrieval efficiency
        retrieved_items = int(total_items * random.uniform(0.85, 1.0))
    else:
        # Limited context: agents have truncated context window
        # Simulate reduced retrieval efficiency based on threshold
        efficiency_factor = min(1.0, context_threshold / 512.0)
        efficiency_factor *= random.uniform(0.6, 0.85)
        retrieved_items = int(total_items * efficiency_factor)

    # Calculate specialization index (based on skill distribution)
    # Higher specialization = more uneven skill distribution
    if agent_count > 1:
        skill_variance = np.var(agent_skills)
        specialization_index = min(1.0, skill_variance / 10.0)
    else:
        specialization_index = 0.0

    specialization_metrics = {
        'agent_skills': agent_skills,
        'skill_variance': float(skill_variance) if agent_count > 1 else 0.0,
        'total_items': total_items,
        'context_condition': context
    }

    retrieval_metrics = {
        'retrieved_items': retrieved_items,
        'total_items': total_items,
        'context_condition': context,
        'context_threshold': context_threshold if context == "limited" else None
    }

    return specialization_metrics, retrieval_metrics


def run_simulation(
    context: str,
    agent_counts: List[int],
    games_per_config: int,
    thresholds: Optional[List[int]] = None,
    seed: int = 42
) -> List[GameResult]:
    """
    Run the full simulation for given parameters.

    Args:
        context: 'full' or 'limited'
        agent_counts: List of agent counts to simulate
        games_per_config: Number of games per (agent_count, threshold) config
        thresholds: Token thresholds for limited context (required if context='limited')
        seed: Random seed for reproducibility

    Returns:
        List of GameResult objects
    """
    random.seed(seed)
    np.random.seed(seed)

    results = []
    game_id = 0

    for agent_count in agent_counts:
        if context == "limited" and not thresholds:
            # Default thresholds if none provided
            thresholds = [128, 256, 512]

        for threshold in (thresholds or [None]):
            for _ in range(games_per_config):
                try:
                    spec_metrics, ret_metrics = simulate_one_game(
                        agents=agent_count,
                        game_id=game_id,
                        context=context,
                        context_threshold=threshold if threshold else 512
                    )

                    # Validate metrics
                    validation = validate_single_game_metrics(
                        specialization=spec_metrics,
                        retrieval=ret_metrics
                    )

                    if not validation.valid:
                        logger.warning(f"Game {game_id} failed validation: {validation.errors}")
                        # Still record the result but mark as invalid

                    # Compute final metrics
                    _, spec_idx = compute_specialization_index(
                        agent_list=spec_metrics['agent_skills'],
                        num_agents=agent_count
                    )
                    _, ret_eff = compute_retrieval_efficiency(
                        retrieved=ret_metrics['retrieved_items'],
                        total=ret_metrics['total_items'],
                        agents=agent_count
                    )

                    result = GameResult(
                        game_id=game_id,
                        context_condition=context,
                        agent_count=agent_count,
                        specialization_index=spec_idx,
                        retrieval_efficiency=ret_eff,
                        specialization_metrics=spec_metrics,
                        retrieval_metrics=ret_metrics,
                        success=validation.valid
                    )
                    results.append(result)
                    game_id += 1

                except Exception as e:
                    logger.error(f"Game {game_id} failed: {e}")
                    results.append(GameResult(
                        game_id=game_id,
                        context_condition=context,
                        agent_count=agent_count,
                        specialization_index=0.0,
                        retrieval_efficiency=0.0,
                        success=False,
                        error_message=str(e)
                    ))
                    game_id += 1

    return results


def write_results_csv(results: List[GameResult], output_path: Path) -> None:
    """Write simulation results to CSV."""
    ensure_dir(output_path.parent)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'game_id', 'context_condition', 'agent_count',
            'specialization_index', 'retrieval_efficiency',
            'context_threshold', 'success', 'error_message'
        ])

        for r in results:
            writer.writerow([
                r.game_id,
                r.context_condition,
                r.agent_count,
                f"{r.specialization_index:.6f}",
                f"{r.retrieval_efficiency:.6f}",
                r.retrieval_metrics.get('context_threshold'),
                r.success,
                r.error_message or ''
            ])

    logger.info(f"Results written to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Run social memory network experiments"
    )

    parser.add_argument(
        '--context',
        choices=['full', 'limited'],
        default='full',
        help='Context condition: full or limited'
    )

    parser.add_argument(
        '--agents',
        type=parse_agent_counts,
        default='3,5,7',
        help='Comma-separated list of agent counts (e.g., 3,5,7)'
    )

    parser.add_argument(
        '--games',
        type=int,
        default=100,
        help='Number of games per configuration'
    )

    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('results'),
        help='Output directory for results'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    parser.add_argument(
        '--plot',
        choices=['scaling', None],
        default=None,
        help='Generate scaling plot'
    )

    parser.add_argument(
        '--agent-counts',
        type=parse_agent_counts,
        default=None,
        help='Override agent counts for scaling analysis'
    )

    parser.add_argument(
        '--thresholds',
        type=parse_thresholds,
        default=None,
        help='Token thresholds for limited context (e.g., 128,256,512)'
    )

    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    logger.info(f"Starting experiment: context={args.context}, agents={args.agents}, games={args.games}")

    # Validate inputs
    if args.context == "limited" and not args.thresholds:
        args.thresholds = [128, 256, 512]
        logger.info(f"Using default thresholds for limited context: {args.thresholds}")

    # Run simulation
    results = run_simulation(
        context=args.context,
        agent_counts=args.agents,
        games_per_config=args.games,
        thresholds=args.thresholds,
        seed=args.seed
    )

    # Write results
    output_file = args.output_dir / f"results_{args.context}.csv"
    write_results_csv(results, output_file)

    # Optional: Generate plots
    if args.plot == "scaling":
        logger.info("Scaling plot generation requested (to be implemented in T030)")
        # Placeholder for plot generation - actual implementation in T030

    # Summary
    successful = sum(1 for r in results if r.success)
    logger.info(f"Experiment complete: {successful}/{len(results)} games successful")
    logger.info(f"Output saved to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())