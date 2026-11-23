import os
import sys
import json
import argparse
from pathlib import Path

from config import ensure_directories
from models.trainer import create_trainer, Trainer
from analysis.metadata_stats import load_dataset_list, process_single_dataset
from utils.logging import get_logger, log_info, log_error

def main(run_id: str):
    """
    Trains the projection layer on all available datasets, consuming metadata stats.
    """
    ensure_directories(["data/processed", "data/artifacts"]) # Ensure output directories exist
    log_info("Starting run_conditioned.py")

    # Load dataset list from config (or default)
    dataset_list = load_dataset_list()
    log_info(f"Loaded {len(dataset_list)} datasets.")

    # Prepare metadata stats for all datasets
    metadata_stats = {}
    for dataset_id in dataset_list:
        try:
            metadata_path = Path("data/processed") / f"metadata_stats_{dataset_id}.json"
            with open(metadata_path, "r") as f:
                metadata_stats[dataset_id] = json.load(f)

        except FileNotFoundError:
            log_error(f"Metadata stats file not found for dataset {dataset_id}")
            continue  # Skip to the next one if missing metadata.

    # Create and train the projection layer
    trainer = create_trainer()

    for dataset_id in dataset_list:
      if dataset_id in metadata_stats:
        try:
          log_info(f"Training projection layer for dataset {dataset_id}...")
          trainer.train(dataset_id, metadata_stats[dataset_id])  # Pass metadata stats

          log_info(f"Finished training for dataset {dataset_id}")
        except Exception as e:
            log_error(f"Error training on dataset {dataset_id}: {e}")
      else:
        log_warning(f"Skipping dataset {dataset_id} - no metadata available.")

    log_info("Finished run_conditioned.py")
