import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from src.analysis.sensitivity_analysis import (
    calculate_unmaintained_proportion,
    run_sensitivity_analysis,
    load_dependencies_data
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'package_name': ['pkg1', 'pkg2', 'pkg3', 'pkg4', 'pkg5'],
        'age_in_days': [100, 200, 300, 50, None],
        'vulnerability_count': [1, 0, 2, 0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv(sample_df):
    """Create a temporary CSV file from sample_df."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_df.to_csv(f, index=False)
        return f.name

def test_calculate_unmaintained_proportion_basic(sample_df):
    """Test basic proportion calculation."""
    # Threshold 150: pkg1 (100) is maintained, pkg2 (200) unmaintained, pkg3 (300) unmaintained, pkg4 (50) maintained.
    # Valid count = 4. Unmaintained = 2. Proportion = 0.5.
    prop = calculate_unmaintained_proportion(sample_df, 150)
    assert prop == 0.5

def test_calculate_unmaintained_proportion_all_maintained(sample_df):
    """Test when all are maintained."""
    prop = calculate_unmaintained_proportion(sample_df, 350)
    assert prop == 0.0

def test_calculate_unmaintained_proportion_all_unmaintained(sample_df):
    """Test when all valid are unmaintained."""
    prop = calculate_unmaintained_proportion(sample_df, 40)
    assert prop == 1.0

def test_calculate_unmaintained_proportion_null_handling(sample_df):
    """Test that null values are excluded."""
    # With threshold 150, we have 4 valid. 2 unmaintained.
    # If we include null as unmaintained, it would be 3/5 = 0.6.
    # We expect 0.5.
    prop = calculate_unmaintained_proportion(sample_df, 150)
    assert prop == 0.5

def test_run_sensitivity_analysis(temp_csv):
    """Test the full sensitivity analysis run."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out_f:
        output_path = out_f.name

    # Use a small range for testing
    thresholds = [100, 200, 300]
    
    result = run_sensitivity_analysis(temp_csv, output_path, threshold_range=thresholds)
    
    assert 'threshold_sweep' in result
    assert len(result['threshold_sweep']) == len(thresholds)
    
    # Check structure of sweep results
    for entry in result['threshold_sweep']:
        assert 'threshold' in entry
        assert 'unmaintained_proportion' in entry
        assert 'robustness_score' in entry
        assert isinstance(entry['threshold'], int)
        assert isinstance(entry['unmaintained_proportion'], float)
    
    # Verify file was written
    assert Path(output_path).exists()
    
    # Verify content matches
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded == result

def test_run_sensitivity_analysis_file_not_found():
    """Test error handling for missing input file."""
    with pytest.raises(FileNotFoundError):
        run_sensitivity_analysis('nonexistent.csv', 'output.json')