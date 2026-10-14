"""
generate_novel_clips.py
------------------------

This script generates a set of *novel* interaction clips that are
not part of the training or validation subsets.  The clips are
stored under ``data/raw_novel/clip_*.npz`` and follow the same
format as the clips produced by :pymod:`src.pipeline.generate_clips`.

The script mirrors the behaviour of ``generate_clips.py`` but writes
to a different output directory and uses a separate random seed
(default ``123``) to ensure the clips are distinct from the
training set.

The command‑line interface is intentionally minimal because the CI
verification simply runs the script and checks the number of files
produced:

    python -m src.pipeline.generate_novel_clips --num_clips 200

After successful execution, the directory ``data/raw_novel`` will
contain exactly ``num_clips`` ``.npz`` files, each with the arrays
``states``, ``actions`` and ``observations`` as required by downstream
pipeline stages.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import gymnasium as gym

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Re‑use the generation logic from the existing module to guarantee
# consistency of the clip format.
from src.pipeline.generate_clips import (
    _clean_output_dir,
    generate_one_clip,
)

DEFAULT_NUM_CLIPS = 200
DEFAULT_SEED = 123  # Different from the training seed (42) for novelty


def _parse_args(argv=None):
    """Parse command‑line arguments.

    Parameters
    ----------
    argv : list of str, optional
        Argument list to parse; if ``None`` (default) the arguments
        are taken from ``sys.argv[1:]``.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with attributes ``num_clips`` and ``seed``.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate a set of novel interaction clips for zero‑shot "
            "validation.  The clips are stored in "
            "``data/raw_novel/clip_*.npz``."
        )
    )
    parser.add_argument(
        "--num_clips",
        type=int,
        default=DEFAULT_NUM_CLIPS,
        help=f"Number of novel clips to generate (default: {DEFAULT_NUM_CLIPS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})",
    )
    return parser.parse_args(argv)


def generate_novel_clips(num_clips: int = DEFAULT_NUM_CLIPS,
                         out_dir: Path = None,
                         seed: int = DEFAULT_SEED) -> None:
    """Create ``num_clips`` reproducible interaction clips.

    The function mirrors :func:`src.pipeline.generate_clips.generate_clips`
    but writes to the ``raw_novel`` data directory.

    Parameters
    ----------
    num_clips : int
        Number of clips to generate.
    out_dir : pathlib.Path, optional
        Destination directory; if ``None`` the default
        ``paths.data('raw_novel')`` is used.
    seed : int
        Seed for the random number generators to ensure deterministic
        clip generation.
    """
    if out_dir is None:
        out_dir = paths.data("raw_novel")
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("Cleaning output directory %s", out_dir)
    _clean_output_dir(out_dir)

    log.info("Generating %d novel clips in %s (seed=%d)", num_clips, out_dir, seed)
    np.random.seed(seed)

    for clip_id in range(num_clips):
        generate_one_clip(clip_id, out_dir, seed=seed + clip_id)

    log.info("Finished generating %d novel clips.", num_clips)


def main(argv=None) -> None:
    """Entry point for ``python -m src.pipeline.generate_novel_clips``."""
    args = _parse_args(argv)
    generate_novel_clips(num_clips=args.num_clips, seed=args.seed)


if __name__ == "__main__":
    # When executed as a script ``python src/pipeline/generate_novel_clips.py``
    # we forward to the ``main`` function.
    main(sys.argv[1:])