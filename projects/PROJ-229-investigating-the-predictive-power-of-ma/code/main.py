"""
Main pipeline entry point for the project.

This script orchestrates the end‑to‑end data processing workflow:

1. Fetch raw Materials Project data (with fallback to matbench).
2. Fetch NIST data and perform target‑selection logic.
3. Compute material descriptors in a streaming‑friendly way.
4. Perform collinearity (VIF) analysis on the computed descriptors.
5. Persist the processed descriptor table to CSV.
6. Run the target‑consistency check that decides whether to use
   ``latent_heat`` or ``melting_point`` as the prediction target.
7. Generate SHA‑256 checksums for the **processed** data files and
   append them to ``data/checksums.txt`` so that the full pipeline
   records provenance of both raw and processed artifacts.

The implementation relies exclusively on the public API surface
defined in the repository (see the “Existing project API surface”
section of the prompt).  No new modules or functions are introduced
beyond what already exists.
"""

import sys
import logging
from pathlib import Path

# Project‑wide utilities
from utils.logger import get_pipeline_logger, log_error, log_info

# Step 1 – fetch Materials Project data (with fallback)
from data.run_fetch_materials import fetch_materials_main

# Step 2 – fetch NIST data and decide on the target variable
from data.run_fetch_nist_data import run as fetch_nist_main

# Step 3 – compute descriptors (streaming implementation)
from data.compute_descriptors import compute_descriptors

# Step 4 – VIF (collinearity) analysis
from utils.collinearity_utils import calculate_vif, identify_high_collinearity

# Step 5 – target consistency check (decides latent_heat vs melting_point)
from data.target_consistency_check import main as target_consistency_main

# Step 6 – generate checksums for processed data files
from data.generate_processed_checksums import main as generate_processed_checksums_main

import pandas as pd

# ----------------------------------------------------------------------
# Helper: wrap each pipeline stage so that a failure is logged and the
# pipeline aborts with a non‑zero exit code.
# ----------------------------------------------------------------------
def _run_stage(name: str, func, *args, **kwargs):
    """Execute a pipeline stage, logging start/end and handling exceptions."""
    logger = get_pipeline_logger()
    logger.info(f"=== Starting pipeline stage: {name} ===")
    try:
        result = func(*args, **kwargs)
        logger.info(f"=== Completed pipeline stage: {name} ===")
        return result
    except Exception as exc:  # pylint: disable=broad-except
        log_error(f"Pipeline stage '{name}' failed: {exc}", exc_info=True)
        # Re‑raise to ensure the process exits with an error status.
        raise

# ----------------------------------------------------------------------
# Core pipeline orchestration
# ----------------------------------------------------------------------
def run_pipeline() -> None:
    """
    Execute the full data‑processing pipeline.

    The order of operations is critical:
    * The target‑consistency check (T005c) must run **before** checksum
      generation so that the resulting ``target_decision.json`` is part of
      the processed artefacts whose checksum is recorded.
    * Descriptor computation (T012) and VIF analysis (T014) must also
      complete before we record checksums for the processed files.
    """
    # 1. Fetch raw Materials Project data
    _run_stage("fetch_materials", fetch_materials_main)

    # 2. Fetch NIST data and decide on the prediction target
    _run_stage("fetch_nist_data", fetch_nist_main)

    # 3. Compute descriptors (streaming, low‑memory)
    descriptors_df = _run_stage("compute_descriptors", compute_descriptors)

    # 4. Perform VIF analysis on the descriptor dataframe
    #    calculate_vif returns a DataFrame with VIF scores per column.
    vif_df = _run_stage("calculate_vif", calculate_vif, descriptors_df)

    # Identify highly collinear pairs (optional diagnostic)
    high_collinear = identify_high_collinearity(vif_df)
    if not high_collinear.empty:
        log_info(f"High collinearity detected in {len(high_collinear)} pairs.")

    # 5. Persist the processed descriptors to CSV for downstream use.
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    processed_path = processed_dir / "processed_features.csv"
    _run_stage(
        "save_processed_descriptors",
        lambda df: df.to_csv(processed_path, index=False),
        descriptors_df,
    )
    log_info(f"Processed descriptor CSV written to {processed_path}")

    # 6. Run target consistency check (produces data/results/target_decision.json)
    _run_stage("target_consistency_check", target_consistency_main)

    # 7. Generate checksums for processed data (adds entries to data/checksums.txt)
    _run_stage("generate_processed_checksums", generate_processed_checksums_main)

    log_info("Pipeline completed successfully.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    """
    Command‑line entry point used by ``python -m code.main`` or the
    ``code/main.py`` script.

    Returns:
        int: Exit status (0 = success, non‑zero = failure)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Initialise the logger early so that all subsequent stages have
    # a configured logger.
    logger = get_pipeline_logger()
    logger.debug(f"Received CLI arguments: {argv}")

    try:
        run_pipeline()
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        # The exception has already been logged by _run_stage; we only
        # need to ensure a non‑zero exit code.
        logger.exception("Pipeline terminated with an error.")
        return 1


if __name__ == "__main__":
    sys.exit(main())