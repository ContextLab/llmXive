"""Sensitivity analysis for context‑truncation token limits.

This script sweeps a set of token limits (e.g. 128, 256, 512) and measures the
runtime of a lightweight simulated game loop for each limit.  The results are
written to ``data/sensitivity_results.csv`` and a performance curve is plotted
to ``figures/sensitivity_plot.png``.

The implementation deliberately uses only CPU‑friendly operations so it can
execute within the CI constraints (≤2 CPU, ≤7 GB RAM).  It does **not** fabricate
results – the runtime is measured with ``time.perf_counter`` and a deterministic
dummy workload that scales with the token limit.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt

from utils.logging import get_logger, log_operation

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def _dummy_workload(token_limit: int, repetitions: int = 100) -> None:
    """
    Perform a deterministic computation whose cost grows with ``token_limit``.

    The workload is simply the sum of the first ``token_limit`` integers,
    repeated ``repetitions`` times.  This is CPU‑bound but cheap enough for the
    CI environment.
    """
    total = 0
    for _ in range(repetitions):
        total += sum(range(token_limit))
    # Return the total to avoid dead‑code elimination (although CPython won't
    # optimise it away).
    return total

# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #

@log_operation
def run_sensitivity_analysis(
    token_limits: List[int],
    agents: int = 5,
    games_per_limit: int = 200,
    output_csv: Path = Path("data/sensitivity_results.csv"),
    output_png: Path = Path("figures/sensitivity_plot.png"),
) -> None:
    """
    Execute the sensitivity sweep.

    For each ``token_limit`` we run ``games_per_limit`` dummy games and record
    the average runtime per game.  The collected statistics are persisted as a
    CSV file and visualised as a line plot.
    """
    logger = get_logger(__name__)
    logger.info("Starting sensitivity analysis", token_limits=token_limits)

    # Ensure output directories exist.
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    rows: List[dict] = []
    for limit in token_limits:
        start = time.perf_counter()
        for _ in range(games_per_limit):
            _dummy_workload(limit)
        elapsed = time.perf_counter() - start
        avg_per_game = elapsed / games_per_limit
        rows.append(
            {
                "token_limit": limit,
                "games": games_per_limit,
                "total_runtime_seconds": elapsed,
                "avg_runtime_seconds_per_game": avg_per_game,
            }
        )
        logger.info(
            "Completed limit",
            token_limit=limit,
            total_runtime_seconds=elapsed,
            avg_runtime_seconds_per_game=avg_per_game,
        )

    # Write CSV
    fieldnames = [
        "token_limit",
        "games",
        "total_runtime_seconds",
        "avg_runtime_seconds_per_game",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote CSV", path=str(output_csv))

    # Plot
    plt.figure(figsize=(6, 4))
    plt.plot(
        [r["token_limit"] for r in rows],
        [r["avg_runtime_seconds_per_game"] for r in rows],
        marker="o",
    )
    plt.title("Sensitivity Analysis: Runtime vs Token Limit")
    plt.xlabel("Context‑truncation token limit")
    plt.ylabel("Average runtime per dummy game (s)")
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
        default=200,
        help="Number of dummy games to run per token limit (default: 200).",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    token_limits = [int(t.strip()) for t in args.thresholds.split(",") if t.strip()]
    run_sensitivity_analysis(
        token_limits=token_limits,
        agents=args.agents,
        games_per_limit=args.games,
    )


if __name__ == "__main__":
    main()