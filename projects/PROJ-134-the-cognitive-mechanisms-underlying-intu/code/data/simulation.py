"""
Simulation Pipeline Orchestrator for PROJ-134.

This script serves as the single entry point for the simulation-only data generation
phase, authorized by the "Staged Implementation Authorization" in plan.md.
It orchestrates the generation of synthetic MFQ data, Moral Stories, and VR logs,
ensuring that all outputs are written to disk and checksummed.

This script resolves the run-book mismatch where `quickstart.md` invoked
`code/data/simulation.py` which did not previously exist.

Execution:
    python code/data/simulation.py

Outputs:
    data/raw/synthetic_mfq.csv
    data/raw/synthetic_stories.csv
    data/raw/synthetic_vr_logs.csv
    data/processed/simulated_data.csv (merged output from ingest)
    state/simulation_manifest.yaml (checksums)
"""

import os
import sys
import logging
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories, init_random_seeds, get_path, validate_data_mode
from code.data.simulation_mfq import main as generate_mfq
from code.data.simulation_stories import main as generate_stories
from code.data.ingest import main as run_ingest
from code.data.preprocess import main as run_preprocess
from code.utils.hashing import checksum_derived_datasets, update_state_yaml
from code.utils.logging_utils import get_logger, log_pipeline_step

def main():
    """
    Orchestrates the full simulation data generation pipeline.
    """
    # Initialize logging
    logger = get_logger("simulation_orchestrator")
    log_pipeline_step(logger, "START", "Simulation Data Generation")

    # 1. Setup
    ensure_directories()
    init_random_seeds()
    validate_data_mode()
    logger.info("Directories initialized, random seeds set, and data mode validated.")

    # 2. Generate Synthetic MFQ Data
    # Dependency: T013 (simulation_mfq.py)
    logger.info("Generating synthetic MFQ data...")
    try:
        generate_mfq()
        logger.info("MFQ data generation completed.")
    except Exception as e:
        logger.error(f"Failed to generate MFQ data: {e}")
        raise

    # 3. Generate Synthetic Moral Stories and VR Logs
    # Dependency: T014 (simulation_stories.py)
    logger.info("Generating synthetic Moral Stories and VR logs...")
    try:
        generate_stories()
        logger.info("Stories and VR logs generation completed.")
    except Exception as e:
        logger.error(f"Failed to generate stories/VR logs: {e}")
        raise

    # 4. Ingest and Merge Data
    # Dependency: T015 (ingest.py)
    logger.info("Ingesting and merging datasets...")
    try:
        run_ingest()
        logger.info("Data ingestion and merging completed.")
    except Exception as e:
        logger.error(f"Failed to ingest/merge data: {e}")
        raise

    # 5. Preprocess Data (Salience Mapping)
    # Dependency: T016 (preprocess.py)
    logger.info("Preprocessing data (salience mapping)...")
    try:
        run_preprocess()
        logger.info("Data preprocessing completed.")
    except Exception as e:
        logger.error(f"Failed to preprocess data: {e}")
        raise

    # 6. Checksum Artifacts
    # Dependency: T018 (hashing integration)
    logger.info("Checksumming generated artifacts...")
    try:
        # Define the output files that must exist
        output_files = [
            get_path("data/raw/synthetic_mfq.csv"),
            get_path("data/raw/synthetic_stories.csv"),
            get_path("data/raw/synthetic_vr_logs.csv"),
            get_path("data/processed/merged_data.csv"),
            get_path("data/processed/preprocessed_data.csv")
        ]

        # Verify files exist before checksumming
        missing = [f for f in output_files if not Path(f).exists()]
        if missing:
            raise FileNotFoundError(f"Expected output files missing: {missing}")

        checksums = checksum_derived_datasets(output_files)
        update_state_yaml("simulation_manifest.yaml", checksums)
        logger.info("Artifacts checksummed and state updated.")
    except Exception as e:
        logger.error(f"Failed to checksum artifacts: {e}")
        raise

    log_pipeline_step(logger, "COMPLETE", "Simulation Data Generation")
    logger.info("Simulation pipeline finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())