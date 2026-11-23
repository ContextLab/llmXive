"""
Script to Inject Anomalies into Time Series Data.

This script invokes the anomaly injector library to inject synthetic anomalies
into a time series dataset based on a configuration file. It produces two output files:
1. The time series with injected anomalies.
2. The ground truth labels indicating the anomaly locations.

Author: Research Team
Date: 2026-04-29
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from lib.anomaly_injector import inject_anomalies_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_config(config_path: Path) -> Path:
    """
    Ensure the configuration file exists, creating a default one if not.

    Args:
        config_path (Path): Path to the configuration file.

    Returns:
        Path: Path to the configuration file.
    """
    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        logger.info("Creating default configuration file...")

        # Default configuration based on T006b schema defaults
        default_config = {
            "mean_shift_range": [0.5, 2.0],
            "variance_ratio_range": [2.0, 5.0],
            "drift_duration_range": [5, 15],
            "anomalies": [
                {
                    "type": "mean_shift",
                    "shift_magnitude": 2.5,
                    "duration_range": [5, 15],
                    "min_gap": 10
                },
                {
                    "type": "variance_spike",
                    "variance_multiplier": 3.0,
                    "duration_range": [5, 15],
                    "min_gap": 10
                },
                {
                    "type": "gradual_drift",
                    "drift_rate": 0.1,
                    "duration_range": [10, 20],
                    "min_gap": 15
                }
            ]
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        logger.info(f"Default configuration created at {config_path}")

    return config_path


def main() -> None:
    """
    Main entry point for the anomaly injection script.
    """
    # Define paths
    # Ensure we use the correct paths as per tasks.md and project structure
    data_path = project_root / "data" / "raw" / "series.csv"
    config_path = project_root / "code" / "config" / "anomaly_injection_config.yaml"
    
    # If the YAML config doesn't exist, try the JSON path for backwards compatibility
    if not config_path.exists():
        config_path = project_root / "data" / "processed" / "anomaly_config.json"
    
    output_path = project_root / "data" / "processed" / "series_with_anomalies.csv"
    ground_truth_path = project_root / "data" / "processed" / "ground_truth.csv"

    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if input data exists
    if not data_path.exists():
        logger.error(f"Input data file not found: {data_path}")
        logger.error("Please run download_data.py first to fetch the time series data.")
        sys.exit(1)

    # Ensure configuration exists
    config_path = ensure_config(config_path)

    # Run anomaly injection
    try:
        logger.info("Starting anomaly injection...")
        logger.info(f"Loading data from: {data_path}")
        logger.info(f"Using config from: {config_path}")
        
        df_anomaly, df_ground_truth = inject_anomalies_from_file(
            data_path=data_path,
            config_path=config_path,
            output_path=output_path,
            ground_truth_path=ground_truth_path,
            seed=42  # Fixed seed for reproducibility
        )

        logger.info(f"Successfully saved data with anomalies to: {output_path}")
        logger.info(f"Successfully saved ground truth to: {ground_truth_path}")
        logger.info(f"Anomaly injection completed. Total anomalies injected: "
                    f"{df_ground_truth['is_anomaly'].sum()}")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        logger.error("T006b (anomaly_injection_config.yaml) must be completed first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Anomaly injection failed: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
