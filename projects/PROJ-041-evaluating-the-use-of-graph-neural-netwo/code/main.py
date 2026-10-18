"""
main.py
-------

Minimal end‑to‑end entry point for the quick‑start pipeline. It performs the
essential bootstrap steps required for the initial execution:

1. Creates the project layout and a minimal ``code/config.yaml`` (via
   ``create_layout.main``).
2. Downloads the CTU‑13 Scenario 1 NetFlow CSV (via
   ``code.data.download_ctu13.main``), producing
   ``data/raw/ctu13_scenario1.csv`` and its SHA‑256 checksum.

The script accepts ``--scenarios`` and ``--seeds`` arguments to stay
compatible with the documented quick‑start command line, but it does not
yet implement the full analysis pipeline – that is addressed in later
tasks.
"""

import argparse
import sys

from create_layout import main as create_layout_main
from data.download_ctu13 import main as download_ctu13_main
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _parse_args():
    parser = argparse.ArgumentParser(description="Bootstrap the project and download the dataset.")
    parser.add_argument("--scenarios", nargs="+", default=["all"], help="Scenarios to process (placeholder).")
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=[42, 123, 456, 789, 101112],
        help="Random seeds for downstream experiments (placeholder).",
    )
    # Allow unknown arguments to keep compatibility with future extensions.
    args, unknown = parser.parse_known_args()
    if unknown:
        log.debug("Ignoring unknown arguments: %s", unknown)
    return args

def main():
    args = _parse_args()
    log.info("Starting project bootstrap with scenarios=%s, seeds=%s", args.scenarios, args.seeds)

    # Step 1: create directory layout and config file
    create_layout_main()

    # Step 2: download the CTU‑13 Scenario 1 CSV
    try:
        download_ctu13_main()
    except Exception as exc:
        log.error("Failed to download CTU‑13 dataset: %s", exc)
        sys.exit(1)

    log.info("Bootstrap completed successfully.")

if __name__ == "__main__":
    main()
