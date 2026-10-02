"""
Pipeline Orchestrator for the Nostalgia-Cognitive Flexibility Study.

This module orchestrates the ingestion pipeline, ensuring that the fetch attempt
(T010b) occurs before any fallback logic (T010d) is triggered. It catches exceptions
from the fetch step and triggers the fallback mechanism if necessary.

Execution Flow:
1. Attempt real data fetch (T010b logic via fetch_data).
2. If RealDataFetchFailed (DataFetchError) is caught: Trigger T010d (Simulation).
3. If fetch succeeds: Proceed to T011 (Validation/Cleaning).
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_config, ensure_dirs, get_env_str
from code.utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from code.ingestion.fetcher import fetch_data, save_metadata, DataFetchError, DataGapError, generate_synthetic_fallback
from code.ingestion.validator import validate_and_filter_dataset, clean_data

# Configure logging
logger = setup_logging("pipeline_orchestrator")

def run_orchestration():
    """
    Main orchestration function.
    1. Ensures directories exist.
    2. Attempts to fetch data (T010b).
    3. If fetch fails, triggers fallback (T010d logic).
    4. Validates and cleans the data (T011).
    5. Saves intermediate artifacts.
    """
    start_time = time.time()
    config = get_config()
    simulation_mode = False

    # 1. Ensure directories exist
    ensure_dirs()
    log_info(logger, "Directories ensured.")

    raw_data_path = config.get("paths", {}).get("raw_data", "data/raw/raw_dataset.csv")
    metadata_path = config.get("paths", {}).get("metadata", "data/raw/metadata.json")
    processed_data_path = config.get("paths", {}).get("processed_data", "data/processed/cleaned_score_filtered.csv")

    # 2. Attempt to fetch data (T010b logic)
    # The fetch_data function handles the canonical source attempt.
    # If it fails, it raises DataFetchError (which maps to RealDataFetchFailed requirement).
    try:
        log_info(logger, "Attempting to fetch data from canonical source (T010b)...")
        df, source_info = fetch_data()
        log_info(logger, f"Data fetched successfully from {source_info.get('source', 'unknown')}.")
        simulation_mode = False
    except DataFetchError as e:
        # T010c Logic: Catch RealDataFetchFailed (DataFetchError) and trigger T010d
        log_error(logger, f"Canonical fetch failed (T010b): {e}. Triggering fallback (T010d - Simulation).")
        try:
            # T010d Logic: Generate synthetic fallback data
            log_warning(logger, "Generating synthetic fallback dataset (T010d).")
            df, source_info = generate_synthetic_fallback(seed=42)
            simulation_mode = True
            log_info(logger, "Synthetic fallback generated successfully.")
        except Exception as fallback_err:
            log_error(logger, f"Fallback generation (T010d) failed: {fallback_err}")
            raise RuntimeError("Pipeline failed: Cannot fetch real data and fallback generation failed.")

    # 3. Save raw dataset
    os.makedirs(os.path.dirname(raw_data_path), exist_ok=True)
    df.to_csv(raw_data_path, index=False)
    log_info(logger, f"Raw dataset saved to {raw_data_path}")

    # 4. Save metadata
    metadata = {
        "dataset_source": source_info.get("source"),
        "validation_study_doi": source_info.get("doi", None),
        "stimuli_checksums": None, # Will be updated by T015
        "simulation_mode": simulation_mode,
        "timestamp": get_timestamp()
    }
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    log_info(logger, f"Metadata saved to {metadata_path}")

    # 5. Validate and Clean Data (T011, T012a, T012b logic)
    # Note: T010c orchestrates the flow, but the actual filtering logic is in validator.py
    # We call the validation and cleaning functions here to ensure the pipeline runs.
    try:
        log_info(logger, "Running validation and cleaning (T011)...")
        # Filter by age >= 65
        df_age = clean_data(df, min_age=65)
        log_info(logger, f"Age filtering complete. Rows: {len(df_age)}")

        # Filter by non-null scores
        df_score = clean_data(df_age, filter_scores=True)
        log_info(logger, f"Score filtering complete. Rows: {len(df_score)}")

        # Save cleaned intermediate data
        os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)
        df_score.to_csv(processed_data_path, index=False)
        log_info(logger, f"Cleaned data saved to {processed_data_path}")

    except Exception as e:
        log_error(logger, f"Data cleaning failed: {e}")
        raise

    end_time = time.time()
    duration = end_time - start_time
    log_info(logger, f"Pipeline orchestration completed in {duration:.2f} seconds.")
    return True

def main():
    """Entry point for the orchestrator."""
    try:
        success = run_orchestration()
        if success:
            log_info(logger, "Pipeline execution successful.")
            sys.exit(0)
        else:
            log_error(logger, "Pipeline execution returned failure status.")
            sys.exit(1)
    except Exception as e:
        log_error(logger, f"Fatal error in pipeline orchestration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()