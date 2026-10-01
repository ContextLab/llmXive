"""
Main orchestration script for the M4 Calibration Evaluation Pipeline.

This script coordinates the download, sampling, model fitting, and evaluation steps.
It specifically implements the T053 requirement to log sample metadata after the
selection phase.
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd

from download import load_m4_metadata, stratified_sample_metadata, log_sample_metadata
from run_pipeline import run_pipeline
from aggregate_coverage import main as aggregate_main
from sensitivity_analysis import main as sensitivity_main
from statistical_significance import main as stats_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Execute the full pipeline."""
    start_time = time.time()

    # Parse arguments
    parser = argparse.ArgumentParser(description="M4 Calibration Evaluation Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--data_dir", type=str, default="data/raw", help="Path to raw data")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Path to processed data")
    args = parser.parse_args()

    logger.info("Starting M4 Calibration Evaluation Pipeline...")

    # 1. Load Configuration
    # Assuming config.yaml is in root or passed via arg
    config_path = args.config
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    nominal_levels = config.get('nominal_levels', [0.80, 0.95])
    seed = config.get('seed', 42)
    max_samples = config.get('max_samples', 1000) # Default from task spec

    # 2. Load Metadata (Assumes T004/T013c has validated and extracted metadata)
    # The metadata file location is assumed to be data/raw/M4-metadata.csv or similar
    # We attempt to find it or load from the processed directory if T013a ran
    metadata_path = os.path.join(args.data_dir, "M4-metadata.csv")
    if not os.path.exists(metadata_path):
        # Fallback to processed if raw doesn't have it (T013a might have created it)
        metadata_path = os.path.join(args.processed_dir, "M4-metadata.csv")
    
    if not os.path.exists(metadata_path):
        logger.error("M4 Metadata file not found. Ensure T004/T013a is complete.")
        sys.exit(1)

    logger.info(f"Loading metadata from {metadata_path}...")
    metadata = load_m4_metadata(metadata_path)

    # 3. Select Sample (T013a-2 logic)
    logger.info("Selecting stratified sample...")
    # Target distribution is implicitly the full distribution of frequencies in metadata
    # We pass the full metadata to the selector to calculate the target distribution internally
    # or we pre-calculate it here. For T053, we just need to log the result.
    
    selected_ids = stratified_sample_metadata(
        metadata=metadata,
        target_distribution={}, # Not strictly needed if proportional
        seed=seed,
        max_samples=max_samples,
        min_length=50
    )

    logger.info(f"Selected {len(selected_ids)} series.")

    # 4. T053: Log Sample Metadata
    # This is the core deliverable for T053
    sample_metadata_path = os.path.join(args.processed_dir, "sample_metadata.json")
    log_sample_metadata(
        selected_ids=selected_ids,
        method="stratified by frequency",
        seed=seed,
        nominal_levels=nominal_levels,
        output_path=sample_metadata_path
    )

    # 5. Save indices for downstream tasks (T013b-2)
    indices_path = os.path.join(args.processed_dir, "sample_indices.csv")
    pd.DataFrame({'id': selected_ids}).to_csv(indices_path, index=False)
    logger.info(f"Sample indices saved to {indices_path}")

    # 6. Run Pipeline (T014-T019)
    logger.info("Running forecasting and evaluation pipeline...")
    # Assuming run_pipeline handles the rest: model fitting, interval generation, coverage calc
    # We pass the indices file path
    run_pipeline(
        config_path=config_path,
        indices_path=indices_path,
        data_dir=args.data_dir,
        processed_dir=args.processed_dir
    )

    # 7. Aggregate and Finalize
    logger.info("Aggregating results...")
    aggregate_main()
    stats_main()
    sensitivity_main()

    end_time = time.time()
    elapsed = end_time - start_time
    
    # Record runtime (T020b)
    runtime_path = "state/runtime.log"
    with open(runtime_path, 'w') as f:
        f.write(f"{elapsed:.2f}")
    
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
