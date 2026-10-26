"""
src/main.py

Entry point for the full pipeline execution as referenced in
`quickstart.md`. It orchestrates the GWTC download (T001) and the
data‑availability recording (T002) steps.

The command line interface mirrors the flags described in the
quickstart documentation, but only the flags required for the
current tasks are implemented:

* ``--download-only`` – perform only the download step.
* ``--skip-download`` – assume the raw files already exist and
  only run the availability check.
* ``--seed`` – placeholder for future reproducibility; not used
  directly by the current tasks.

The script exits with a non‑zero status if any step fails,
satisfying the “fail loudly” requirement.
"""

import argparse
import sys

from llmxive_toolkit import get_logger
from src.data.download_gwtc import main as download_main
from src.data.record_availability import main as record_main

log = get_logger(__name__)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the GWTC download and data‑availability checks."
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download GWTC files (skip availability check).",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading; only perform availability check.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed placeholder (not used in current tasks).",
    )
    return parser.parse_args(argv)

def run_pipeline(args):
    """
    Execute the pipeline steps according to the supplied arguments.
    """
    # Step 1: download GWTC files unless explicitly skipped.
    if not args.skip_download:
        log.info("Starting GWTC download step...")
        try:
            download_main()
        except SystemExit as exc:
            # download_main uses sys.exit on failure; propagate the error.
            log.error("GWTC download failed with exit code %s", exc.code)
            raise
        except Exception as exc:
            log.error("Unexpected error during GWTC download: %s", exc)
            raise

    # Step 2: record data‑availability metadata unless download‑only.
    if not args.download_only:
        log.info("Running data‑availability recording step...")
        try:
            record_main()
        except SystemExit as exc:
            log.error(
                "Data‑availability recording failed with exit code %s",
                exc.code,
            )
            raise
        except Exception as exc:
            log.error("Unexpected error during availability check: %s", exc)
            raise

    log.info("Pipeline completed successfully.")

def main(argv=None):
    """
    CLI entry point.
    """
    args = parse_args(argv)
    try:
        run_pipeline(args)
    except Exception:
        # Ensure a non‑zero exit status on any failure.
        sys.exit(1)

if __name__ == "__main__":
    main()