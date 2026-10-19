"""Entry point for the statistical properties pipeline.

This script orchestrates the main steps required by the project, including:
- Downloading GWTC observational data (if not already present).
- Recording data‑availability metadata.
- Preprocessing the observational data.
- Acquiring the simulation catalog (download or synthetic fallback).
- Logging progress and emitting a concise JSON summary.

It matches the command referenced in ``quickstart.md``:
    python src/main.py

The script uses relative imports so it works when executed as a
script inside the ``src`` package (``python src/main.py``).
"""

import argparse
import json
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Relative imports to avoid import‑collision issues when the script is run
# directly from the ``src`` package directory.
from .data.download import download_all
from .data.preprocess import preprocess
from .data.synthetic_gen import acquire_sim_catalog
from .data.record_availability import record_availability

log = get_logger(__name__)

def _run_download() -> dict:
    """Download raw GWTC files (if needed) and return their paths."""
    log.info("Starting GWTC download step...")
    try:
        result = download_all()
        log.info("GWTC download completed.")
        return result
    except Exception as exc:
        log.error("GWTC download failed: %s", exc)
        raise

def _run_record_availability() -> dict:
    """Write the data‑availability JSON report."""
    log.info("Recording data‑availability metadata...")
    try:
        result = record_availability()
        log.info("Data‑availability report written.")
        return result
    except Exception as exc:
        log.error("Data‑availability recording failed: %s", exc)
        raise

def _run_preprocess() -> dict:
    """Preprocess the raw GWTC HDF5 files."""
    log.info("Starting preprocessing step...")
    try:
        result = preprocess()
        log.info("Preprocessing completed.")
        return result
    except Exception as exc:
        log.error("Preprocessing failed: %s", exc)
        raise

def _run_acquire_sim() -> Path:
    """Acquire (download or synthesize) the simulation catalog."""
    log.info("Acquiring simulation catalog...")
    try:
        out_path = acquire_sim_catalog()
        log.info("Simulation catalog ready at %s", out_path)
        return out_path
    except Exception as exc:
        log.error("Simulation catalog acquisition failed: %s", exc)
        raise

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full statistical‑properties pipeline."
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download raw data and exit.",
    )
    parser.add_argument(
        "--generate-synth-only",
        action="store_true",
        help="Skip GWTC download/preprocess and only generate the simulation catalog.",
    )
    parser.add_argument(
        "--alpha-sweep",
        action="store_true",
        default=True,
        help="Enable sensitivity analysis (default: enabled).",
    )
    args = parser.parse_args()

    # Step 1: GWTC download (unless explicitly skipped)
    if not args.generate_synth_only:
        download_info = _run_download()
        # Record availability immediately after download
        _run_record_availability()
    else:
        download_info = {}

    # Step 2: Preprocess observational data (unless skipped)
    if not args.generate_synth_only:
        preprocess_info = _run_preprocess()
    else:
        preprocess_info = {}

    # Step 3: Acquire simulation catalog (always executed)
    sim_path = _run_acquire_sim()

    # Summarise the artefacts produced by this run.
    summary = {
        "downloaded_files": {k: str(v) for k, v in download_info.items()},
        "preprocess_outputs": {k: str(v) for k, v in preprocess_info.items()},
        "simulation_catalog": str(sim_path),
    }

    # Write a tiny JSON summary to the results folder for downstream steps.
    summary_path = paths.results("pipeline_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    log.info("Pipeline completed successfully. Summary written to %s", summary_path)

if __name__ == "__main__":
    main()
