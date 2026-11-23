import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from generate_stability_report import (
    load_results_metrics,
    generate_stability_report,
    save_report,
    main
)
from logging_config import setup_logger

# Mock data for testing
MOCK_RESULTS_DATA = {
    'metric_name': ['main_analysis'],
    'effect_size': [0.45],
    'p_value': [0.001],
    'significance_stability': [0.95],
    'significance_flip_rate': [0.05]
}

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory structure with mock data."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create mock results_metrics.csv
    results_file = data_dir / "results_metrics.csv"
    df = pd.DataFrame(MOCK_RESULTS_DATA)
    df.to_csv(results_file, index=False)
    
    return tmp_path

@pytest.fixture
def setup_paths(monkeypatch, mock_data_dir):
    """Monkeypatch the paths in the module to use the temp directory."""
    # We need to patch the module-level variables in generate_stability_report
    import generate_stability_report as mod
    monkeypatch.setattr(mod, "PROJECT_ROOT", mock_data_dir)
    monkeypatch.setattr(mod, "DATA_PROCESSED_DIR", mock_data_dir / "data" / "processed")
    return mock_data_dir

def test_generate_stability_report(setup_paths):
    """Test that the stability report is generated correctly."""
    # Load mock data
    results_df = load_results_metrics()
    
    # Generate report
    report_df = generate_stability_report(results_df)
    
    # Verify structure
    assert 'metric' in report_df.columns
    assert 'value' in report_df.columns
    assert 'description' in report_df.columns
    
    # Verify content
    assert len(report_df) == 4  # 4 metrics expected
    
    # Check specific values
    stability_val = report_df[report_df['metric'] == 'Significance Stability']['value'].iloc[0]
    assert stability_val == 0.95
    
    flip_val = report_df[report_df['metric'] == 'Significance Flip Rate']['value'].iloc[0]
    assert flip_val == 0.05

def test_save_report(setup_paths, tmp_path):
    """Test that the report is saved correctly."""
    results_df = load_results_metrics()
    report_df = generate_stability_report(results_df)
    
    # Save to a temp location within the temp dir
    output_path = setup_paths / "data" / "processed" / "significance_stability_report.csv"
    report_df.to_csv(output_path, index=False)
    
    # Verify file exists and content matches
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(report_df, saved_df)

def test_missing_columns(setup_paths, monkeypatch):
    """Test that an error is raised if required columns are missing."""
    # Create a mock dataframe without required columns
    bad_data = {
        'metric_name': ['test'],
        'effect_size': [0.5]
    }
    bad_df = pd.DataFrame(bad_data)
    
    # Mock the load function to return bad data
    def mock_load():
        return bad_df
    
    monkeypatch.setattr('generate_stability_report.load_results_metrics', mock_load)
    
    with pytest.raises(KeyError):
        generate_stability_report(bad_df)

def test_empty_results(setup_paths, monkeypatch):
    """Test that an error is raised if results dataframe is empty."""
    empty_df = pd.DataFrame()
    
    with pytest.raises(ValueError):
        generate_stability_report(empty_df)