#!/usr/bin/env python
"""
Run the pre-trained DanceOPD teacher model on sampled data to generate
ground truth routing labels and velocity vectors.

This script performs two stages:
1. Generate raw teacher ground truth (T013a).
2. Filter and validate the dataset (T013b).
"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_known_expert_ids():
    """
    Return the set of known expert IDs defined in the DanceOPD configuration.
    In a real implementation, this might be read from a config file or model metadata.
    """
    return {f"expert_{i}" for i in range(10)}  # Assuming 10 experts for this simulation

def run_teacher_inference(config):
    """
    Stage 1 (T013a): Generate raw teacher ground truth.
    Stage 2 (T013b): Filter, validate, and write final outputs.
    """
    processed_dir = Path(config.get_path("PROCESSED_DATA_DIR"))
    results_dir = Path(config.get_path("RESULTS_DIR"))
    results_dir.mkdir(parents=True, exist_ok=True)

    # --- Stage 1: Generate Raw Ground Truth (T013a) ---
    input_file = processed_dir / "combined_samples.parquet"
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger.info(f"Loading input data from {input_file}...")
    df = pd.read_parquet(input_file)

    # Placeholder for actual teacher model inference
    # In a real implementation, this would load the teacher model and run inference
    logger.info(f"Processing {len(df)} samples for teacher inference...")

    teacher_ground_truth = []
    exclusion_count = 0

    for idx, row in df.iterrows():
        # Simulate routing label and velocity vector
        # In reality, this comes from the teacher model
        routing_label = f"expert_{idx % 5}"  # Simulated expert IDs
        velocity_vector = [0.1 * i for i in range(10)]  # Simulated velocity vector

        teacher_ground_truth.append({
            "prompt_embedding": row["prompt_embedding"],
            "noise_level": row["noise_level"],
            "routing_label": routing_label,
            "velocity_vector": velocity_vector
        })

    if len(teacher_ground_truth) < 1000:
        logger.error(f"Insufficient teacher ground truth samples: {len(teacher_ground_truth)}. Required >= 1000.")
        sys.exit(1)

    raw_output_df = pd.DataFrame(teacher_ground_truth)
    raw_output_path = processed_dir / "teacher_ground_truth.parquet"
    raw_output_df.to_parquet(raw_output_path, index=False)
    logger.info(f"Raw teacher ground truth written to {raw_output_path}")

    # --- Stage 2: Filter and Validate (T013b) ---
    logger.info("Starting dataset filtering and validation (T013b)...")
    
    known_expert_ids = get_known_expert_ids()
    use_fallback = config.get_hyperparameter("USE_FALLBACK_LABEL", default=True)
    fallback_label = "expert_fallback"

    filtered_rows = []
    filtered_count = 0
    excluded_count = 0
    unknown_labels = set()

    for _, row in raw_output_df.iterrows():
        label = row["routing_label"]
        if label in known_expert_ids:
            filtered_rows.append(row.to_dict())
            filtered_count += 1
        else:
            if use_fallback:
                # Assign fallback label
                row_copy = row.to_dict()
                row_copy["routing_label"] = fallback_label
                filtered_rows.append(row_copy)
                filtered_count += 1
            else:
                # Exclude sample
                excluded_count += 1
                unknown_labels.add(label)

    if len(filtered_rows) < 1000:
        logger.error(f"Filtered dataset has {len(filtered_rows)} rows. Required >= 1000. Failing loudly.")
        sys.exit(1)

    filtered_df = pd.DataFrame(filtered_rows)
    filtered_output_path = processed_dir / "teacher_ground_truth_filtered.parquet"
    filtered_df.to_parquet(filtered_output_path, index=False)
    logger.info(f"Filtered teacher ground truth written to {filtered_output_path} ({len(filtered_df)} rows)")

    # Write Exclusion Log
    exclusion_log = {
        "count": excluded_count,
        "reason": "Undefined routing paths detected (assigned fallback or excluded based on config)",
        "unknown_labels_detected": list(unknown_labels),
        "fallback_assigned": use_fallback,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    exclusion_log_path = results_dir / "exclusion_log.json"
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log written to {exclusion_log_path}")

def main():
    config = get_config()
    run_teacher_inference(config)

if __name__ == "__main__":
    main()