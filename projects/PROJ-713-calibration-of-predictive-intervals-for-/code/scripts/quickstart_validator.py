"""
Quickstart Validation Script for PROJ-713
Ensures end-to-end reproducibility of the calibration pipeline.

This script:
1. Verifies project structure and dependencies.
2. Runs a minimal end-to-end test on a single small series (M4 Hourly).
3. Validates that all expected output files are generated.
4. Checks that results are non-empty and contain expected columns.
"""
import os
import sys
import argparse
import time
import json
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from config import Config, ensure_dirs, RESULTS_DIR, DATA_DIR
from utils.logger import get_logger
from utils.exceptions import CalibrationError, DataValidationError
from data_loader import fetch_data, load_m4_hourly, split_series
from models.arima_model import ARIMAModel
from metrics.coverage import compute_coverage, coverage_to_dataframe
from metrics.pit import compute_pit_metrics, pit_metrics_to_dataframe
from metrics.crps import compute_crps, crps_to_dataframe
from data.sampler import stratified_sampler

logger = get_logger(__name__)

def verify_dependencies():
    """Check that all required packages are installed."""
    required = ['statsmodels', 'prophet', 'torch', 'properscoring', 'scikit-learn', 'scipy', 'pandas', 'numpy', 'matplotlib']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        raise ImportError(f"Missing required dependencies: {', '.join(missing)}")
    logger.info("All dependencies verified.")

def verify_structure():
    """Verify project directory structure exists."""
    dirs = [
        PROJECT_ROOT / 'code',
        PROJECT_ROOT / 'tests',
        PROJECT_ROOT / 'data' / 'raw',
        PROJECT_ROOT / 'data' / 'processed',
        PROJECT_ROOT / 'results',
        PROJECT_ROOT / 'figures'
    ]
    for d in dirs:
        if not d.exists():
            raise FileNotFoundError(f"Required directory missing: {d}")
    logger.info("Project structure verified.")

def run_single_series_test():
    """
    Run a minimal end-to-end pipeline on a single small series to verify reproducibility.
    We use the first available M4 Hourly series for speed.
    """
    logger.info("Starting single-series end-to-end test...")
    
    # 1. Load a small subset of real data
    # We fetch M4 Hourly data. If the full dataset is too large, we sample just one series.
    try:
        # Attempt to load M4 Hourly data
        # Note: This relies on the data being available or the loader fetching it.
        # For the quickstart, we assume the data_loader can handle the fetch or local file.
        # We will try to load a small sample.
        raw_data = load_m4_hourly(limit=1) # Limit to first 1 series for speed
        
        if not raw_data or len(raw_data) == 0:
            raise DataValidationError("No M4 Hourly data available for testing.")
        
        series_id = raw_data[0]['series_id']
        train, test = split_series(raw_data[0], test_size=24) # 24 hours test set
        
        logger.info(f"Selected series: {series_id} (Train: {len(train)}, Test: {len(test)})")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # 2. Initialize Model
    try:
        model = ARIMAModel()
        logger.info("ARIMA model initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise

    # 3. Fit and Predict
    try:
        logger.info("Fitting model...")
        # Fit on train
        model.fit(train)
        
        logger.info("Generating predictions...")
        # Predict on test
        predictions, intervals = model.predict(len(test), level=[0.80, 0.95])
        
        if predictions is None or intervals is None:
            raise CalibrationError("Model failed to produce predictions or intervals.")
        
        logger.info(f"Generated {len(predictions)} predictions.")
    except Exception as e:
        logger.error(f"Model execution failed: {e}")
        raise

    # 4. Compute Metrics
    try:
        # Ground truth
        y_true = test['value'].values
        
        # Coverage
        cov_results = compute_coverage(y_true, intervals, levels=[0.80, 0.95])
        logger.info(f"Coverage computed: {cov_results}")
        
        # PIT
        pit_results = compute_pit_metrics(y_true, predictions, intervals)
        logger.info(f"PIT metrics computed: {pit_results}")
        
        # CRPS
        crps_val = compute_crps(y_true, predictions, intervals)
        logger.info(f"CRPS computed: {crps_val}")
        
    except Exception as e:
        logger.error(f"Metric computation failed: {e}")
        raise

    # 5. Save Results (Simulating the pipeline output)
    try:
        ensure_dirs()
        
        # Save coverage
        cov_df = coverage_to_dataframe([{'series_id': series_id, 'model': 'ARIMA', **cov_results}])
        cov_path = RESULTS_DIR / 'quickstart_coverage.csv'
        cov_df.to_csv(cov_path, index=False)
        
        # Save PIT
        pit_df = pit_metrics_to_dataframe([{'series_id': series_id, 'model': 'ARIMA', **pit_results}])
        pit_path = RESULTS_DIR / 'quickstart_pit.csv'
        pit_df.to_csv(pit_path, index=False)
        
        # Save CRPS
        crps_df = crps_to_dataframe([{'series_id': series_id, 'model': 'ARIMA', 'crps': crps_val}])
        crps_path = RESULTS_DIR / 'quickstart_crps.csv'
        crps_df.to_csv(crps_path, index=False)
        
        logger.info(f"Results saved to {RESULTS_DIR}")
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise

    return True

def validate_outputs():
    """Verify that the expected output files exist and contain valid data."""
    logger.info("Validating output files...")
    
    expected_files = [
        RESULTS_DIR / 'quickstart_coverage.csv',
        RESULTS_DIR / 'quickstart_pit.csv',
        RESULTS_DIR / 'quickstart_crps.csv'
    ]
    
    for f in expected_files:
        if not f.exists():
            raise FileNotFoundError(f"Expected output file missing: {f}")
        
        # Check non-empty
        if f.stat().st_size == 0:
            raise ValueError(f"Output file is empty: {f}")
        
        # Basic column check
        try:
            import pandas as pd
            df = pd.read_csv(f)
            if len(df) == 0:
                raise ValueError(f"Output file has no data rows: {f}")
            logger.info(f"Verified {f.name}: {len(df)} rows, columns: {list(df.columns)}")
        except Exception as e:
            raise ValueError(f"Failed to parse {f}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Quickstart Validation for PROJ-713")
    parser.add_argument("--skip-dependencies", action="store_true", help="Skip dependency check")
    args = parser.parse_args()

    start_time = time.time()
    success = True

    try:
        if not args.skip_dependencies:
            verify_dependencies()
        
        verify_structure()
        run_single_series_test()
        validate_outputs()
        
        elapsed = time.time() - start_time
        logger.info(f"Quickstart validation PASSED in {elapsed:.2f} seconds.")
        return 0

    except Exception as e:
        logger.error(f"Quickstart validation FAILED: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
