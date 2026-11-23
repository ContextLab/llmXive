"""
Integration tests for the Report Generation module (T029).
Verifies that plots are generated correctly from mock data.
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import module under test
from code.utils.config import get_path, ensure_directories
from code import _05_report_generation as report_gen

@pytest.fixture
def mock_metrics_data(tmp_path):
    """Create a temporary metrics file with mock data."""
    # Setup temporary directory structure
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock metrics records
    records = [
        {
            "year": 2010, "ece_5": 0.05, "ece_10": 0.04, "ece_20": 0.03, 
            "brier": 0.15, "pca_shift": 0.2, "key_feature_shift": 0.1
        },
        {
            "year": 2015, "ece_5": 0.08, "ece_10": 0.07, "ece_20": 0.06, 
            "brier": 0.18, "pca_shift": 0.35, "key_feature_shift": 0.25
        },
        {
            "year": 2020, "ece_5": 0.12, "ece_10": 0.11, "ece_20": 0.10, 
            "brier": 0.22, "pca_shift": 0.5, "key_feature_shift": 0.4
        }
    ]
    
    metrics_file = data_dir / "metrics_records.json"
    with open(metrics_file, 'w') as f:
        json.dump(records, f)
    
    return records

@pytest.fixture
def mock_regression_results(tmp_path):
    """Create a temporary regression results file."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "slope": 0.002,
        "intercept": 0.05,
        "p_value": 0.03,
        "r_squared": 0.85
    }
    
    results_file = data_dir / "regression_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    return results

def test_plot_generation_creates_files(tmp_path, mock_metrics_data, mock_regression_results):
    """
    Test that the report generation script creates the expected figure files.
    """
    # We need to monkeypatch the get_path function to use our tmp_path
    # Since get_path relies on _PROJECT_ROOT, we'll simulate the environment
    
    original_root = report_gen._PROJECT_ROOT
    
    # Create a fake project structure in tmp_path
    fake_root = tmp_path / "fake_project"
    fake_root.mkdir()
    
    # Create necessary subdirectories
    (fake_root / "data" / "processed").mkdir(parents=True)
    (fake_root / "figures").mkdir(parents=True)
    
    # Move the mock files to the fake root
    import shutil
    shutil.copy(tmp_path / "data" / "processed" / "metrics_records.json", 
                fake_root / "data" / "processed" / "metrics_records.json")
    shutil.copy(tmp_path / "data" / "processed" / "regression_results.json", 
                fake_root / "data" / "processed" / "regression_results.json")
    
    # Patch the module's root
    report_gen._PROJECT_ROOT = fake_root
    report_gen.get_path = lambda key: fake_root / key.replace(".", "/")
    
    try:
        # Run the generation
        records = mock_metrics_data
        regression_results = mock_regression_results
        
        ece_path, brier_path = report_gen.generate_time_series_plots(records, regression_results)
        
        # Assertions
        assert ece_path.exists(), f"ECE plot not created at {ece_path}"
        assert brier_path.exists(), f"Brier plot not created at {brier_path}"
        
        # Check file size (should be non-empty)
        assert ece_path.stat().st_size > 0, "ECE plot is empty"
        assert brier_path.stat().st_size > 0, "Brier plot is empty"
        
        # Check file extensions
        assert str(ece_path).endswith('.png'), "ECE plot is not a PNG"
        assert str(brier_path).endswith('.png'), "Brier plot is not a PNG"
        
    finally:
        # Restore original
        report_gen._PROJECT_ROOT = original_root
        # Reload config logic if needed, but simple patching is sufficient for this test

def test_empty_dataframe_handling(tmp_path):
    """
    Test that the plotting functions handle empty data gracefully.
    """
    # Patch root
    fake_root = tmp_path / "fake_project_empty"
    fake_root.mkdir()
    (fake_root / "figures").mkdir()
    
    original_root = report_gen._PROJECT_ROOT
    report_gen._PROJECT_ROOT = fake_root
    report_gen.get_path = lambda key: fake_root / key.replace(".", "/")
    
    try:
        df = report_gen.prepare_time_series_data([])
        assert df.empty, "DataFrame should be empty"
        
        # Try to plot (should not crash, just log error)
        ece_path = fake_root / "figures" / "test_ece.png"
        report_gen.plot_time_series_ece(df, ece_path)
        
        # File should not be created or should be empty/invalid
        # In our implementation, we return early if empty, so file might not exist
        # or exist but be empty. Let's check the log or behavior.
        # The implementation returns early, so no file is saved.
        assert not ece_path.exists() or ece_path.stat().st_size == 0
        
    finally:
        report_gen._PROJECT_ROOT = original_root
