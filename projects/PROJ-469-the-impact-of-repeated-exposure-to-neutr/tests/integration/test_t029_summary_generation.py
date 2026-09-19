"""
Integration test for T029: Summary Table Generation.

This test verifies that the summary aggregation pipeline can:
1. Read existing model results and diagnostics
2. Generate consolidated CSV summary tables
3. Write outputs to the correct locations
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from aggregate_summary import run_summary_aggregation_pipeline


@pytest.fixture
def mock_results_dir(tmp_path):
    """Create a temporary directory with mock result files."""
    # Create mock primary model results
    primary_df = pd.DataFrame({
        "term": ["news_exposure_z", "political_ideology", "news_exposure_z:political_ideology"],
        "coef": [0.45, -0.32, 0.18],
        "std err": [0.12, 0.15, 0.09],
        "t": [3.75, -2.13, 2.00],
        "P>|t|": [0.0002, 0.033, 0.046],
        "r_squared": [0.15],
        "adj_r_squared": [0.14],
        "aic": [1234.5],
        "bic": [1250.2]
    })
    (tmp_path / "primary_model.csv").to_csv(primary_df, index=False)
    
    # Create mock binary model results
    binary_df = pd.DataFrame({
        "term": ["news_exposure_z", "ideology_binary", "news_exposure_z:ideology_binary"],
        "coef": [0.42, -0.28, 0.15],
        "std err": [0.13, 0.14, 0.10],
        "t": [3.23, -2.00, 1.50],
        "P>|t|": [0.001, 0.046, 0.134],
        "r_squared": [0.12],
        "adj_r_squared": [0.11],
        "aic": [1245.3],
        "bic": [1261.0]
    })
    (tmp_path / "binary_model.csv").to_csv(binary_df, index=False)
    
    # Create mock covariate model results
    covariate_df = pd.DataFrame({
        "term": ["news_exposure_z", "political_ideology", "news_exposure_z:political_ideology", "age", "gender", "education"],
        "coef": [0.38, -0.25, 0.12, 0.01, 0.05, -0.03],
        "std err": [0.14, 0.16, 0.11, 0.02, 0.08, 0.04],
        "t": [2.71, -1.56, 1.09, 0.50, 0.62, -0.75],
        "P>|t|": [0.007, 0.119, 0.276, 0.617, 0.535, 0.453],
        "r_squared": [0.18],
        "adj_r_squared": [0.17],
        "aic": [1220.1],
        "bic": [1245.8]
    })
    (tmp_path / "covariate_model.csv").to_csv(covariate_df, index=False)
    
    # Create mock diagnostics
    diag_df = pd.DataFrame({
        "metric": ["missing_rate_IAT", "missing_rate_ideology", "missing_rate_news", "mice_iterations", "mice_chains"],
        "value": [0.05, 0.08, 0.03, 5, 20]
    })
    (tmp_path / "diagnostics.csv").to_csv(diag_df, index=False)
    
    # Create mock power design results
    power_design_df = pd.DataFrame({
        "required_n": [250],
        "met_target": [True],
        "effect_size": [0.25],
        "power": [0.80]
    })
    (tmp_path / "power_design.csv").to_csv(power_design_df, index=False)
    
    # Create mock retrospective power analysis
    power_analysis_df = pd.DataFrame({
        "observed_power": [0.85],
        "required_n": [250],
        "effect_size": [0.28],
        "met_target": [True]
    })
    (tmp_path / "power_analysis.csv").to_csv(power_analysis_df, index=False)
    
    return tmp_path


def test_summary_generation_integration(mock_results_dir, tmp_path):
    """Test the full summary generation pipeline with mock data."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    with patch('aggregate_summary.get_results_path', return_value=mock_results_dir):
        output_files = run_summary_aggregation_pipeline(mock_results_dir)
    
    # Verify both output files were created
    assert "model_summary.csv" in output_files
    assert "diagnostics.csv" in output_files
    
    model_summary_path = output_files["model_summary.csv"]
    diagnostics_path = output_files["diagnostics.csv"]
    
    assert model_summary_path.exists(), "model_summary.csv was not created"
    assert diagnostics_path.exists(), "diagnostics.csv was not created"
    
    # Load and verify model_summary.csv
    model_summary = pd.read_csv(model_summary_path)
    assert not model_summary.empty, "model_summary.csv is empty"
    
    # Should have entries from all three model types
    model_types = set(model_summary["model_type"])
    assert "primary" in model_types, "Primary model results missing"
    assert "binary" in model_types, "Binary model results missing"
    assert "covariate_adjusted" in model_types, "Covariate model results missing"
    
    # Verify key columns exist
    required_cols = ["model_type", "source_file", "coef", "P>|t|"]
    for col in required_cols:
        assert col in model_summary.columns, f"Missing column: {col}"
    
    # Load and verify diagnostics.csv
    diagnostics = pd.read_csv(diagnostics_path)
    assert not diagnostics.empty, "diagnostics.csv is empty"
    
    # Should have entries from multiple diagnostic files
    source_files = set(diagnostics["source_file"])
    assert "diagnostics.csv" in source_files, "Imputation diagnostics missing"
    assert "power_design.csv" in source_files, "Power design results missing"
    assert "power_analysis.csv" in source_files, "Power analysis results missing"
    
    # Verify the content is reasonable
    assert len(model_summary) > 0, "No model summary records"
    assert len(diagnostics) > 0, "No diagnostic records"

def test_summary_generation_with_partial_data(mock_results_dir, tmp_path):
    """Test summary generation when some result files are missing."""
    # Remove some files
    (mock_results_dir / "binary_model.csv").unlink()
    (mock_results_dir / "power_design.csv").unlink()
    
    output_dir = tmp_path / "output_partial"
    output_dir.mkdir()
    
    with patch('aggregate_summary.get_results_path', return_value=mock_results_dir):
        output_files = run_summary_aggregation_pipeline(mock_results_dir)
    
    # Should still generate files, but with less content
    assert "model_summary.csv" in output_files
    assert "diagnostics.csv" in output_files
    
    model_summary = pd.read_csv(output_files["model_summary.csv"])
    diagnostics = pd.read_csv(output_files["diagnostics.csv"])
    
    # Binary model should be missing
    assert "binary" not in set(model_summary["model_type"]), "Binary model should not be present"
    
    # Power design should be missing from diagnostics
    source_files = set(diagnostics["source_file"])
    assert "power_design.csv" not in source_files, "Power design should not be present"