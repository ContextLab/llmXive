"""
Orchestrator for the "Evaluating the Impact of Code Generation on Software Security"
research pipeline.

This minimal orchestrator runs the core data‑ingestion steps required for the
quick‑start verification:
  1. Download the Devign dataset (or abort on error).
  2. Filter the dataset to retain only Python samples with vulnerability labels.
Additional pipeline stages (LLM generation, static analysis, etc.) are outside
the scope of the quick‑start task.

The script accepts a few CLI arguments for reproducibility but currently
ignores them beyond logging.
"""
import argparse
import sys

from llmxive_toolkit import get_logger, paths

# Import the two data‑preparation modules
from code.download_devign import main as download_devign_main
from code.filter_human_python import main as filter_human_python_main

log = get_logger(__name__)

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the core data preparation steps of the pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible downstream steps (currently unused).",
    )
    parser.add_argument(
        "--max-pairs",
        type=int,
        default=300,
        help="Maximum number of human/LLM pairs to generate (currently unused).",
    )
    parser.add_argument(
        "--confidence-thresholds",
        nargs="*",
        type=float,
        default=[0.0, 0.5, 0.9],
        help="Confidence thresholds for the sensitivity sweep (currently unused).",
    )
    return parser.parse_args(argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    log.info("Pipeline started with arguments: %s", args)

    # Step 1: download the Devign CSV (creates data/checksums.json)
    log.info("Downloading Devign dataset...")
    download_devign_main()

    # Step 2: filter for Python samples
    log.info("Filtering Devign dataset for Python samples...")
    filter_human_python_main()

    log.info("Core data‑preparation steps completed successfully.")

if __name__ == "__main__":
    main()
