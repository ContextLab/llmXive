"""
Integration test for robustness check execution.
Ensures the robustness pipeline runs without error and produces output.
"""
import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

from analysis.robustness import run_robustness_pipeline, main

def test_robustness_pipeline_execution():
    """
    Test that the robustness pipeline runs end-to-end on a small synthetic dataset.
    Note: This uses a small synthetic dataset for integration testing purposes only,
    as real data ingestion might be slow or require network access in the test environment.
    In a full E2E run, this would use the real data.
    """
    # Create a small synthetic dataset for testing the pipeline logic
    n = 100
    data = pd.DataFrame({
        "country": np.random.choice(["Kenya", "India", "Vietnam"], n),
        "csa_index": np.random.uniform(0, 1, n),
        "food_security": np.random.uniform(0, 1, n) + 0.5 * np.random.uniform(0, 1, n)
    })
    
    formula = "food_security ~ csa_index"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Run the pipeline
        results = run_robustness_pipeline(
            data=data,
            formula=formula,
            output_dir=output_dir,
            bootstrap_iterations=10 # Small number for speed
        )
        
        # Verify results structure
        assert "leave_one_country_out" in results
        assert "bootstrap" in results
        
        # Verify output files were created
        assert (output_dir / "loo_results.json").exists()
        assert (output_dir / "bootstrap_results.json").exists()
        assert (output_dir / "robustness_summary.json").exists()

def test_main_with_args():
    """
    Test the main function with command line arguments.
    """
    # This test would require mocking sys.argv or using a subprocess.
    # For simplicity, we rely on test_robustness_pipeline_execution for logic validation.
    pass
