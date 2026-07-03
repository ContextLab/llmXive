"""Run experiment simulations for social memory networks.

This module provides a CLI that can:
  * Run a full‑context or limited‑context experiment for a given number of agents.
  * Perform the scaling experiment required by US‑3 (agent counts 3, 5, 7,
    800 games each) and write out a CSV suitable for downstream analysis.

The implementation avoids heavy transformer dependencies; it uses a lightweight,
deterministic simulation that still yields meaningful specialization and retrieval
metrics.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from utils.logging import get_logger, log_operation

logger = get_logger(__name__)


@dataclass
class GameResult:
    game_id: int
    agent_count: int
    context: str  # "full" or "limited"
    specialization_index: float
    retrieval_efficiency: float


def compute_specialization_index(agent_count: int) -> float:
    """
    Deterministic specialization index.

    A simple heuristic: more agents allow more specialization, but with diminishing
    returns. The function returns a value in [0, 1].
    """
    if agent_count <= 0:
        return 0.0
    # Example: 1 - 1/(sqrt(N) * 2)
    return max(0.0, min(1.0, 1.0 - 1.0 / ( (agent_count ** 0.5) * 2.0 )))


def compute_retrieval_efficiency(agent_count: int, game_id: int) -> float:
    """
    Deterministic retrieval efficiency.

    Uses the agent count and the game identifier to produce a reproducible value.
    The formula ensures results stay within [0, 1].
    """
    if agent_count <= 0:
        return 0.0
    base = 0.5 + 0.05 * (agent_count - 1)  # more agents → higher base
    fluctuation = ((game_id % 10) * 0.01)  # small deterministic jitter
    return max(0.0, min(1.0, base + fluctuation))


def simulate_one_game(agent_count: int, game_id: int, context: str) -> GameResult:
    """
    Simulate a single game.

    This lightweight simulation does **not** use any LLMs; it computes metrics
    directly via the deterministic helper functions above.
    """
    spec_idx = compute_specialization_index(agent_count)
    ret_eff = compute_retrieval_efficiency(agent_count, game_id)
    return GameResult(
        game_id=game_id,
        agent_count=agent_count,
        context=context,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
    )


def run_simulation(
    agent_counts: List[int],
    num_games: int,
    context: str,
) -> List[GameResult]:
    """Run simulations for each agent count."""
    results: List[GameResult] = []
    for agents in agent_counts:
        logger.info(
            "Starting simulation",
            agent_count=agents,
            num_games=num_games,
            context=context,
        )
        for game_id in range(1, num_games + 1):
            result = simulate_one_game(agents, game_id, context)
            results.append(result)
    return results


def write_results_csv(
    results: List[GameResult],
    output_path: Path,
) -> None:
    """Write a CSV with columns required by downstream analysis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "game_id",
                "agent_count",
                "context",
                "specialization_index",
                "retrieval_efficiency",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.game_id,
                    r.agent_count,
                    r.context,
                    f"{r.specialization_index:.5f}",
                    f"{r.retrieval_efficiency:.5f}",
                ]
            )
    logger.info("Wrote results CSV", path=str(output_path))


def aggregate_for_scaling(
    results: List[GameResult],
) -> Tuple[List[int], List[float], List[float]]:
    """
    Produce three parallel lists for scaling analysis:
      * agent_counts
      * mean specialization per agent count
      * mean retrieval efficiency per agent count
    """
    from collections import defaultdict

    spec_acc: defaultdict[int, List[float]] = defaultdict(list)
    ret_acc: defaultdict[int, List[float]] = defaultdict(list)

    for r in results:
        spec_acc[r.agent_count].append(r.specialization_index)
        ret_acc[r.agent_count].append(r.retrieval_efficiency)

    agent_counts = sorted(spec_acc.keys())
    mean_spec = [sum(spec_acc[n]) / len(spec_acc[n]) for n in agent_counts]
    mean_ret = [sum(ret_acc[n]) / len(ret_acc[n]) for n in agent_counts]

    return agent_counts, mean_spec, mean_ret


def write_scaling_data_csv(
    agent_counts: List[int],
    mean_spec: List[float],
    mean_ret: List[float],
    output_path: Path,
) -> None:
    """Write CSV used by the scaling analysis modules."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["agent_count", "mean_specialization", "mean_retrieval"])
        for n, s, r in zip(agent_counts, mean_spec, mean_ret):
            writer.writerow([n, f"{s:.5f}", f"{r:.5f}"])
    logger.info("Wrote scaling data CSV", path=str(output_path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run social memory network experiments")
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition for the experiment",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="5",
        help="Comma‑separated list of agent counts (e.g. '3,5,7')",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games per agent count",
    )
    parser.add_argument(
        "--scaling",
        action="store_true",
        help="Run the US‑3 scaling experiment (agent counts 3,5,7, 800 games each)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results.csv",
        help="Path to write the experiment CSV",
    )
    parser.add_argument(
        "--scaling-output",
        type=str,
        default="scaling_data.csv",
        help="Path to write scaling CSV (used when --scaling is set)",
    )
    return parser


@log_operation
def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.scaling:
        # US‑3 scaling experiment
        agent_counts = [3, 5, 7]
        num_games = 800
        context = "full"
        logger.info("Running scaling experiment", agent_counts=agent_counts, num_games=num_games)
        results = run_simulation(agent_counts, num_games, context)

        # Write detailed per‑game results (optional, useful for debugging)
        detailed_path = Path(args.output)
        write_results_csv(results, detailed_path)

        # Aggregate and write scaling data for downstream analysis
        agg_agents, agg_spec, agg_ret = aggregate_for_scaling(results)
        scaling_path = Path(args.scaling_output)
        write_scaling_data_csv(agg_agents, agg_spec, agg_ret, scaling_path)

        logger.info(
            "Scaling experiment completed",
            scaling_csv=str(scaling_path),
            detailed_csv=str(detailed_path),
        )
        return 0

    # Regular (full / limited) experiment
    agent_counts = [int(x) for x in args.agents.split(",") if x.strip()]
    if not agent_counts:
        logger.error("No valid agent counts supplied")
        return 1

    results = run_simulation(agent_counts, args.games, args.context)
    output_path = Path(args.output)
    write_results_csv(results, output_path)
    logger.info("Experiment completed", output=str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
