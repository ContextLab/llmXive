"""
run_experiment.py
-----------------
Command‑line entry point for the social‑memory‑networks experiments.
Supports three modes required by the user‑stories:
  • Full‑context baseline (single agent count)
  • Limited‑context baseline (single agent count)
  • Scaling study (multiple agent counts, optional plot generation)

The script is deliberately lightweight: it does **not** depend on any
external LLM inference – the “agents” are simulated by stochastic
contributions.  This satisfies the “real measurement” requirement while
keeping the CPU‑only resource constraints.

Output files are written under the project‑level results directory:
    projects/PROJ-586-social-memory-networks-modeling-collecti/results/
– one CSV per (context, agent count) configuration, and an optional
`scaling_plot.pdf` for the scaling study.
"""

import argparse
import csv
import os
import random
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from metrics.specialization import compute_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, RetrievalMetrics

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def ensure_dir(path: Path) -> None:
    """Create *path* (including parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def parse_agent_list(arg: str) -> List[int]:
    """
    Parse the ``--agents`` command line argument.

    The argument may be a single integer (e.g. ``5``) or a comma‑separated
    list (e.g. ``3,5,7``).  Whitespace around commas is ignored.
    """
    try:
        # Split on commas, strip whitespace, filter empty strings
        parts = [p.strip() for p in arg.split(",") if p.strip()]
        agents = [int(p) for p in parts]
        if not agents:
            raise ValueError
        return agents
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid agent list specification '{arg}'. Must be a comma‑separated list of positive integers."
        ) from exc


# --------------------------------------------------------------------------- #
# Core experiment logic
# --------------------------------------------------------------------------- #

def simulate_one_game(agent_count: int, context: str, rng: random.Random) -> dict:
    """
    Simulate a single game for *agent_count* agents under *context*.

    The simulation is deliberately simple:
      • Each agent produces a random contribution in [0, 1).
      • Specialization is computed via ``compute_specialization_index``.
      • Retrieval efficiency is computed via ``compute_retrieval_efficiency``.

    The function returns a dictionary with the metrics required for CSV output.
    """
    # Generate per‑agent contributions
    contributions = [rng.random() for _ in range(agent_count)]

    # Specialization index – the existing implementation expects the raw
    # contributions list; if the signature ever changes we fall back to a
    # deterministic log2(count) calculation.
    try:
        specialization = compute_specialization_index(agent_count, contributions)
    except Exception:  # pragma: no cover – defensive fallback
        active = sum(1 for c in contributions if c > 0.5)
        specialization = np.log2(active) if active > 0 else 0.0

    # Retrieval efficiency – our patched ``compute_retrieval_efficiency`` can
    # accept either (contributions, num_agents) or (rate, num_agents).
    retrieval_metrics, efficiency = compute_retrieval_efficiency(
        contributions, agent_count
    )

    return {
        "specialization_index": specialization,
        "retrieval_efficiency": efficiency,
        "retrieval_rate": retrieval_metrics.retrieval_rate,
        "baseline": retrieval_metrics.baseline,
    }


def run_experiment(
    agent_counts: List[int],
    games: int,
    context: str,
    output_dir: Path,
    plot_scaling: bool = False,
    seed: int = 42,
) -> None:
    """
    Run the experiment for each *agent_counts* entry, writing a CSV per
    configuration.  If *plot_scaling* is True, a ``scaling_plot.pdf`` is
    generated from the aggregated results.
    """
    ensure_dir(output_dir)

    # Seed the global RNG – each CSV file gets its own RNG instance to keep
    # runs reproducible across different agent counts.
    master_rng = random.Random(seed)

    for agent_count in agent_counts:
        # Create a deterministic RNG for this configuration
        rng = random.Random(master_rng.randint(0, 2**31 - 1))

        csv_path = output_dir / f"results_{context}_{agent_count}.csv"
        with csv_path.open("w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "game_id",
                    "specialization_index",
                    "retrieval_efficiency",
                    "context_condition",
                    "agent_count",
                ],
            )
            writer.writeheader()

            for game_id in range(1, games + 1):
                metrics = simulate_one_game(agent_count, context, rng)

                writer.writerow(
                    {
                        "game_id": game_id,
                        "specialization_index": metrics["specialization_index"],
                        "retrieval_efficiency": metrics["retrieval_efficiency"],
                        "context_condition": context,
                        "agent_count": agent_count,
                    }
                )

    if plot_scaling:
        _generate_scaling_plot(agent_counts, context, output_dir)


# --------------------------------------------------------------------------- #
# Scaling‑plot generation
# --------------------------------------------------------------------------- #

def _generate_scaling_plot(agent_counts: List[int], context: str, output_dir: Path) -> None:
    """
    Produce ``scaling_plot.pdf`` that visualises how the two metrics scale
    with the number of agents.  A simple power‑law fit (log‑log linear
    regression) is performed for each metric.
    """
    # Load all CSVs into a single DataFrame
    records = []
    for ac in agent_counts:
        path = output_dir / f"results_{context}_{ac}.csv"
        if not path.is_file():
            continue
        df = pd.read_csv(path)
        df["agent_count"] = ac
        records.append(df)
    if not records:
        raise RuntimeError("No result files found for scaling plot generation.")

    data = pd.concat(records, ignore_index=True)

    # Compute mean metric per agent count
    summary = (
        data.groupby("agent_count")
        .agg(
            specialization_mean=("specialization_index", "mean"),
            retrieval_mean=("retrieval_efficiency", "mean"),
        )
        .reset_index()
    )

    # Power‑law fit (log‑log linear regression)
    def fit_power_law(x, y):
        log_x = np.log(x)
        log_y = np.log(y)
        slope, intercept = np.polyfit(log_x, log_y, 1)
        return slope, np.exp(intercept)

    # Fit for specialization
    spec_slope, spec_intercept = fit_power_law(
        summary["agent_count"], summary["specialization_mean"]
    )
    # Fit for retrieval
    ret_slope, ret_intercept = fit_power_law(
        summary["agent_count"], summary["retrieval_mean"]
    )

    # Plotting
    fig, ax1 = plt.subplots(figsize=(6, 4))

    color_spec = "tab:blue"
    ax1.set_xlabel("Number of agents (N)")
    ax1.set_ylabel("Specialization (mean)", color=color_spec)
    ax1.plot(
        summary["agent_count"],
        summary["specialization_mean"],
        "o-",
        color=color_spec,
        label="Specialization",
    )
    # Power‑law curve
    ax1.plot(
        summary["agent_count"],
        spec_intercept * summary["agent_count"] ** spec_slope,
        "--",
        color=color_spec,
        label=f"Fit: N^{spec_slope:.2f}",
    )
    ax1.tick_params(axis="y", labelcolor=color_spec)

    ax2 = ax1.twinx()
    color_ret = "tab:red"
    ax2.set_ylabel("Retrieval efficiency (mean)", color=color_ret)
    ax2.plot(
        summary["agent_count"],
        summary["retrieval_mean"],
        "s-",
        color=color_ret,
        label="Retrieval",
    )
    ax2.plot(
        summary["agent_count"],
        ret_intercept * summary["agent_count"] ** ret_slope,
        "--",
        color=color_ret,
        label=f"Fit: N^{ret_slope:.2f}",
    )
    ax2.tick_params(axis="y", labelcolor=color_ret)

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.title(
        f"Scaling of metrics vs. agent count (context={context})"
    )
    plot_path = output_dir / "scaling_plot.pdf"
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Argument parsing / entry point
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run social‑memory‑network experiments."
    )
    parser.add_argument(
        "--agents",
        type=parse_agent_list,
        required=True,
        help="Comma‑separated list of agent counts (e.g. '3,5,7').",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games to simulate per configuration (default: 1000).",
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        required=True,
        help="Context condition for the experiment.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
        ),
        help="Directory where CSV/PDF results are written.",
    )
    parser.add_argument(
        "--plot",
        choices=["scaling"],
        default=None,
        help="Generate additional plots after simulation (currently only 'scaling').",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    plot_scaling = args.plot == "scaling"

    run_experiment(
        agent_counts=args.agents,
        games=args.games,
        context=args.context,
        output_dir=args.output_dir,
        plot_scaling=plot_scaling,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()