"""
src/simulation/simulate_participants.py
---------------------------------------

Synthetic driver that simulates a full within‑subjects experiment.
Generates at least 7,500 log lines (30 participants * 50 figures * 5 edits).
"""

import argparse
import random
from pathlib import Path
from datetime import datetime, timezone

from src.logger.interaction_logger import log_interaction, set_deterministic

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate participant sessions.")
    parser.add_argument("--participants", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-dir", type=str, default="data/logs/")
    return parser

def _sample_latency_ms(rng: random.Random) -> int:
    seconds = rng.lognormvariate(0, 0.5)
    return max(100, int(seconds * 1000))

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    rng = random.Random(args.seed)

    set_deterministic(True)

    figures_dir = Path("data/figures")
    figure_ids = [f.stem for f in sorted(figures_dir.glob("*.png"))] if figures_dir.is_dir() else []
    if not figure_ids:
        figure_ids = [f"figure_{i}" for i in range(50)]

    base_timestamp_ms = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

    for p_idx in range(args.participants):
        p_id = f"participant_{p_idx:03d}"
        interfaces = ["structured", "chat"]
        rng.shuffle(interfaces)

        shuffled_figs = figure_ids[:]
        rng.shuffle(shuffled_figs)
        half = len(shuffled_figs) // 2
        assignments = {interfaces[0]: shuffled_figs[:half], interfaces[1]: shuffled_figs[half:]}

        for mode, figs in assignments.items():
            for fig_id in figs:
                task_base_ts = base_timestamp_ms + (p_idx * 1_000_000)
                for iteration in range(1, 6): # 5 edits per figure
                    latency = _sample_latency_ms(rng)
                    task_base_ts += latency
                    log_interaction(
                        participant_id=p_id,
                        figure_id=fig_id,
                        interface=mode,
                        payload={"payload": f"synthetic edit {iteration} for {fig_id} using {mode}"},
                        iteration=iteration,
                    )

    set_deterministic(False)

if __name__ == "__main__":
    main()
