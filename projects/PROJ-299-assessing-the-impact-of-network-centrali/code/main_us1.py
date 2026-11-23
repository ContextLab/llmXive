"""
User Story 1 Orchestration Script

Chains: Download -> Preprocess -> QC -> Connectivity -> Centrality.
Produces: data/analysis/centrality_metrics.csv, data/analysis/qc_log.json, data/raw/participant_list.csv.
"""
import argparse
import json
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.download.adni_downloader import run_downloader
from code.preprocess.fMRI_pipeline import run_production_pipeline, run_qc_exclusion
from code.centrality.connectivity import run_connectivity_pipeline
from code.centrality.metrics import run_centrality_pipeline
from code.utils.logging_config import setup_logging, get_logger
from code.utils.io_utils import write_json, read_json

def run_us1_pipeline():
    """
    Executes the full User Story 1 pipeline.
    Returns 0 on success, non-zero on failure.
    """
    logger = get_logger("us1")
    logger.info("Starting User Story 1 Pipeline")

    # 1. Download Data
    # Note: This step expects ADNI credentials in .env or CLI args.
    # It will generate data/raw/participant_list.csv if successful.
    logger.info("Step 1: Downloading ADNI data...")
    ret = run_downloader()
    if ret != 0:
        logger.error("Download failed.")
        return ret

    # 2. Preprocess fMRI
    logger.info("Step 2: Preprocessing fMRI data...")
    ret = run_production_pipeline()
    if ret != 0:
        logger.error("Preprocessing failed.")
        return ret

    # 3. Calculate FD and QC
    logger.info("Step 3: Calculating Framewise Displacement and QC...")
    ret = run_qc_exclusion()
    if ret != 0:
        logger.error("QC calculation failed.")
        return ret
    
    # Ensure qc_log.json exists (run_qc_exclusion should create it)
    qc_log_path = project_root / "data" / "analysis" / "qc_log.json"
    if not qc_log_path.exists():
        logger.error("QC Log not found. QC exclusion step may have failed silently.")
        return 1

    # 4. Compute Connectivity
    logger.info("Step 4: Computing Connectivity Matrices...")
    ret = run_connectivity_pipeline()
    if ret != 0:
        logger.error("Connectivity computation failed.")
        return ret

    # 5. Compute Centrality Metrics
    logger.info("Step 5: Computing Centrality Metrics...")
    ret = run_centrality_pipeline()
    if ret != 0:
        logger.error("Centrality computation failed.")
        return ret

    logger.info("User Story 1 Pipeline completed successfully.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Run User Story 1 Pipeline")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)
    
    return run_us1_pipeline()

if __name__ == "__main__":
    sys.exit(main())
