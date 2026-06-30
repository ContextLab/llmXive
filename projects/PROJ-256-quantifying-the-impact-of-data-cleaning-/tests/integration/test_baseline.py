"""
Integration test for User Story 1: Baseline Analysis.

Verifies that the baseline analysis script produces `data/processed/baseline_metrics.json`
with valid p-values (0 < p < 1) and finite Confidence Intervals (CI).

This test executes the full pipeline:
1. Loads a real dataset (UCI HAR or Shopper).
2. Runs statistical analyses (t-tests, linear regression).
3. Writes the results to disk.
4. Validates the output file contents.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from utils import pin_random_seed, setup_logging
from config import get_config
from data_loader import load_and_prepare_dataset
from analysis import run_baseline_analysis

# Configure logging for the test
logger = setup_logging("INFO")
pin_random_seed(42)

def test_baseline_analysis_produces_valid_metrics():
    """
    Integration test: Verify baseline analysis script produces valid output.
    
    Requirements:
    1. Output file `data/processed/baseline_metrics.json` must exist.
    2. P-values must be strictly between 0 and 1.
    3. CI bounds (lower, upper) must be finite numbers.
    """
    # Ensure output directory exists
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "baseline_metrics.json"
    
    # Clean up any existing file to ensure we are testing the fresh run
    if output_file.exists():
        output_file.unlink()

    try:
        # 1. Load a real dataset
        # We attempt to load the HAR dataset first as per T011 logic
        logger.info("Loading dataset for baseline analysis...")
        df, metadata = load_and_prepare_dataset("hars")
        
        if df is None or df.empty:
            # Fallback to Shopper if HAR fails (though T011 handles fallback logic internally,
            # we ensure we have data here for the test to proceed)
            logger.warning("HAR dataset load failed or empty, trying Shopper...")
            df, metadata = load_and_prepare_dataset("shopper")
        
        assert df is not None and not df.empty, "Failed to load any real dataset for baseline analysis."
        logger.info(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns.")

        # 2. Run the baseline analysis
        logger.info("Running baseline statistical analysis...")
        # The analysis function writes directly to the configured output path
        # We pass the dataframe directly to the analysis logic
        results = run_baseline_analysis(df, metadata)
        
        # 3. Verify the file was written
        assert output_file.exists(), f"Output file {output_file} was not created."
        logger.info(f"Output file created: {output_file}")

        # 4. Load and validate the JSON content
        with open(output_file, 'r') as f:
            metrics_data = json.load(f)

        assert isinstance(metrics_data, list), "Expected metrics to be a list of analysis results."
        assert len(metrics_data) > 0, "Expected at least one analysis result in the metrics file."

        logger.info("Validating p-values and Confidence Intervals...")
        
        validation_errors = []
        for i, result in enumerate(metrics_data):
            # Check p-value
            p_val = result.get("p_value")
            if p_val is None:
                validation_errors.append(f"Result {i}: Missing 'p_value'")
            elif not (0 < p_val < 1):
                validation_errors.append(f"Result {i}: p_value {p_val} is not in (0, 1)")
            
            # Check CI bounds
            ci = result.get("confidence_interval", {})
            ci_lower = ci.get("lower")
            ci_upper = ci.get("upper")
            
            if ci_lower is None or ci_upper is None:
                validation_errors.append(f"Result {i}: Missing CI bounds")
            elif not (np.isfinite(ci_lower) and np.isfinite(ci_upper)):
                validation_errors.append(f"Result {i}: CI bounds are not finite (lower={ci_lower}, upper={ci_upper})")
            
            # Check effect size exists (bonus validation)
            if "effect_size" not in result:
                validation_errors.append(f"Result {i}: Missing 'effect_size'")

        if validation_errors:
            error_msg = "Validation failed:\n" + "\n".join(validation_errors)
            raise AssertionError(error_msg)

        logger.info("SUCCESS: All p-values are valid (0 < p < 1) and all CIs are finite.")
        logger.info(f"Total results validated: {len(metrics_data)}")

    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        raise
    finally:
        # Optional: Clean up the generated file after test if desired, 
        # but keeping it allows manual inspection. 
        # For strict CI, we might remove it:
        # if output_file.exists(): output_file.unlink()
        pass

if __name__ == "__main__":
    test_baseline_analysis_produces_valid_metrics()
    print("Integration test passed.")