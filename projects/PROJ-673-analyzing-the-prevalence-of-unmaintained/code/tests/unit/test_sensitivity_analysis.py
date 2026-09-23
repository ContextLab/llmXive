"""
Unit tests for sensitivity analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.sensitivity import (
    calculate_unmaintained_ratio,
    run_threshold_sweep,
    run_sensitivity_analysis,
    load_dependencies_data
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'name': ['pkg1', 'pkg2', 'pkg3', 'pkg4', 'pkg5'],
        'age_in_days': [30, 90, 180, 365, 730],
        'vulnerability_count': [0, 1, 2, 5, 10]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_unmaintained_ratio_low_threshold(sample_dataframe):
    """Test unmaintained ratio calculation with a low threshold."""
    # Threshold of 30 days: pkg2, pkg3, pkg4, pkg5 are unmaintained (4/5 = 0.8)
    ratio = calculate_unmaintained_ratio(sample_dataframe, 30)
    assert abs(ratio - 0.8) < 0.001

def test_calculate_unmaintained_ratio_high_threshold(sample_dataframe):
    """Test unmaintained ratio calculation with a high threshold."""
    # Threshold of 730 days: only pkg5 is unmaintained (1/5 = 0.2)
    ratio = calculate_unmaintained_ratio(sample_dataframe, 730)
    assert abs(ratio - 0.2) < 0.001

def test_calculate_unmaintained_ratio_empty_dataframe():
    """Test unmaintained ratio calculation with empty DataFrame."""
    df = pd.DataFrame(columns=['age_in_days', 'vulnerability_count'])
    ratio = calculate_unmaintained_ratio(df, 90)
    assert ratio == 0.0

def test_run_threshold_sweep(sample_dataframe):
    """Test threshold sweep produces expected structure."""
    thresholds = [30, 90, 180]
    results = run_threshold_sweep(sample_dataframe, thresholds)
    
    assert len(results) == 3
    for result in results:
        assert 'threshold_days' in result
        assert 'unmaintained_ratio' in result
        assert 'correlation_coefficient' in result
        assert 'p_value' in result
        assert 'sample_size' in result
        assert result['sample_size'] == 5

def test_run_sensitivity_analysis_creates_file(temp_csv_file):
    """Test that sensitivity analysis creates output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_sensitivity.json"
        
        result = run_sensitivity_analysis(
            input_path=temp_csv_file,
            output_path=str(output_path),
            thresholds=[30, 90]
        )
        
        assert output_path.exists()
        assert 'threshold_sweep' in result
        assert 'analysis_metadata' in result
        
        # Verify JSON content
        with open(output_path) as f:
            data = json.load(f)
            assert len(data['threshold_sweep']) == 2

def test_run_sensitivity_analysis_missing_input():
    """Test that sensitivity analysis fails loudly on missing input."""
    with pytest.raises(FileNotFoundError):
        run_sensitivity_analysis(input_path="nonexistent_file.csv")

def test_run_threshold_sweep_with_null_values():
    """Test handling of null values in data."""
    data = {
        'age_in_days': [30, np.nan, 180, 365],
        'vulnerability_count': [0, 1, 2, 5]
    }
    df = pd.DataFrame(data)
    # Should filter out the NaN row
    results = run_threshold_sweep(df, [90])
    assert len(results) == 1
    assert results[0]['sample_size'] == 3  # Only 3 valid rows