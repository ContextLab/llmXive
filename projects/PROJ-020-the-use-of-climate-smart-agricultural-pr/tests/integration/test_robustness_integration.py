"""
Integration test for the full robustness pipeline (T035).
Verifies end-to-end execution and output file generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.robustness import run_robustness_pipeline

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with mock processed data."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir)
    
    # Create mock data
    np.random.seed(42)
    n = 1000
    data = pd.DataFrame({
        "region": np.random.choice(["North", "South", "East", "West", "Central"], n),
        "country": np.random.choice(["KE", "IN", "VN"], n),
        "food_security_index": np.random.normal(50, 10, n),
        "csa_index": np.random.normal(0.5, 0.2, n),
        "digital_access": np.random.binomial(1, 0.4, n),
        "finance_access": np.random.binomial(1, 0.3, n),
        "age": np.random.normal(45, 12, n),
        "education_years": np.random.normal(8, 3, n),
        "household_size": np.random.normal(4, 2, n),
        "plot_size": np.random.exponential(2, n)
    })
    
    # Save to parquet
    processed_dir = data_dir / "processed"
    processed_dir.mkdir()
    output_file = processed_dir / "merged_sample.parquet"
    data.to_parquet(output_file)
    
    yield data_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_full_pipeline_execution(temp_data_dir):
    """Test the full robustness pipeline execution."""
    output_dir = temp_data_dir / "state" / "robustness"
    
    # Run pipeline
    result_path = run_robustness_pipeline(
        data_path=temp_data_dir / "processed" / "merged_sample.parquet",
        formula="food_security_index ~ csa_index + digital_access",
        n_loro_folds=3, # Limit for speed
        n_bootstrap=20, # Small number for test speed
        output_dir=output_dir
    )
    
    # Verify output file exists
    assert result_path.exists(), f"Output file {result_path} was not created"
    
    # Verify content structure
    with open(result_path, 'r') as f:
        results = json.load(f)
    
    assert "loro" in results
    assert "bootstrap" in results
    
    # Verify LORO results
    loro = results["loro"]
    assert "full_model" in loro
    assert "loro_results" in loro
    assert len(loro["loro_results"]) > 0
    
    # Verify Bootstrap results
    bootstrap = results["bootstrap"]
    assert "summary" in bootstrap
    assert "distributions" in bootstrap
    assert bootstrap["n_iterations_requested"] == 20
    
    # Check that at least one coefficient has valid stats
    assert len(bootstrap["summary"]) > 0
    for key, val in bootstrap["summary"].items():
        if val["n_success"] > 0:
            assert not np.isnan(val["mean"])
            break