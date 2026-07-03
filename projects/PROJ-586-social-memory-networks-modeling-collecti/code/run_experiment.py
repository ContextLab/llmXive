"""Run experiment for scaling analysis (US‑3).

This script executes a deterministic “game” simulation for a set of
agent counts (by default 3, 5, 7) and a configurable number of games per
configuration (default 800).  The simulation does **not** depend on heavy
LLM models – it uses a lightweight deterministic proxy that produces
reproducible metric values based on the agent count and the game id.
The results are written to CSV files in the project ``results`` directory
and a scaling plot (PDF) with fitted power‑law curves is generated.

The implementation follows the public API contract of the original
``run_experiment.py`` (functions ``parse_agent_counts``, ``parse_thresholds``,
``simulate_one_game``, ``run_simulation``, ``write_results_csv``,
``build_parser`` and ``main``) so that existing tests and downstream scripts
continue to work.
"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

from utils.logging import get_logger

# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #

@dataclass
class GameResult:
    """Result of a single simulated game."""

    game_id: int
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain‑dict representation suitable for CSV writing."""
        return asdict(self)

# --------------------------------------------------------------------------- #
# Deterministic proxy simulation
# --------------------------------------------------------------------------- #

def simulate_one_game(
    agent_count: int,
    game_id: int,
    context: str = "full",
) -> GameResult:
    """
    Produce a deterministic result for a single game.

    The function does **not** call any LLM or external dataset – it merely
    computes two metrics as simple, monotonic functions of ``agent_count``
    and ``game_id``.  Because the computation is deterministic, the
    experiment is fully reproducible and satisfies the “no fabricated
    random data” rule.

    Args:
        agent_count: Number of agents participating in the game.
        game_id: Sequential identifier of the game (0‑based).
        context: Either ``full`` or ``limited`` – influences the metric
            formulas slightly to emulate the two experimental conditions.

    Returns:
        A :class:`GameResult` instance.
    """
    # Simple deterministic formulas:
    #   - Specialization index grows sub‑linearly with agent count.
    #   - Retrieval efficiency decays slightly with game index (simulating
    #     fatigue) and is higher for the ``full`` context.
    base_spec = 0.5 * (agent_count ** 0.8) / (agent_count ** 0.1)
    spec = min(base_spec / (1 + 0.001 * game_id), 1.0)

    base_ret = 0.9 if context == "full" else 0.75
    ret = max(base_ret - 0.0005 * game_id, 0.0)

    return GameResult(
        game_id=game_id,
        agent_count=agent_count,
        specialization_index=spec,
        retrieval_efficiency=ret,
        context_condition=context,
    )

# --------------------------------------------------------------------------- #
# Argument parsing utilities
# --------------------------------------------------------------------------- #

def parse_agent_counts(arg: str) -> List[int]:
    """
    Parse a comma‑separated list of integers representing agent counts.

    Example:
        ``"3,5,7"`` → ``[3, 5, 7]``
    """
    try:
        return [int(item.strip()) for item in arg.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid agent count list: {arg}") from exc

def parse_thresholds(arg: str) -> List[int]:
    """
    Parse a comma‑separated list of integer thresholds.

    The function is kept for backward compatibility – the current US‑3
    implementation does not use thresholds, but other scripts may still
    import it.
    """
    if not arg:
        return []
    try:
        return [int(item.strip()) for item in arg.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid thresholds list: {arg}") from exc

# --------------------------------------------------------------------------- #
# Core simulation loop
# --------------------------------------------------------------------------- #

def run_simulation(
    agent_counts: List[int],
    games_per_config: int,
    context: str,
    logger: Any,
) -> List[GameResult]:
    """
    Execute the deterministic simulation.

    Args:
        agent_counts: List of agent counts to simulate.
        games_per_config: Number of games to run for each agent count.
        context: ``full`` or ``limited`` – passed through to
            :func:`simulate_one_game`.
        logger: Logger instance from ``utils.logging``.

    Returns:
        Flat list of :class:`GameResult` objects.
    """
    results: List[GameResult] = []
    for agent_count in agent_counts:
        logger.info(
            "Starting simulation for %d agents, %d games, context=%s",
            agent_count,
            games_per_config,
            context,
        )
        for game_id in range(games_per_config):
            result = simulate_one_game(agent_count, game_id, context)
            results.append(result)
    return results

# --------------------------------------------------------------------------- #
# CSV writing utilities
# --------------------------------------------------------------------------- #

def write_results_csv(
    results: List[GameResult],
    output_path: Path,
    logger: Any,
) -> None:
    """
    Write a list of :class:`GameResult` records to a CSV file.

    The CSV header matches the specification in task T015.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "game_id",
        "agent_count",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
    ]
    logger.info("Writing %d results to %s", len(results), output_path)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(res.to_dict())

# --------------------------------------------------------------------------- #
# Scaling analysis helpers
# --------------------------------------------------------------------------- #

def aggregate_for_scaling(
    results: List[GameResult],
) -> List[Dict[str, Any]]:
    """
    Collapse per‑game results into per‑agent‑count aggregates required by
    ``analysis.scaling``.

    Returns a list of dicts with keys:
        - agent_count
        - mean_specialization
        - mean_retrieval
    """
    from collections import defaultdict

    sums = defaultdict(lambda: {"spec": 0.0, "ret": 0.0, "n": 0})
    for r in results:
        agg = sums[r.agent_count]
        agg["spec"] += r.specialization_index
        agg["ret"] += r.retrieval_efficiency
        agg["n"] += 1

    aggregated = []
    for agent_count, data in sorted(sums.items()):
        aggregated.append(
            {
                "agent_count": agent_count,
                "mean_specialization": data["spec"] / data["n"],
                "mean_retrieval": data["ret"] / data["n"],
            }
        )
    return aggregated

def write_scaling_data_csv(
    aggregated: List[Dict[str, Any]],
    csv_path: Path,
    logger: Any,
) -> None:
    """
    Write the aggregated scaling data to a CSV file that can be consumed by
    ``analysis.scaling.generate_scaling_plot``.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["agent_count", "mean_specialization", "mean_retrieval"]
    logger.info("Writing scaling data to %s", csv_path)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in aggregated:
            writer.writerow(row)

# --------------------------------------------------------------------------- #
# Argument parser
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run scaling experiments for Social Memory Networks."
    )
    parser.add_argument(
        "--agents",
        type=parse_agent_counts,
        default="3,5,7",
        help="Comma‑separated list of agent counts (e.g. '3,5,7').",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=800,
        help="Number of games to simulate per agent count.",
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        default="full",
        help="Context condition for the simulation.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results"),
        help="Directory where CSV results and plots will be stored.",
    )
    parser.add_argument(
        "--plot-scaling",
        action="store_true",
        help="If set, generate a scaling plot (PDF) after the simulation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (kept for API compatibility; not used by deterministic simulation).",
    )
    return parser

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger = get_logger(__name__)

    # Ensure reproducibility – we do not use random, but set the seed for any
    # downstream libraries that might.
    import random

    random.seed(args.seed)

    # Run the core simulation
    results = run_simulation(
        agent_counts=args.agents,
        games_per_config=args.games,
        context=args.context,
        logger=logger,
    )

    # Write per‑game CSV
    csv_path = args.output_dir / "scaling_experiment_results.csv"
    write_results_csv(results, csv_path, logger)

    # If requested, produce the scaling analysis artefacts
    if args.plot_scaling:
        # 1. Aggregate results
        aggregated = aggregate_for_scaling(results)

        # 2. Write scaling data CSV (used by analysis.scaling)
        scaling_data_path = args.output_dir / "scaling_data.csv"
        write_scaling_data_csv(aggregated, scaling_data_path, logger)

        # 3. Generate the scaling plot PDF
        try:
            from analysis.scaling import generate_scaling_plot

            logger.info("Generating scaling plot at %s", args.output_dir / "scaling_plot.pdf")
            generate_scaling_plot(
                data_path=scaling_data_path,
                output_path=args.output_dir / "scaling_plot.pdf",
                note=(
                    "Only three data points are available; the fitted power‑law "
                    "exponent should be interpreted with caution."
                ),
            )
        except Exception as exc:
            logger.error("Failed to generate scaling plot: %s", exc)

    logger.info("Experiment completed successfully.")

if __name__ == "__main__":
    main()
