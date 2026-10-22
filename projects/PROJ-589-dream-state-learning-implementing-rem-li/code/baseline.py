"""
Baseline training script for the Dream‑State Learning project.

This script runs a continuous‑training baseline that mirrors the experimental
wake/dream run’s total *real‑token* exposure.  It disables the dream phase by
setting an extremely large wake‑to‑dream ratio, ensuring that every training
step is a standard supervised “wake” step.

The output artifacts (checkpoint and JSON log) follow the same naming scheme
as ``code/train.py`` so that downstream integration tests can locate and
compare them directly.
"""

import argparse
from pathlib import Path
from typing import List

# Re‑use the core training utilities from the existing training entry point.
# Importing the functions directly avoids code duplication and guarantees
# that the baseline uses exactly the same data loading, model, optimizer,
# memory‑monitoring and logging logic as the experimental run.
from train import run_one  # type: ignore  # ``train`` is a sibling module

def parse_seed_list(seeds: str | None, single_seed: int) -> List[int]:
    """Return a list of integer seeds."""
    if seeds:
        return [int(s) for s in seeds.split(",") if s.strip()]
    return [single_seed]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the continuous‑training baseline (no dream phases)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Single seed to run when ``--seeds`` is not supplied.",
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default=None,
        help="Comma‑separated list of seeds. Overrides ``--seed``.",
    )
    parser.add_argument(
        "--total_steps",
        type=int,
        default=100,
        help="Total number of training steps per seed.",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=None,
        help="Number of warm‑up wake‑only steps before dream could be allowed.",
    )
    parser.add_argument(
        "--glue_subset",
        type=str,
        default="mrpc",
        help="GLUE subset to use for training (kept for API compatibility).",
    )
    args = parser.parse_args()

    seed_list = parse_seed_list(args.seeds, args.seed)

    # ``run_one`` expects the following signature:
    #   run_one(seed, total_steps, mode, ratio, warmup)
    # To disable dreaming we pass a ratio with an astronomically large wake‑to‑dream
    # cycle length (e.g. ``1000000:1``).  The ``DreamScheduler`` in ``trainer.py``
    # triggers a dream step only when ``current_step % ratio == 0``; with a ratio
    # far larger than ``total_steps`` this condition is never met.
    baseline_ratio = "1000000:1"

    for s in seed_list:
        try:
            # ``mode`` is set to ``baseline`` so that checkpoint and log filenames
            # clearly indicate the regime.
            run_one(
                seed=s,
                total_steps=args.total_steps,
                mode="baseline",
                ratio=baseline_ratio,
                warmup=args.warmup,
            )
        except Exception as exc:
            # Propagate any exception – the CI harness will surface the failure.
            raise RuntimeError(f"Baseline training failed for seed {s}") from exc

if __name__ == "__main__":
    main()
