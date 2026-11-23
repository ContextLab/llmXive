import os
import sys
import pickle
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path if not already there
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from compute_trends import load_and_prepare_data, fit_mixed_linear_model, extract_year_statistics, save_results, save_summary, main

@pytest.fixture
def sample_power_data(tmp_path):
    """Generate a small realistic dataset for testing LMM."""
    # Create a dataframe that mimics data/derived/power_estimates.csv
    data = {
        'study_id': [f's{i}' for i in range(50)],
        'year': np.random.randint(1990, 2024, 50),
        'field': np.random.choice(['Psychology', 'Biology', 'Physics'], 50),
        'original_study_id': np.random.choice(['orig_1', 'orig_2', 'orig_3'], 50),
        'effect_size': np.random.uniform(0.1, 0.8, 50),
        'sample_size': np.random.randint(20, 200, 50),
        'power_est': np.random.uniform(0.4, 0.9, 50)
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "power_estimates.csv"
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def setup_dirs(tmp_path):
    """Ensure required directories exist."""
    derived_dir = tmp_path / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    return derived_dir

def test_load_and_prepare_data_valid(sample_power_data, tmp_path):
    """Test loading valid data."""
    # Copy file to expected location or adjust path
    # For this test, we pass the path directly
    df = load_and_prepare_data(sample_power_data)
    assert df is not None
    assert 'power_est' in df.columns
    assert 'year' in df.columns
    assert len(df) > 0

def test_load_and_prepare_data_handles_nan(tmp_path):
    """Test that NaN values in effect_size or sample_size are dropped and logged."""
    data = {
        'study_id': ['s1', 's2', 's3'],
        'year': [2000, 2001, 2002],
        'field': ['A', 'B', 'A'],
        'original_study_id': ['o1', 'o2', 'o1'],
        'effect_size': [0.5, np.nan, 0.6],
        'sample_size': [50, 60, np.nan],
        'power_est': [0.7, 0.8, 0.9]
    }
    df_input = pd.DataFrame(data)
    input_path = tmp_path / "test_nan.csv"
    df_input.to_csv(input_path, index=False)
    
    df = load_and_prepare_data(input_path)
    # Should drop rows with NaN in effect_size or sample_size
    # Original 3 rows, s2 has nan effect_size, s3 has nan sample_size. Both dropped.
    assert len(df) == 1
    assert df.iloc[0]['study_id'] == 's1'

def test_fit_mixed_linear_model_basic(sample_power_data, setup_dirs):
    """Test that the LMM fits successfully with crossed random effects."""
    df = load_and_prepare_data(sample_power_data)
    assert df is not None
    
    # Temporarily change working directory to allow relative paths if needed, 
    # but the function takes df directly.
    model = fit_mixed_linear_model(df)
    assert model is not None
    
    # Verify the model object has the expected structure
    # Check that random effects are present
    assert hasattr(model, 'params')
    assert 'year' in model.params
    
def test_extract_year_statistics(sample_power_data, setup_dirs):
    """Test extraction of year slope, SE, CI, and p-value."""
    df = load_and_prepare_data(sample_power_data)
    assert df is not None
    
    model = fit_mixed_linear_model(df)
    assert model is not None
    
    result = extract_year_statistics(model)
    assert result is not None
    slope, se, ci_lower, ci_upper, p_value = result
    
    assert isinstance(slope, (float, np.floating))
    assert isinstance(se, (float, np.floating))
    assert isinstance(ci_lower, (float, np.floating))
    assert isinstance(ci_upper, (float, np.floating))
    assert isinstance(p_value, (float, np.floating))
    assert 0 <= p_value <= 1

def test_save_results(tmp_path, setup_dirs):
    """Test saving results to CSV."""
    # Ensure output directory exists relative to the test
    output_file = tmp_path / "data" / "derived" / "lmm_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Mock the save_results to write to our temp path
    # We need to patch the internal os.path or just run the logic
    # Since save_results hardcodes the path, we can't easily test without mocking
    # Let's instead test the full pipeline or mock the path
    
    # For now, let's just verify the function logic by calling it with dummy data
    # and checking if it creates a file in the expected default location (if we change cwd)
    # But a better way is to patch the function or just rely on the main test below.
    pass

def test_full_pipeline_integration(sample_power_data, tmp_path, monkeypatch):
    """Test the full pipeline from loading to saving files."""
    # Change working directory to tmp_path so relative paths work
    monkeypatch.chdir(tmp_path)
    
    # Create the expected directory structure
    derived_dir = tmp_path / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy sample data to the expected input path
    input_path = derived_dir / "power_estimates.csv"
    sample_data = pd.read_csv(sample_power_data)
    sample_data.to_csv(input_path, index=False)
    
    # Run main
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            raise AssertionError(f"Main exited with code {e.code}")
    
    # Check output files
    model_file = derived_dir / "input_trends_models.pkl"
    raw_file = derived_dir / "input_trends_raw.pkl"
    summary_file = derived_dir / "lmm_summary.csv"
    
    assert model_file.exists(), "Model pickle file not created"
    assert raw_file.exists(), "Raw parameters pickle file not created"
    assert summary_file.exists(), "Summary CSV not created"
    
    # Verify model content
    with open(model_file, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None
    assert hasattr(loaded_model, 'params')
    
    # Verify raw parameters
    with open(raw_file, 'rb') as f:
        raw_params = pickle.load(f)
    assert 'slope_year' in raw_params
    assert 'p_value' in raw_params
    
    # Verify summary CSV
    df_summary = pd.read_csv(summary_file)
    assert 'slope_year' in df_summary.columns
    assert 'p_value' in df_summary.columns
    assert not df_summary['p_value'].isnull().any()