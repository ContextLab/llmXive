import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from generate_sensitivity_summary import (
    load_sensitivity_data,
    compute_summary_stats,
    generate_summary_text,
    write_summary
)

@pytest.fixture
def sample_sensitivity_data():
    """Create a temporary CSV file with sample sensitivity data."""
    data = {
        'chi2_threshold': [1.0, 1.5, 2.0, 2.5, 3.0],
        'mond_pass_count': [50, 60, 70, 75, 80],
        'nfw_pass_count': [40, 50, 60, 65, 70],
        'total_galaxies': [100, 100, 100, 100, 100],
        'mond_pass_rate': [0.50, 0.60, 0.70, 0.75, 0.80],
        'nfw_pass_rate': [0.40, 0.50, 0.60, 0.65, 0.70]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(sample_sensitivity_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_sensitivity_data.to_csv(f, index=False)
        yield Path(f.name)
    os.unlink(f.name)

def test_load_sensitivity_data_valid_file(temp_csv_path, sample_sensitivity_data):
    """Test loading a valid sensitivity data file."""
    df = load_sensitivity_data(temp_csv_path)
    pd.testing.assert_frame_equal(df, sample_sensitivity_data)

def test_load_sensitivity_data_missing_file():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_data(Path("/nonexistent/path/file.csv"))

def test_load_sensitivity_data_missing_columns(temp_csv_path):
    """Test loading a file with missing required columns raises ValueError."""
    # Create a file with missing columns
    data = {'chi2_threshold': [1.0], 'mond_pass_count': [50]}
    with open(temp_csv_path, 'w') as f:
        pd.DataFrame(data).to_csv(f, index=False)
    
    with pytest.raises(ValueError):
        load_sensitivity_data(temp_csv_path)

def test_compute_summary_stats(sample_sensitivity_data):
    """Test computing summary statistics."""
    stats = compute_summary_stats(sample_sensitivity_data)
    
    assert 'optimal_threshold' in stats
    assert 'mond_pass_rate_at_optimal' in stats
    assert 'nfw_pass_rate_at_optimal' in stats
    assert 'max_abs_diff' in stats
    assert 'avg_mond_pass_rate' in stats
    assert 'avg_nfw_pass_rate' in stats
    assert 'mond_favored_count' in stats
    assert 'nfw_favored_count' in stats
    assert 'total_thresholds' in stats

    # Verify specific values based on sample data
    # In sample data, MOND pass rate is always higher than NFW
    assert stats['mond_favored_count'] == 5
    assert stats['nfw_favored_count'] == 0
    assert stats['total_thresholds'] == 5
    assert stats['avg_mond_pass_rate'] == 0.67  # (0.5+0.6+0.7+0.75+0.8)/5

def test_compute_summary_stats_empty_dataframe():
    """Test computing stats on an empty dataframe."""
    empty_df = pd.DataFrame(columns=['chi2_threshold', 'mond_pass_count', 'nfw_pass_count', 
                                     'total_galaxies', 'mond_pass_rate', 'nfw_pass_rate'])
    stats = compute_summary_stats(empty_df)
    
    assert stats['optimal_threshold'] is None
    assert stats['mond_favored_count'] == 0
    assert stats['nfw_favored_count'] == 0

def test_generate_summary_text(sample_sensitivity_data):
    """Test generating summary text."""
    stats = compute_summary_stats(sample_sensitivity_data)
    summary = generate_summary_text(stats, 100)
    
    assert "SENSITIVITY ANALYSIS SUMMARY" in summary
    assert "Total Galaxies Analyzed: 100" in summary
    assert "MOND" in summary
    assert "NFW" in summary
    assert "CONCLUSION" in summary

def test_write_summary(temp_csv_path, sample_sensitivity_data):
    """Test writing summary to a file."""
    stats = compute_summary_stats(sample_sensitivity_data)
    summary_text = generate_summary_text(stats, 100)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_summary.txt"
        write_summary(summary_text, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert "SENSITIVITY ANALYSIS SUMMARY" in content
        assert "Total Galaxies Analyzed: 100" in content