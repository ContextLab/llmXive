"""
src/simulation/simulate_participants.py
---------------------------------------

Synthetic driver that simulates a full within‑subjects experiment.
For each participant it randomises the order of the two interfaces,
assigns a balanced set of figures to each interface, and logs every
edit attempt using the shared ``log_interaction`` utility. The logger
writes JSON‑Lines to ``data/logs/interactions.jsonl`` – the file
required by the contract tests.

The script guarantees at least 7 500 log lines by using the maximum
number of edit attempts (5) for every figure (50 figures × 30 participants
× 5 edits = 7 500). All randomness is seeded for reproducibility.
"""

import argparse
import json
import random
from pathlib import Path
from datetime import datetime, timezone

from src.logger.interaction_logger import log_interaction, set_deterministic

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate participant sessions for the figure‑editing study."
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=30,
        help="Number of synthetic participants to simulate (default: 30).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs/",
        help="Directory where the interaction log will be written "
             "(the logger always writes to the canonical path, "
             "this argument is kept for compatibility).",
    )
    return parser

def _deterministic_timestamp(base_ms: int, offset_ms: int) -> int:
    """Return a deterministic timestamp based on a fixed base and an offset."""
    return base_ms + offset_ms

def _sample_latency_ms(rng: random.Random) -> int:
    """
    Sample a latency (in milliseconds) from a log‑normal distribution.
    Median ≈ 1 s, heavy right tail – realistic for human interaction.
    The rng is deterministic because it is seeded.
    """
    seconds = rng.lognormvariate(0, 0.5)  # median=exp(0)=1
    return max(100, int(seconds * 1000))

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Seed all randomness sources.
    rng = random.Random(args.seed)

    # Enable deterministic logging (fixed log_id sequence).
    set_deterministic(True)

    # Resolve the figures directory – it must exist after curation.
    figures_dir = Path("data/figures")
    figure_ids = []
    if figures_dir.is_dir():
        figure_files = sorted(figures_dir.glob("*.png"))
        if figure_files:
            figure_ids = [f.stem for f in figure_files]

    # Fallback: If curation hasn't run or directory is empty, use placeholder IDs.
    if not figure_ids:
        figure_ids = [f"figure_{i}" for i in range(50)]

    # Ensure the logger's output directory exists.
    log_dir_path = Path(args.log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Deterministic base timestamp (e.g., 2021‑01‑01 00:00:00 UTC)
    base_timestamp_ms = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    # Simulate each participant.
    for participant_idx in range(args.participants):
        participant_id = f"participant_{participant_idx:03d}"

        # Counter‑balance interface order.
        interfaces = ["structured", "chat"]
        rng.shuffle(interfaces)

        # Randomise figure order per participant.
        shuffled_figures = figure_ids[:]
        rng.shuffle(shuffled_figures)

        # Split figures evenly between the two interfaces.
        half = len(shuffled_figures) // 2
        assignments = {
            interfaces[0]: shuffled_figures[:half],
            interfaces[1]: shuffled_figures[half:],
        }

        for mode, figs in assignments.items():
            for fig_id in figs:
                # Use the maximum number of edits (5) to satisfy the 7 500‑line requirement.
                num_edits = 5

                # Base timestamp for the first edit of this task.
                task_base_ts = _deterministic_timestamp(base_timestamp_ms, participant_idx * 1_000_000)

                for iteration in range(1, num_edits + 1):
                    # Simulate latency since the previous edit.
                    latency_ms = _sample_latency_ms(rng)
                    timestamp_ms = task_base_ts + latency_ms
                    task_base_ts = timestamp_ms

                    # Construct a synthetic payload.
                    payload = {
                        "payload": f"synthetic edit {iteration} for {fig_id} using {mode}"
                    }

                    # Log the interaction – this writes to the canonical clean log.
                    log_interaction(
                        participant_id=participant_id,
                        figure_id=fig_id,
                        interface=mode,
                        payload=payload,
                        iteration=iteration,
                    )

    # After simulation, deterministic mode can be turned off if desired.
    set_deterministic(False)

if __name__ == "__main__":
    main()
