"""
src/main.py

Entry point for the end‑to‑end analysis pipeline. The script follows the
Quickstart specification:

* ``--download-only`` – fetch GWTC files, record availability, then exit.
* ``--skip-download`` – assume the raw files and checksum manifest already
  exist; the script will still verify availability before proceeding.
* ``--seed <int>`` – optional override of the global random seed (used by
  downstream steps).

The implementation invokes the core building‑block functions defined in
``src.data`` and ``src.analysis``. Only the steps required for T001 are
guaranteed to run; later stages are left untouched to preserve existing
behaviour.
"""

import argparse
import sys
from llmxive_toolkit import get_logger

# Core pipeline components
from src.data.download import download_all
from src.data.record_availability import record_availability
from src.data.preprocess import preprocess
from src.data.synthetic_gen import acquire_sim_catalog

log = get_logger(__name__)

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run the GWTC statistical‑properties pipeline"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download GWTC files and record availability",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Assume GWTC files already exist (skip download step)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the default random seed (debugging only)",
    )
    return parser.parse_args()

def main():
    args = _parse_args()

    # ------------------------------------------------------------------
    # Step 1 – GWTC download and availability recording
    # ------------------------------------------------------------------
    if not args.skip_download:
        log.info("Starting GWTC download")
        try:
            download_all()
        except Exception as exc:
            log.error("GWTC download failed: %s", exc)
            sys.exit(1)

    # At this point a ``checksums.json`` should exist – either freshly
    # written by ``download_all`` or pre‑existing.
    try:
        record_availability()
    except Exception as exc:
        log.error("Data‑availability check failed: %s", exc)
        sys.exit(1)

    if args.download_only:
        log.info("Download‑only mode selected; exiting after availability check")
        return

    # ------------------------------------------------------------------
    # Step 2 – Observational preprocessing (required for later phases)
    # ------------------------------------------------------------------
    try:
        preprocess()
    except Exception as exc:
        log.error("Preprocessing of GWTC data failed: %s", exc)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 3 – Simulation catalog acquisition / synthetic fallback
    # ------------------------------------------------------------------
    try:
        acquire_sim_catalog()
    except Exception as exc:
        log.error("Simulation catalog acquisition failed: %s", exc)
        sys.exit(1)

    log.info("Pipeline execution completed successfully")

if __name__ == "__main__":
    main()
