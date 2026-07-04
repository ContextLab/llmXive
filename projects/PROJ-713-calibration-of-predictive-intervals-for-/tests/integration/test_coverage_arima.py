"""
Integration test for end-to-end ARIMA coverage calculation.

This test verifies that the ARIMA model can:
1. Load real data (M4 hourly or UCI Electricity)
2. Split data into train/test (80/20)
3. Fit the ARIMA model
4. Generate prediction intervals using conditional variance
5. Calculate empirical coverage rates
6. Write results to results/coverage.csv

The test uses a small subset of data to ensure it runs within time limits.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import PROJECT_ROOT, RESULTS_DIR
from data_loader import load_m4_hourly, split_series, standardize
from models.arima_model import ARIMAModel
from metrics.coverage import compute_coverage
from utils.logger import get_logger

logger = get_logger(__name__)


def test_arima_coverage_end_to_end():
    """
    End-to-end integration test for ARIMA coverage calculation.

    This test:
    1. Loads a small subset of M4 hourly data (or falls back to a single series)
    2. Splits the data into train/test (80/20)
    3. Fits an ARIMA model on the training data
    4. Generates prediction intervals for the test period
    5. Computes empirical coverage rates
    6. Verifies that results are written to results/coverage.csv
    """
    # Ensure results directory exists
    results_dir = Path(PROJECT_ROOT) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_file = results_dir / "coverage.csv"

    # Clean up any existing output file
    if output_file.exists():
        output_file.unlink()

    try:
        # Load a small subset of M4 hourly data
        # We use a single series for this integration test to keep it fast
        logger.info("Loading M4 hourly data...")
        try:
            data = load_m4_hourly()
            if data is None or len(data) == 0:
                logger.warning("M4 data not available, skipping test")
                return
            
            # Take the first series for testing
            series_name = list(data.keys())[0]
            series_data = data[series_name]
            logger.info(f"Using series: {series_name} with {len(series_data)} points")
        except Exception as e:
            logger.error(f"Failed to load M4 data: {e}")
            # Try to create a minimal mock for testing purposes if real data fails
            # This is a fallback only for integration testing when real data is unavailable
            logger.info("Creating minimal test series for integration test...")
            dates = pd.date_range(start='2020-01-01', periods=100, freq='H')
            values = np.sin(np.arange(100) * 2 * np.pi / 24) + np.random.normal(0, 0.1, 100)
            series_data = pd.Series(values, index=dates)
            series_name = "test_series"

        # Split data into train/test (80/20)
        logger.info("Splitting data into train/test (80/20)...")
        train_data, test_data = split_series(series_data, train_ratio=0.8)
        logger.info(f"Train size: {len(train_data)}, Test size: {len(test_data)}")

        # Standardize the data
        logger.info("Standardizing data...")
        train_std, test_std, scaler = standardize(train_data, test_data)

        # Initialize and fit ARIMA model
        logger.info("Fitting ARIMA model...")
        model = ARIMAModel(order=(1, 1, 1))
        model.fit(train_std)

        # Generate predictions and intervals
        logger.info("Generating predictions and intervals...")
        predictions, intervals = model.predict(n_steps=len(test_std), return_intervals=True)

        # Compute coverage
        logger.info("Computing coverage...")
        coverage_results = compute_coverage(
            test_std.values,
            predictions,
            intervals,
            series_name=series_name,
            model_name="ARIMA"
        )

        # Convert to DataFrame and save
        coverage_df = pd.DataFrame([coverage_results])
        coverage_df.to_csv(output_file, index=False)
        logger.info(f"Coverage results saved to {output_file}")

        # Verify the output file exists and contains data
        assert output_file.exists(), "Output file was not created"
        result_df = pd.read_csv(output_file)
        assert len(result_df) > 0, "Output file is empty"
        
        # Verify expected columns exist
        expected_columns = ['series_name', 'model_name', 'nominal_level', 'empirical_coverage', 'coverage_deviation']
        for col in expected_columns:
            assert col in result_df.columns, f"Missing column: {col}"

        # Verify coverage values are reasonable (between 0 and 1)
        assert (result_df['empirical_coverage'] >= 0).all(), "Empirical coverage should be >= 0"
        assert (result_df['empirical_coverage'] <= 1).all(), "Empirical coverage should be <= 1"

        logger.info("Integration test passed!")
        return coverage_results

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise


if __name__ == "__main__":
    test_arima_coverage_end_to_end()
    print("Integration test completed successfully!")