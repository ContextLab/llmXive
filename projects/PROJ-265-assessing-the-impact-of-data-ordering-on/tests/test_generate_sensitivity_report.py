import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from generate_sensitivity_report import load_metrics_csv, aggregate_by_n, generate_plots, generate_markdown_report

@pytest.fixture
def sample_csv_data():
    """Create a temporary CSV file with sample data for testing."""
    data = {
        'phi': [0.5, 0.5, 0.8, 0.8],
        'n': [50, 100, 50, 100],
        'ordered_cov': [0.90, 0.92, 0.85, 0.88],
        'shuffled_cov': [0.94, 0.95, 0.94, 0.95],
        'diff': [-0.04, -0.03, -0.09, -0.07],
        'p_value': [0.01, 0.02, 0.001, 0.005]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_csv_file(sample_csv_data):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_csv_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_metrics_csv(temp_csv_file):
    df = load_metrics_csv(temp_csv_file)
    assert isinstance(df, pd.DataFrame)
    assert 'n' in df.columns
    assert 'ordered_cov' in df.columns
    assert len(df) == 4

def test_load_metrics_csv_missing_file():
    with pytest.raises(FileNotFoundError):
        load_metrics_csv("non_existent_file.csv")

def test_aggregate_by_n(sample_csv_data):
    agg_df = aggregate_by_n(sample_csv_data)
    assert isinstance(agg_df, pd.DataFrame)
    assert 'n' in agg_df.columns
    assert 'ordered_cov_mean' in agg_df.columns
    # We have two unique N values (50, 100)
    assert len(agg_df) == 2
    # Check that mean calculation is roughly correct for N=50
    # Ordered cov for N=50: 0.90, 0.85 -> mean 0.875
    row_50 = agg_df[agg_df['n'] == 50].iloc[0]
    assert abs(row_50['ordered_cov_mean'] - 0.875) < 0.001

def test_aggregate_by_n_empty_df():
    empty_df = pd.DataFrame(columns=['n', 'ordered_cov'])
    with pytest.raises(ValueError):
        aggregate_by_n(empty_df)

def test_generate_plots_and_report(tmp_path, sample_csv_data):
    # Create a temporary CSV
    temp_csv = tmp_path / "test_metrics.csv"
    sample_csv_data.to_csv(temp_csv, index=False)
    
    # Load and aggregate
    df = load_metrics_csv(str(temp_csv))
    agg_df = aggregate_by_n(df)
    
    # Generate plots
    output_dir = str(tmp_path)
    plot_paths = generate_plots(agg_df, output_dir)
    
    assert len(plot_paths) == 2
    for p in plot_paths:
        assert os.path.exists(p)
        assert os.path.getsize(p) > 0
    
    # Generate report
    report_path = tmp_path / "test_report.md"
    generate_markdown_report(agg_df, plot_paths, str(report_path))
    
    assert os.path.exists(report_path)
    with open(report_path, 'r') as f:
        content = f.read()
    
    assert "Sensitivity Analysis Report" in content
    assert "Sensitivity by N" in content
    assert "Sample Size (N)" in content
    assert "Ordered Coverage" in content
    assert "sensitivity_coverage_by_n.png" in content
    assert "sensitivity_coverage_gap_by_n.png" in content