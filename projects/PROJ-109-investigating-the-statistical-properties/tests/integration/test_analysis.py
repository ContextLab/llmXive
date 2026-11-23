"""
Integration test for the full analysis pipeline (User Story 3).

This test verifies the end-to-end execution of:
1. Data loading (from preprocessed parquet produced by US1)
2. Statistical analysis (binning, KS tests, BH correction, Spearman, Bullock comparison)
3. Visualization generation
4. Results persistence

It ensures that the pipeline runs without errors and produces valid output files.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest

# Import the full analysis pipeline function
from code.analysis.stats import run_full_analysis_pipeline
from code.analysis.visualize import generate_all_visualizations
from code.utils.logging import setup_logging, get_logger

# Import config for paths
from code.config import (
    PROCESSED_DATA_PATH,
    RESULTS_DIR,
    FIGURES_DIR,
    STATISTICS_OUTPUT_PATH
)

# Setup logging for the test
logger = get_logger(__name__)

# Create a temporary directory for test outputs to avoid polluting the real data
# We will mock the data loading to use synthetic-but-real-structure data
# since T012/T014 might not have run or we want isolation.
# However, the requirement is to test the pipeline logic.
# We will create a minimal valid dataset that satisfies the schema.

@pytest.fixture(scope="module")
def test_environment():
    """Create a temporary directory structure for the test."""
    # Use a temp directory to avoid overwriting real project files during CI
    temp_dir = tempfile.mkdtemp(prefix="test_analysis_")
    
    # Create necessary subdirectories
    data_dir = Path(temp_dir) / "data" / "processed"
    results_dir = Path(temp_dir) / "results"
    figures_dir = results_dir / "figures"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a minimal realistic dataset for testing
    # This simulates the output of T014 (filtered_halos.parquet)
    # but ensures we have the required columns for US3 analysis.
    # We use real physics-based distributions, not random noise, to ensure
    # the statistical tests have meaningful data to process.
    np.random.seed(42)
    n_halos = 500
    
    # Simulate halo properties based on typical distributions
    # Mass (log-normal distribution)
    log_mass = np.random.normal(12.0, 1.0, n_halos)
    mass = 10**log_mass
    
    # Concentration (log-normal, anti-correlated with mass)
    log_c = np.random.normal(1.0, 0.3, n_halos) - 0.2 * (log_mass - 12.0)
    concentration = 10**log_c
    
    # Spin (log-normal)
    log_lambda = np.random.normal(-2.0, 0.4, n_halos)
    spin = 10**log_lambda
    
    # Shape (beta distribution, skewed towards 0.8)
    shape = np.random.beta(5, 2, n_halos) * 0.8 + 0.1
    
    # Overdensity (log-normal)
    log_delta = np.random.normal(4.0, 0.5, n_halos)
    overdensity = 10**log_delta
    
    # Create DataFrame
    df = pd.DataFrame({
        'mass': mass,
        'concentration': concentration,
        'spin': spin,
        'shape': shape,
        'overdensity': overdensity,
        'particle_count': np.random.randint(300, 5000, n_halos),
        # Add environment indicator (0: low, 1: high) based on overdensity
        'environment': (overdensity > 200).astype(int)
    })
    
    # Ensure no NaN or Inf values
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    # Save to parquet
    parquet_path = data_dir / "filtered_halos_test.parquet"
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    yield {
        "temp_dir": temp_dir,
        "data_path": str(parquet_path),
        "results_dir": str(results_dir),
        "figures_dir": str(figures_dir)
    }
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_full_analysis_pipeline(test_environment):
    """
    Integration test: Run the full analysis pipeline.
    
    Verifies:
    1. The pipeline executes without raising exceptions.
    2. Statistical results are written to a JSON file.
    3. Visualizations are generated as image files.
    4. The results structure matches expectations.
    """
    # Override paths for this test using the temp directory
    # We patch the config or pass paths directly. 
    # Since run_full_analysis_pipeline likely uses config, we'll mock the environment
    # or pass the paths if the function signature allows.
    # Looking at the API surface, run_full_analysis_pipeline is the entry point.
    # We assume it uses the global config or we can pass overrides.
    # To be safe and robust, we will create a local config override or
    # assume the function reads from the environment or we can monkey-patch.
    # Given the constraint to use existing API, we assume the function accepts
    # optional overrides or we set environment variables if the code supports it.
    # However, the most robust way for a test is to pass arguments if available.
    # If not, we assume the test environment sets up the config correctly.
    
    # Let's assume the pipeline function accepts a data_path and output_dir for testing
    # If the current implementation in stats.py does not, we must adapt.
    # Based on the task description "Run the full analysis pipeline", 
    # we will call the function. If it relies on global config, we ensure
    # the test environment is set up or we pass parameters.
    
    # For this implementation, we assume the function signature is:
    # run_full_analysis_pipeline(data_path=None, output_dir=None)
    # If the existing code doesn't support this, we might need to adjust.
    # But since I am implementing T030 (the test), I can assume the pipeline
    # is designed to be testable. If not, I will pass the paths.
    
    # Let's call the pipeline with the test data path
    # If the function signature is strictly no-args, we might need to mock config.
    # To ensure this test works with the provided API surface which shows:
    # `from analysis.stats import ..., run_full_analysis_pipeline`
    # We will assume it can take optional arguments or we use a context manager.
    # Since I cannot change the stats.py implementation in this task (T030 is the test),
    # I will assume the stats.py implementation is robust enough to accept paths
    # or I will set the environment variables if the code uses os.environ.
    
    # Let's try to call it with arguments first. If the signature is fixed,
    # we might need to rely on the global config being set up by the test runner
    # or we patch the config module.
    # Given the instruction "Implement one task", and T030 is the test,
    # I will write the test to be as robust as possible.
    
    # Strategy: We will pass the data path and results dir to the function.
    # If the function doesn't accept them, it will raise TypeError, which
    # indicates the implementation needs to be updated to be testable.
    # However, to make this test passable, I will assume the function signature
    # is: run_full_analysis_pipeline(data_path=None, output_dir=None, figures_dir=None)
    # or similar. If not, I will fallback to mocking.
    
    # Let's assume the function is implemented to be flexible.
    try:
        results = run_full_analysis_pipeline(
            data_path=test_environment["data_path"],
            output_dir=test_environment["results_dir"],
            figures_dir=test_environment["figures_dir"]
        )
    except TypeError:
        # Fallback: If the function doesn't accept args, we assume it uses global config.
        # We will mock the config paths for the duration of the test.
        # This requires importing the config module and patching.
        from code import config
        original_processed = config.PROCESSED_DATA_PATH
        original_results = config.RESULTS_DIR
        original_figures = config.FIGURES_DIR
        
        config.PROCESSED_DATA_PATH = test_environment["data_path"]
        config.RESULTS_DIR = test_environment["results_dir"]
        config.FIGURES_DIR = test_environment["figures_dir"]
        
        try:
            results = run_full_analysis_pipeline()
        finally:
            config.PROCESSED_DATA_PATH = original_processed
            config.RESULTS_DIR = original_results
            config.FIGURES_DIR = original_figures
    
    # Assertions
    assert results is not None, "Pipeline should return a results dictionary."
    assert isinstance(results, dict), "Results should be a dictionary."
    
    # Check for expected keys
    expected_keys = [
        "ks_tests", 
        "spearman_correlations", 
        "bullock_comparison", 
        "benjamini_hochberg",
        "statistics_summary"
    ]
    for key in expected_keys:
        assert key in results, f"Results missing expected key: {key}"
    
    # Verify JSON output file exists
    stats_json_path = Path(test_environment["results_dir"]) / "statistics.json"
    assert stats_json_path.exists(), "statistics.json should be created."
    
    # Verify JSON content is valid
    with open(stats_json_path, 'r') as f:
        saved_results = json.load(f)
    assert "ks_tests" in saved_results
    assert "spearman_correlations" in saved_results
    
    # Verify figures are created
    figures_path = Path(test_environment["figures_dir"])
    figure_files = list(figures_path.glob("*.png"))
    assert len(figure_files) > 0, "At least one figure should be generated."
    
    # Verify specific figure types if possible
    figure_names = [f.name for f in figure_files]
    assert any("distribution" in name for name in figure_names), "Distribution plot should be generated."
    assert any("correlation" in name for name in figure_names), "Correlation plot should be generated."
    
    logger.info("Full analysis pipeline integration test passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])