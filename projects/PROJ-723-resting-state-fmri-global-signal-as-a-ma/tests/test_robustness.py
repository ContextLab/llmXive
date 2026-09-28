import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from robustness import run_alpha_sweep, run_variance_metric_analysis, run_partial_correlation_analysis
from utils import write_csv

@pytest.fixture
def sample_cleaned_data(tmp_path):
    """Create a temporary cleaned_data.csv for testing."""
    data = {
        'Subject_ID': [f'sub-{i}' for i in range(1, 51)],
        'Global_Signal_SD': np.random.normal(0.5, 0.1, 50),
        'MWQ_Score': np.random.normal(30, 5, 50),
        'FD': np.random.uniform(0.1, 0.4, 50),
        'DVARS': np.random.uniform(0.1, 0.5, 50),
        'Age': np.random.randint(18, 65, 50),
        'Sex': np.random.choice(['M', 'F'], 50)
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "cleaned_data.csv"
    write_csv(csv_path, df)
    return csv_path

def test_alpha_sweep_returns_results(sample_cleaned_data, tmp_path):
    """Verify alpha sweep produces a list of results with expected keys."""
    # Mock the load function behavior by passing the dataframe directly
    df = pd.read_csv(sample_cleaned_data)
    
    # Patch the load function in the module if needed, but here we test the core logic
    # by calling the function that does the work.
    result = run_alpha_sweep(df)
    
    assert isinstance(result, dict)
    assert "results" in result
    assert len(result["results"]) > 0
    
    for item in result["results"]:
        assert "alpha" in item
        assert "mean_mae" in item
        assert "std_mae" in item
        assert "mean_r2" in item
        # MAE should be positive
        assert item["mean_mae"] > 0

def test_variance_metric_analysis_returns_mae(sample_cleaned_data):
    """Verify variance metric analysis returns an MAE."""
    df = pd.read_csv(sample_cleaned_data)
    result = run_variance_metric_analysis(df)
    
    assert isinstance(result, dict)
    assert "mean_mae" in result
    assert result["mean_mae"] > 0
    assert result["metric"] == "Global_Signal_Variance"

def test_partial_correlation_analysis_returns_stats(sample_cleaned_data):
    """Verify partial correlation returns r and p-value."""
    df = pd.read_csv(sample_cleaned_data)
    result = run_partial_correlation_analysis(df)
    
    assert isinstance(result, dict)
    assert "partial_correlation_r" in result
    assert "p_value" in result
    assert "controlled_for" in result
    assert result["controlled_for"] == "Mean_FD"
    
    # Correlation should be between -1 and 1
    assert -1.0 <= result["partial_correlation_r"] <= 1.0
    assert 0.0 <= result["p_value"] <= 1.0

def test_robustness_script_execution(tmp_path, monkeypatch):
    """Test that the main script runs and produces the output file."""
    # Setup temporary paths
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    results_dir = tmp_path / "data" / "results"
    results_dir.mkdir(parents=True)
    
    # Create dummy cleaned data
    csv_path = data_dir / "cleaned_data.csv"
    data = {
        'Subject_ID': [f'sub-{i}' for i in range(1, 21)],
        'Global_Signal_SD': np.random.normal(0.5, 0.1, 20),
        'MWQ_Score': np.random.normal(30, 5, 20),
        'FD': np.random.uniform(0.1, 0.4, 20),
        'DVARS': np.random.uniform(0.1, 0.5, 20),
        'Age': np.random.randint(18, 65, 20),
        'Sex': np.random.choice(['M', 'F'], 20)
    }
    df = pd.DataFrame(data)
    write_csv(csv_path, df)
    
    # Change CWD to tmp_path to simulate project root
    monkeypatch.chdir(tmp_path)
    
    # Import and run main
    from robustness import main
    exit_code = main()
    
    assert exit_code == 0
    
    output_file = Path("data/results/robustness_report.json")
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    assert "alpha_sweep" in report
    assert "variance_metric_analysis" in report
    assert "partial_correlation_analysis" in report