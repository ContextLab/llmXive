"""
T014: Inject anomalies into time series data using the anomaly_injector library.

This script invokes `code/lib/anomaly_injector.py` with research parameters to:
1. Load real time series data from `data/raw/series.csv` (downloaded by T004/T003).
2. Inject anomalies (mean shifts, variance spikes, gradual drift) based on a config.
3. Save the modified series to `data/processed/series_with_anomalies.csv`.
4. Save the ground truth labels to `data/processed/ground_truth.csv`.

Execution:
    python code/scripts/inject_anomalies.py
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path to allow imports from code/lib
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from lib.anomaly_injector import (
    load_config,
    inject_anomalies_from_config,
    main as injector_main
)
from lib.data_loader import load_time_series
from lib.utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
INPUT_FILE = DATA_RAW_DIR / "series.csv"
OUTPUT_SERIES_FILE = DATA_PROCESSED_DIR / "series_with_anomalies.csv"
OUTPUT_GT_FILE = DATA_PROCESSED_DIR / "ground_truth.csv"
CONFIG_FILE = project_root / "data" / "anomaly_config.json"

# Research parameters per FR-009 and Reviewer comments
# Mean shift: 2.5 standard deviations
# Variance spike: 3x baseline variance
# Duration: 5-15 consecutive time points (using 5 for variance spike window)
DEFAULT_CONFIG = {
    "seed": 42,
    "anomalies": [
        {
            "type": "mean_shift",
            "magnitude_std": 2.5,
            "direction": "positive",
            "count": 3,
            "spacing_factor": 0.15
        },
        {
            "type": "mean_shift",
            "magnitude_std": 2.5,
            "direction": "negative",
            "count": 2,
            "spacing_factor": 0.25
        },
        {
            "type": "variance_spike",
            "variance_multiplier": 3.0,
            "window_size": 5,
            "count": 3,
            "spacing_factor": 0.20
        },
        {
            "type": "gradual_drift",
            "slope": 0.5,
            "duration": 10,
            "count": 1,
            "spacing_factor": 0.5
        }
    ]
}

def ensure_config():
    """Ensure the anomaly configuration file exists."""
    if not CONFIG_FILE.exists():
        logger.info(f"Creating default config at {CONFIG_FILE}")
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    return CONFIG_FILE

def main():
    """Main entry point for T014."""
    logger.info("Starting anomaly injection pipeline (T014)...")

    # 1. Setup
    set_seed(42)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Ensure config exists (with research parameters)
    config_path = ensure_config()
    logger.info(f"Loading config from {config_path}")
    config = load_config(config_path)

    # 3. Load real data
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.error("Please run download_data.py (T003) first to populate data/raw/series.csv")
        sys.exit(1)

    logger.info(f"Loading time series from {INPUT_FILE}")
    try:
        series_df = load_time_series(INPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to load time series: {e}")
        sys.exit(1)

    if series_df.empty:
        logger.error("Loaded time series is empty.")
        sys.exit(1)

    # Determine the value column
    value_col = None
    for col in ['value', 'Value', 'values', 'y', 'Y']:
        if col in series_df.columns:
            value_col = col
            break
    
    if value_col is None:
        # Fallback to first column
        value_col = series_df.columns[0]
        logger.warning(f"Standard column names not found. Using '{value_col}' as value column.")

    series_values = series_df[value_col].values.astype(float)
    logger.info(f"Loaded {len(series_values)} data points from column '{value_col}'.")

    # 4. Inject anomalies using the library
    logger.info("Injecting anomalies based on configuration...")
    
    # We need to adapt the library call to return both the modified series and ground truth
    # The library function `inject_anomalies_from_config` expects a numpy array and config
    # and returns (modified_series, ground_truth_array)
    
    try:
        anomalous_series, ground_truth = inject_anomalies_from_config(
            series_values, 
            config
        )
    except Exception as e:
        logger.error(f"Anomaly injection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 5. Save outputs
    logger.info(f"Saving anomalous series to {OUTPUT_SERIES_FILE}")
    output_df = pd.DataFrame({value_col: anomalous_series})
    # Preserve index if it exists, otherwise default 0..N-1
    if 'timestamp' in series_df.columns:
        output_df.insert(0, 'timestamp', series_df['timestamp'])
    output_df.to_csv(OUTPUT_SERIES_FILE, index=False)

    logger.info(f"Saving ground truth to {OUTPUT_GT_FILE}")
    gt_df = pd.DataFrame({
        'index': range(len(ground_truth)),
        'is_anomaly': ground_truth.astype(int)
    })
    # Add timestamp if available for alignment
    if 'timestamp' in series_df.columns:
        gt_df.insert(0, 'timestamp', series_df['timestamp'].values)
    gt_df.to_csv(OUTPUT_GT_FILE, index=False)

    # 6. Summary
    total_anomalies = int(ground_truth.sum())
    total_points = len(ground_truth)
    anomaly_rate = 100.0 * total_anomalies / total_points if total_points > 0 else 0.0

    logger.info("=" * 50)
    logger.info("Injection Summary:")
    logger.info(f"  Total points: {total_points}")
    logger.info(f"  Anomalies injected: {total_anomalies} ({anomaly_rate:.2f}%)")
    logger.info(f"  Output series: {OUTPUT_SERIES_FILE}")
    logger.info(f"  Output ground truth: {OUTPUT_GT_FILE}")
    logger.info("=" * 50)

    print(f"T014 completed successfully. Files saved to {DATA_PROCESSED_DIR}")

if __name__ == "__main__":
    # Import pandas here to avoid circular imports or if not needed in library scope
    import pandas as pd
    main()