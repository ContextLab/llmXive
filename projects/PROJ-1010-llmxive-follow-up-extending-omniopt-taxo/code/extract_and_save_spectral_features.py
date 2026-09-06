"""
Task T013c: Write extracted SpectralFeatureVector records to CSV.

This script orchestrates the full extraction pipeline for selected models,
computes spectral features (including Tail Decay and Entropy), and writes
the results to data/processed/spectral_features.csv.

It depends on T012 (model selection/proxy training) and T013/T013b (feature math).
"""
import os
import sys
import csv
import json
import gc
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = DATA_PROCESSED_DIR / "spectral_features.csv"

# Ensure we can import sibling modules
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from spectral_extractor import (
    run_proxy_training,
    compute_spectral_features,
    select_models,
    count_parameters,
    get_logger,
    info,
    error,
    warning,
    TimeoutError,
)
from utils.logging import set_correlation_id, configure_logging
from utils.seeds import set_seed
from utils.memory_monitor import enforce_memory_limit

logger = get_logger(__name__)


def save_features_to_csv(features: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write a list of SpectralFeatureVector dictionaries to a CSV file.

    Expected keys in each dict:
      - model_id
      - architecture
      - param_count
      - spectral_radius
      - condition_number
      - tail_decay_exponent
      - spectral_entropy
      - status (success/failure)
      - timestamp
    """
    if not features:
        logger.warning("No features to write.")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define column order
    fieldnames = [
        "model_id",
        "architecture",
        "param_count",
        "spectral_radius",
        "condition_number",
        "tail_decay_exponent",
        "spectral_entropy",
        "status",
        "timestamp",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)

    logger.info(f"Successfully wrote {len(features)} records to {output_path}")


def main() -> int:
    """
    Main entry point for T013c.
    1. Select models.
    2. Run proxy training (or load cached if logic exists, but per spec we run).
    3. Compute spectral features.
    4. Save to CSV.
    """
    configure_logging()
    set_correlation_id(f"T013c-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    set_seed(42)

    # Memory limit: 7GB
    enforce_memory_limit(7 * 1024 * 1024 * 1024)

    info("Starting T013c: Spectral Feature Extraction and Save")

    # 1. Select models
    try:
        models = select_models()
        if not models:
            error("No models selected for analysis.")
            return 1
        info(f"Selected {len(models)} models for analysis.")
    except Exception as e:
        error(f"Failed to select models: {e}")
        return 1

    all_features: List[Dict[str, Any]] = []

    # 2. Process each model
    for model_spec in models:
        model_id = model_spec.get("model_id")
        architecture = model_spec.get("architecture")
        info(f"Processing model: {model_id} ({architecture})")

        try:
            # Run proxy training to get gradients
            # This returns a structure containing gradients or covariance info
            training_result = run_proxy_training(model_spec)

            if training_result is None:
                warning(f"Proxy training returned None for {model_id}. Skipping.")
                continue

            # Compute spectral features
            # Expected keys: spectral_radius, condition_number, tail_decay_exponent, spectral_entropy
            features = compute_spectral_features(training_result)

            if features is None:
                warning(f"Feature computation failed for {model_id}. Skipping.")
                continue

            # Construct record
            record = {
                "model_id": model_id,
                "architecture": architecture,
                "param_count": count_parameters(model_spec.get("model_name")), # Helper to count
                "spectral_radius": features.get("spectral_radius"),
                "condition_number": features.get("condition_number"),
                "tail_decay_exponent": features.get("tail_decay_exponent"),
                "spectral_entropy": features.get("spectral_entropy"),
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            all_features.append(record)
            info(f"Saved features for {model_id}")

        except TimeoutError:
            warning(f"Timeout processing {model_id}. Recording failure.")
            all_features.append({
                "model_id": model_id,
                "architecture": architecture,
                "param_count": 0,
                "spectral_radius": None,
                "condition_number": None,
                "tail_decay_exponent": None,
                "spectral_entropy": None,
                "status": "timeout",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            error(f"Unexpected error processing {model_id}: {e}", exc_info=True)
            all_features.append({
                "model_id": model_id,
                "architecture": architecture,
                "param_count": 0,
                "spectral_radius": None,
                "condition_number": None,
                "tail_decay_exponent": None,
                "spectral_entropy": None,
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Force cleanup between models
        gc.collect()

    # 3. Save to CSV
    if not all_features:
        error("No features were generated. Aborting save.")
        return 1

    save_features_to_csv(all_features, OUTPUT_FILE)

    info("T013c completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
