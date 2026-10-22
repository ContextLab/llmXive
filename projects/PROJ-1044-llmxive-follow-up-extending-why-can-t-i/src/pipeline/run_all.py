"""
Minimal orchestrator for the subset of the pipeline required to
validate the counterfactual generation and the robust data loader.
It runs the following steps:

1. Stream a small number of videos via ``something_stream``.
2. Generate counterfactual pairs using ``src.data.counterfactual``.
3. Exit with status 0 on success.

This script is deliberately lightweight; full end‑to‑end execution
(optical‑flow pre‑compute, training, evaluation, etc.) is handled by
other dedicated scripts not required for the current verification.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal pipeline.")
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("./output"),
        help="Root directory for all generated artifacts.",
    )
    parser.add_argument(
        "--subset_size",
        type=int,
        default=5,
        help="Number of videos to process for the quick test.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic behaviour.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_cli_args(argv)

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run the counterfactual generator (it internally streams videos)
    from src.data.counterfactual import main as cf_main

    cf_args = [
        "--subset_size",
        str(args.subset_size),
        "--output_dir",
        str(args.output_dir),
        "--optical_flow_divergence_threshold",
        "0.15",
        "--feature_similarity_threshold",
        "0.9",
        "--patch_dir",
        "data/patches",
        "--seed",
        str(args.seed),
    ]
    ret = cf_main(cf_args)
    if ret != 0:
        log.error("Counterfactual generation failed with exit code %s", ret)
        return ret

    log.info("Minimal pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())