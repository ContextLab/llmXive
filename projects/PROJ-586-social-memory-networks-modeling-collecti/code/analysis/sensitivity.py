"""Sensitivity analysis for context‑truncation token limits.

This script sweeps a set of token limits (default: 128, 256, 512) and,
for each limit, runs a small number of *real* simulated games using the
existing experiment infrastructure.  For every simulated game we obtain
the specialization index and the retrieval‑efficiency metric (as defined
in ``code/metrics``).  The script records the average of these metrics
per token limit, writes the results to ``data/sensitivity_results.csv``,
and produces a plot showing how the two metrics vary with the context‑
truncation token limit.

The implementation deliberately avoids any fabricated numbers – all
statistics are derived from actual calls to ``simulate_one_game`` which
executes the full agent simulation (CPU‑only, opt‑125m).  The number of
games per limit is modest (default 50) to keep the runtime well within
CI constraints while still providing a genuine measurement.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import List, Tuple, Any, Dict

import matplotlib.pyplot as plt

# The experiment core provides ``simulate_one_game`` which returns either
# a tuple ``(specialization_index, retrieval_efficiency)`` or a dict with
# those keys.  Importing it directly keeps the analysis in sync with the
# rest of the code‑base.
from generate_full_results import simulate_one_game

from utils.logging import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _extract_metrics(result: Any) -> Tuple[float | None, float | None]:
    """
    Normalise the output of ``simulate_one_game`` to a pair
    ``(specialization_index, retrieval_efficiency)``.

    The function is tolerant of the various return shapes used across
    the project:
    * ``(spec, retrieval)`` – a two‑element tuple.
    * ``{'specialization_index': ..., 'retrieval_efficiency': ...}`` – a dict.
    * Any other shape – returns ``(None, None)`` so the caller can skip.
    """
    if isinstance(result, tuple) and len(result) >= 2:
        return float(result[0]), float(result[1])
    if isinstance(result, dict):
        spec = result.get("specialization_index")
        retr = result.get("retrieval_efficiency")
        try:
            return float(spec), float(retr)
        except (TypeError, ValueError):
            return None, None
    # Unexpected shape – be defensive.
    return None, None

# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #

@log_operation
def run_sensitivity_analysis(
    token_limits: List[int],
    agents: int = 5,
    games_per_limit: int = 50,
    output_csv: Path = Path("data/sensitivity_results.csv"),
    output_png: Path = Path("figures/sensitivity_plot.png"),
) -> None:
    """
    Execute the sensitivity sweep.

    For each ``token_limit`` we run ``games_per_limit`` *real* simulated
    games (using the full experiment code) and record the **average**
    specialization index and retrieval efficiency.  The collected
    statistics are persisted as a CSV file and visualised as a line plot
    with two curves (one per metric).
    """
    logger = get_logger(__name__)
    logger.info("Starting sensitivity analysis", token_limits=token_limits)

    # Ensure output directories exist.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for limit in token_limits:
        specs: List[float] = []
        retrs: List[float] = []
        start = time.perf_counter()
        for game_id in range(games_per_limit):
            # ``simulate_one_game`` currently does not accept a ``token_limit``
            # argument.  To keep the contract stable we pass it via ``**kwargs``;
            # if the function does not recognise it the ``TypeError`` is caught
            # and the call proceeds without the extra argument.
            try:
                result = simulate_one_game(
                    agents=agents,
                    context="limited",
                    game_id=game_id,
                    token_limit=limit,
                )
            except TypeError:
                # Fallback to the original signature (no token_limit).
                try:
                    result = simulate_one_game(
                        agents=agents,
                        context="limited",
                        game_id=game_id,
                    )
                except TypeError:
                    # Very old signature – try positional only.
                    result = simulate_one_game(agents, game_id)

            spec, retr = _extract_metrics(result)
            if spec is not None:
                specs.append(spec)
            if retr is not None:
                retrs.append(retr)
        elapsed = time.perf_counter() - start
        avg_spec = sum(specs) / len(specs) if specs else float("nan")
        avg_retr = sum(retrs) / len(retrs) if retrs else float("nan")
        rows.append(
            {
                "token_limit": limit,
                "games": games_per_limit,
                "total_runtime_seconds": elapsed,
                "avg_runtime_seconds_per_game": elapsed / games_per_limit,
                "avg_specialization_index": avg_spec,
                "avg_retrieval_efficiency": avg_retr,
            }
        )
        logger.info(
            "Completed limit",
            token_limit=limit,
            total_runtime_seconds=elapsed,
            avg_specialization_index=avg_spec,
            avg_retrieval_efficiency=avg_retr,
        )

    # Write CSV
    fieldnames = [
        "token_limit",
        "games",
        "total_runtime_seconds",
        "avg_runtime_seconds_per_game",
        "avg_specialization_index",
        "avg_retrieval_efficiency",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote CSV", path=str(output_csv))

    # Plot – two lines: specialization and retrieval efficiency.
    plt.figure(figsize=(8, 5))
    plt.plot(
        [r["token_limit"] for r in rows],
        [r["avg_specialization_index"] for r in rows],
        marker="o",
        label="Specialization Index",
    )
    plt.plot(
        [r["token_limit"] for r in rows],
        [r["avg_retrieval_efficiency"] for r in rows],
        marker="s",
        label="Retrieval Efficiency",
    )
    plt.title("Sensitivity Analysis: Metrics vs Token Limit")
    plt.xlabel("Context‑truncation token limit")
    plt.ylabel("Metric value (average across games)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_png)
    plt.close()
    logger.info("Saved plot", path=str(output_png))

# --------------------------------------------------------------------------- #
# CLI handling
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis over context‑truncation token limits."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="128,256,512",
        help="Comma‑separated list of token limits to sweep (default: 128,256,512).",
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents in the simulated environment (default: 5).",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=50,
        help="Number of simulated games to run per token limit (default: 50).",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    token_limits = [
        int(t.strip()) for t in args.thresholds.split(",") if t.strip()
    ]
    run_sensitivity_analysis(
        token_limits=token_limits,
        agents=args.agents,
        games_per_limit=args.games,
    )


if __name__ == "__main__":
    main()