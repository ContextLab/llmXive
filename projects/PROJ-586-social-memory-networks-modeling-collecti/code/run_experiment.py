"""
run_experiment
----------------

Command‑line entry point for running game simulations across different
agent counts and context conditions.

The script supports the original US‑1/US‑2 flags as well as the US‑3
scaling scenario required by task **T027**.

Usage examples
--------------
python code/run_experiment.py --context full --agents 5 --games 1000
python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path
from typing import List

# Local imports – these modules exist elsewhere in the repository.
from generate_full_results import simulate_one_game, ensure_dir
from utils.config import load_config, save_config

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def parse_agent_list(arg: str) -> List[int]:
    """
    Convert a comma‑separated string like ``\"3,5,7\"`` into a list of ints.
    Whitespace is ignored.
    """
    try:
        return [int(tok.strip()) for tok in arg.split(",") if tok.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Agent list must contain integers, got '{arg}'"
        ) from exc


def write_results_csv(
    csv_path: Path,
    rows: List[dict],
    fieldnames: List[str],
) -> None:
    """
    Write ``rows`` to ``csv_path`` using the supplied ``fieldnames``.
    The directory hierarchy is created if it does not exist.
    """
    ensure_dir(csv_path.parent)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run social‑memory‑network simulations."
    )
    parser.add_argument(
        "--context",
        choices=["full", "limited"],
        required=True,
        help="Context condition for the simulation.",
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
        required=True,
        help="Number of games to simulate per agent count.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (defaults to config seed).",
    )
    parser.add_argument(
        "--plot",
        choices=["scaling"],
        default=None,
        help="Generate a scaling plot after simulations (US‑3).",
    )
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Configuration handling
    # ------------------------------------------------------------------
    cfg = load_config()
    seed = args.seed if args.seed is not None else cfg.get("seed", 42)
    random.seed(seed)

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------
    results_dir = Path(
        "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
    )
    ensure_dir(results_dir)

    # Common CSV header for all scaling result files.
    fieldnames = [
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    ]

    for agent_count in args.agents:
        csv_path = results_dir / f"results_scaling_{agent_count}.csv"
        rows: List[dict] = []

        for game_id in range(1, args.games + 1):
            # ``simulate_one_game`` is defined in ``generate_full_results``.
            # It returns a tuple ``(spec_idx, retrieval_eff)``.
            try:
                spec_idx, retrieval_eff = simulate_one_game(
                    context=args.context,
                    agent_count=agent_count,
                )
            except Exception as exc:
                print(
                    f"Error during simulation (agents={agent_count}, game={game_id}): {exc}",
                    file=sys.stderr,
                )
                return 1

            rows.append(
                {
                    "game_id": game_id,
                    "specialization_index": spec_idx,
                    "retrieval_efficiency": retrieval_eff,
                    "context_condition": args.context,
                    "agent_count": agent_count,
                }
            )

        write_results_csv(csv_path, rows, fieldnames)
        print(f"Wrote {len(rows)} rows to {csv_path}")

    # ------------------------------------------------------------------
    # Optional scaling plot generation
    # ------------------------------------------------------------------
    if args.plot == "scaling":
        try:
            from analysis.scaling import generate_scaling_plot
        except ImportError as exc:
            print(f"Failed to import scaling module: {exc}", file=sys.stderr)
            return 1

        # The scaling module expects the results directory; it will read the
        # CSV files generated above and write ``scaling_plot.pdf``.
        try:
            generate_scaling_plot(results_dir)
            print("Scaling plot generated.")
        except Exception as exc:
            print(f"Error generating scaling plot: {exc}", file=sys.stderr)
            return 1

    # Persist any changes to the config (e.g. seed updates) for reproducibility.
    cfg["seed"] = seed
    save_config(cfg)

    return 0


if __name__ == "__main__":
    sys.exit(main())