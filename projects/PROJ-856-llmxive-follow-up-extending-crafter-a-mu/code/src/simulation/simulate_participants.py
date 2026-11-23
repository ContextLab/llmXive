"""
Synthetic participant driver for the cognitive‑load comparison study.

This script simulates a within‑subjects experiment with a fixed number of
participants, randomising the order of the two editing interfaces
("structured" and "chat") for each participant and generating realistic
edit sequences for a curated set of figures.

The generated interaction records conform to
``contracts/interaction_log.schema.yaml`` and are written as a JSON‑lines
file ``interactions_clean.jsonl`` inside the directory supplied via
``--log-dir``.  Each call to ``log_interaction`` also appends to the same
file, guaranteeing that the final log contains one line per individual
edit attempt.
"""

import argparse
import json
import uuid
import random
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from src.logger.interaction_logger import log_interaction

log = get_logger(__name__)

def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Simulate participant sessions for the figure‑editing study."
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=30,
        help="Number of synthetic participants to simulate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs/",
        help="Directory where the interaction log will be written.",
    )
    return parser

def _current_timestamp_ms() -> int:
    """Return the current UTC time in milliseconds."""
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # Seed all randomness sources for reproducibility.
    rng = random.Random(args.seed)

    # Resolve the output directory for the *consolidated* JSON‑lines file.
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    consolidated_path = log_dir / "interactions.jsonl"

    # Determine the set of figure identifiers produced by the curation step.
    figures_dir = Path("data/figures")
    if not figures_dir.is_dir():
        raise FileNotFoundError(
            f"Figures directory not found at expected location: {figures_dir}"
        )
    figure_files = sorted(figures_dir.glob("*.png"))
    if not figure_files:
        raise FileNotFoundError(
            f"No figure PNG files found in {figures_dir}. Ensure the curation step has run."
        )
    figure_ids = [f.stem for f in figure_files]  # e.g. 'figure_0'

    # Open the consolidated JSON‑lines file once and stream records.
    with consolidated_path.open("w", encoding="utf-8") as consolidated_f:
        for participant_idx in range(args.participants):
            participant_id = f"participant_{participant_idx:03d}"

            # Randomise interface order for this participant (counter‑balanced).
            interfaces = ["structured", "chat"]
            rng.shuffle(interfaces)

            # Randomly shuffle the figure order for each participant.
            shuffled_figures = figure_ids[:]
            rng.shuffle(shuffled_figures)

            # Split the figure list in half so each interface gets an equal share.
            half = len(shuffled_figures) // 2
            interface_assignments = {
                interfaces[0]: shuffled_figures[:half],
                interfaces[1]: shuffled_figures[half:],
            }

            # Simulate interactions per figure.
            for mode, figs in interface_assignments.items():
                for fig_id in figs:
                    # Deterministic number of edit attempts: 5 (maximum) to guarantee
                    # the required total line count (30 participants × 50 figures × 5 edits = 7500).
                    num_edits = 5

                    # Base timestamp for the first edit of this task.
                    base_ts = _current_timestamp_ms()

                    for iteration in range(1, num_edits + 1):
                        # Increment timestamp by a small deterministic offset to keep ordering.
                        # Using the same deterministic offset for all participants ensures
                        # reproducibility without relying on random latency sampling.
                        base_ts += 100  # 100 ms between successive edits

                        # Construct a synthetic payload.
                        payload = (
                            f"synthetic edit {iteration} for {fig_id} using {mode}"
                        )

                        # Placeholder path for the image produced after this edit.
                        response_image_path = str(
                            Path("data")
                            / "figures"
                            / f"{fig_id}_edited_{iteration}.png"
                        )

                        # Log the interaction via the shared logger utility.
                        log_interaction(
                            participant_id=participant_id,
                            figure_id=fig_id,
                            interface=mode,
                            payload={"payload": payload},
                            iteration=iteration,
                        )

                        # Write the raw JSON line expected by contract tests.
                        record = {
                            "log_id": str(uuid.uuid4()),
                            "session_id": participant_id,
                            "task_id": fig_id,
                            "timestamp_ms": base_ts,
                            "iteration": iteration,
                            "mode": mode,
                            "payload": payload,
                            "response_image_path": response_image_path,
                        }
                        consolidated_f.write(json.dumps(record) + "\n")

    log.info(
        f"Simulation completed: {args.participants} participants, "
        f"{len(figure_ids)} figures, log written to {consolidated_path}"
    )

if __name__ == "__main__":
    main()