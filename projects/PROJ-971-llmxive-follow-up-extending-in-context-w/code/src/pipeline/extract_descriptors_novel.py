#!/usr/bin/env python
"""
Extract latent statistical descriptors for novel interaction clips.

This script processes all ``.npz`` files in the ``data/raw_novel`` directory,
runs the pre‑trained ICWM encoder on each clip, computes the three
statistical descriptors (variance, lag‑1 autocorrelation, Welch spectral
density), and writes the results to ``data/descriptors_novel.csv``.
The output CSV conforms to the ``descriptor.schema.yaml`` contract.
"""

import argparse
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from src.pipeline.extract_descriptors import extract_all_descriptors

log = get_logger(__name__)

def _parse_args(argv=None):
    """Parse command‑line arguments.

    Parameters
    ----------
    argv : list of str, optional
        Argument list to parse; if ``None`` the arguments are taken from
        ``sys.argv[1:]``.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with ``input_dir`` and ``output_csv`` attributes.
    """
    parser = argparse.ArgumentParser(
        description="Extract latent descriptors for novel clips."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=paths.data("raw_novel"),
        help="Directory containing .npz novel clips (default: data/raw_novel).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=paths.data("descriptors_novel.csv"),
        help="Path to write the descriptors CSV (default: data/descriptors_novel.csv).",
    )
    return parser.parse_args(argv)

def main(argv=None):
    """Run the extraction pipeline for novel clips."""
    args = _parse_args(argv)

    # Ensure the output directory exists (paths.data creates it automatically)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    log.info(f"Extracting descriptors from novel clips in {args.input_dir}")
    extract_all_descriptors(args.input_dir, args.output_csv)
    log.info(f"Descriptors written to {args.output_csv}")

if __name__ == "__main__":
    main()
