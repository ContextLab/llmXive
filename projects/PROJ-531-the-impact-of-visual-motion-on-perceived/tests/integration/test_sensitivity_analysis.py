"""
Integration test for T023 Sensitivity Analysis.

Verifies that the sensitivity analysis script runs end-to-end,
produces the correct output file, and the CSV contains the expected columns.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path
import numpy as np
import statsmodels.api as sm

# Ensure the code directory is in the path if running from tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modeling.sensitivity_analysis import run_sensitivity_analysis, main

@pytest.fixture
def setup_test_environment(tmp_path):
    """Create a mock project structure with dummy data and metrics."""
    # Create directories
    data_dir = tmp_path / "data" / "processed"
    results_dir = tmp_path / "data" / "results"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy cleaned_data.csv
    n = 150
    np.random.seed(42)
    df = pd.DataFrame({
        'latency': np.random.normal(0, 1, n),
        'smoothness': np.random.normal(0, 1, n),
        'lead_time': np.random.normal(0, 1, n),
        'agency_score': np.random.normal(0, 1, n)
    })
    # Inject some correlation to make regression meaningful
    df['agency_score'] = 0.5 * df['latency'] + 0.3 * df['smoothness'] + np.random.normal(0, 0.1, n)
    
    csv_path = data_dir / "cleaned_data.csv"
    df.to_csv(csv_path, index=False)
    
    # Create dummy model_metrics.json
    metrics = {
        "ols": {
            "features": ["latency", "smoothness", "lead_time"],
            "coefficients": {"latency": 0.5, "smoothness": 0.3, "lead_time": 0.1},
            "p_values": {"latency": 0.01, "smoothness": 0.03, "lead_time": 0.4}
        }
    }
    metrics_path = results_dir / "model_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f)
    
    return tmp_path

def test_sensitivity_analysis_output_structure(setup_test_environment):
    """Test that the output CSV has the correct columns and rows."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(str(setup_test_environment))
        
        # Run the analysis
        df = run_sensitivity_analysis()
        
        # Assertions
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3  # 3 thresholds
        
        required_cols = {"threshold", "significance_rate", "p_value_variance"}
        assert set(df.columns) == required_cols
        
        # Check threshold values
        assert list(df['threshold']) == [0.01, 0.05, 0.1]
        
        # Check rates are between 0 and 1
        assert all(0 <= x <= 1 for x in df['significance_rate'])
        
        # Check variances are non-negative
        assert all(x >= 0 for x in df['p_value_variance'])
        
    finally:
        os.chdir(original_cwd)

def test_sensitivity_analysis_file_creation(setup_test_environment):
    """Test that the script actually writes the file to disk."""
    original_cwd = os.getcwd()
    try:
        os.chdir(str(setup_test_environment))
        
        main()
        
        output_path = Path("data/results/sensitivity_analysis.csv")
        assert output_path.exists(), "Output file was not created"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert 'threshold' in df.columns
        
    finally:
        os.chdir(original_cwd)