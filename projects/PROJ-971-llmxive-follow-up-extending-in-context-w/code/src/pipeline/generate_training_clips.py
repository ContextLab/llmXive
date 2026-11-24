"""
generate_training_clips.py
---------------------------

Wrapper script for Task T020: generate 200 training interaction clips.

This script re‑uses the existing ``src.pipeline.generate_clips`` module
to create 200 reproducible CartPole interaction clips and stores them
under ``data/raw/clip_<id>.npz`` (the default output directory used by
``generate_clips``).

The script is deliberately minimal – it simply calls the public
``generate_clips`` function with ``num_clips=200``.  When executed as
``python -m src.pipeline.generate_training_clips`` it will:
  1. Clean any existing ``clip_*.npz`` files in ``data/raw``.
  2. Generate exactly 200 clips (IDs 000‑199) with deterministic seeds.
  3. Log progress via the project's ``llmxive_toolkit`` logger.

The CI verifier for Task T020 checks that the directory
``data/raw`` contains 200 ``.npz`` files after the script runs and that
each file can be loaded with ``np.load`` without error.
"""

import logging
from src.pipeline.generate_clips import generate_clips
from llmxive_toolkit import get_logger

# Obtain a logger scoped to this module; the toolkit configures
# formatting and optional file output.
log = get_logger(__name__)

def main() -> None:
    """Generate exactly 200 training clips."""
    log.info("Starting generation of 200 training interaction clips.")
    generate_clips(num_clips=200)
    log.info("Finished generating 200 training clips.")

if __name__ == "__main__":
    # When run as a script ``python -m src.pipeline.generate_training_clips``
    # the ``main`` function is invoked.
    main()
