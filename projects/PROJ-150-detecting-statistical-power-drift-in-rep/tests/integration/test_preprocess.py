"""
Integration tests for the preprocessing module (T011a).

These tests verify:
1. The script runs end-to-end without errors.
2. The output file `data/derived/cleaned_data.csv` is created.
3. The output file `data/derived/grouping_validation.json` is created.
4. Rows with missing critical columns are filtered out.
5. Power estimates are calculated correctly.
"""
import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.preprocessing import (
    load_raw_data, 
    filter_missing_rows, 
    validate_grouping_variables, 
    save_cleaned_data, 
    save_grouping_validation,
    DataFetchError
)
from code.power_calc import calculate_power_cohen_d

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_raw_data(temp_data_dir):
    """Create a sample raw data CSV with some missing values."""
    data = {
        'study_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'year': [2000, 2005, None, 2015, 2020],
        'field': ['Psychology', 'Psychology', 'Biology', 'Physics', 'Biology'],
        'original_study_id': ['O1', 'O1', 'O2', 'O3', 'O2'],
        'effect_size': [0.5, None, 0.3, 0.8, 0.2],
        'sample_size': [50, 60, 40, None, 70]
    }
    df = pd.DataFrame(data)
    csv_path = Path(temp_data_dir) / "data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def setup_directories(temp_data_dir):
    """Setup the directory structure expected by the script."""
    raw_dir = Path(temp_data_dir) / "data" / "raw"
    derived_dir = Path(temp_data_dir) / "data" / "derived"
    raw_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    return {
        "temp_root": temp_data_dir,
        "raw_path": str(raw_dir / "data.csv"),
        "derived_path": str(derived_dir)
    }

def test_filter_missing_rows():
    """Test that rows with missing critical values are filtered."""
    data = {
        'year': [2000, None, 2005, 2010],
        'effect_size': [0.5, 0.3, None, 0.8],
        'sample_size': [50, 60, 40, None],
        'other': ['A', 'B', 'C', 'D']
    }
    df = pd.DataFrame(data)
    
    filtered = filter_missing_rows(df, ['year', 'effect_size', 'sample_size'])
    
    # Only the first row should remain (all non-null)
    assert len(filtered) == 1
    assert filtered.iloc[0]['year'] == 2000

def test_validate_grouping_variables_single_level():
    """Test validation detects single-level grouping factors."""
    data = {
        'field': ['Psychology', 'Psychology', 'Psychology'],
        'original_study_id': ['O1', 'O2', 'O3'],
        'power_estimate': [0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    results = validate_grouping_variables(df)
    
    assert results['field']['status'] == 'single_level'
    assert results['field']['count'] == 1
    assert results['original_study_id']['status'] == 'valid'

def test_preprocess_end_to_end(setup_directories, sample_raw_data):
    """Test the full preprocessing pipeline end-to-end."""
    # Copy sample data to the expected raw location
    import shutil
    shutil.copy(sample_raw_data, setup_directories['raw_path'])
    
    # Change to the temp directory to simulate script execution
    original_cwd = os.getcwd()
    os.chdir(setup_directories['temp_root'])
    
    try:
        # Import and run the main logic manually (simulating script run)
        from code.preprocessing import load_raw_data, filter_missing_rows, validate_grouping_variables, save_cleaned_data, save_grouping_validation
        from code.power_calc import calculate_power_cohen_d
        
        # 1. Load
        df_raw = load_raw_data("data/raw/data.csv")
        assert len(df_raw) == 5 # Original count
        
        # 2. Filter
        df_clean = filter_missing_rows(df_raw)
        # Rows 1 (year missing), 2 (effect_size missing), 3 (sample_size missing) should be removed
        # Row 0 is valid. Row 4 is valid.
        # Wait: Row 1: year=2005, effect_size=None -> filtered.
        # Row 2: year=None -> filtered.
        # Row 3: sample_size=None -> filtered.
        # Row 4: year=2020, effect_size=0.2, sample_size=70 -> valid.
        # So we expect 2 rows.
        assert len(df_clean) == 2
        
        # 3. Power Calculation
        df_clean['power_estimate'] = df_clean.apply(
            lambda row: calculate_power_cohen_d(row['effect_size'], row['sample_size']),
            axis=1
        )
        assert 'power_estimate' in df_clean.columns
        assert not df_clean['power_estimate'].isna().any()
        
        # 4. Validate
        validation = validate_grouping_variables(df_clean)
        assert 'field' in validation
        assert 'original_study_id' in validation
        
        # 5. Save
        save_cleaned_data(df_clean, "data/derived/cleaned_data.csv")
        save_grouping_validation(validation, "data/derived/grouping_validation.json")
        
        # Verify outputs exist
        assert os.path.exists("data/derived/cleaned_data.csv")
        assert os.path.exists("data/derived/grouping_validation.json")
        
        # Verify content
        df_out = pd.read_csv("data/derived/cleaned_data.csv")
        assert len(df_out) == 2
        assert list(df_out.columns) == ['study_id', 'year', 'field', 'original_study_id', 'effect_size', 'sample_size', 'power_estimate']
        
        with open("data/derived/grouping_validation.json", 'r') as f:
            val_json = json.load(f)
            assert 'field' in val_json
            assert 'original_study_id' in val_json
            
    finally:
        os.chdir(original_cwd)

def test_data_fetch_error_on_missing_file(setup_directories):
    """Test that DataFetchError is raised if raw data is missing."""
    original_cwd = os.getcwd()
    os.chdir(setup_directories['temp_root'])
    
    try:
        with pytest.raises(DataFetchError):
            load_raw_data("data/raw/data.csv")
    finally:
        os.chdir(original_cwd)

def test_power_calculation_values():
    """Test that power calculation produces reasonable values."""
    # Cohen's d = 0.5, n = 100 -> Power should be high
    p1 = calculate_power_cohen_d(0.5, 100)
    assert 0.9 < p1 < 1.0
    
    # Cohen's d = 0.2, n = 20 -> Power should be low
    p2 = calculate_power_cohen_d(0.2, 20)
    assert 0.0 < p2 < 0.5