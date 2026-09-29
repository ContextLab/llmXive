import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import (
    validate_url_reachability,
    validate_source_citations,
    derive_primary_anion_cation_group,
    validate_entry,
    validate_no_missing_primary_predictors,
    flag_high_variance_ranges,
    generate_data_availability_report,
    validate_data_gap,
    load_curated_literature_data
)
from code.contracts.schemas import CeramicEntry

@pytest.fixture
def sample_csv():
    """Create a sample CSV file for testing."""
    data = {
        'composition': ['Al2O3', 'ZrO2', 'SiC'],
        'weibull_modulus': [10.5, 12.3, 8.7],
        'sample_count': [50, 45, 35],
        'sintering_temp': [1600, 1400, 2100]
    }
    df = pd.DataFrame(data)
    output_path = Path("data/raw/test_curated.csv")
    df.to_csv(output_path, index=False)
    yield output_path
    # Cleanup
    if output_path.exists():
        output_path.unlink()

@pytest.fixture
def marker_file():
    """Create a marker file for testing."""
    marker_path = Path("data/processed/data_availability_marker.txt")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()
    yield marker_path
    # Cleanup
    if marker_path.exists():
        marker_path.unlink()

def test_validate_url_reachability():
    """Test URL reachability validation."""
    # Test with a known valid URL
    assert validate_url_reachability("https://httpbin.org/status/200") == True
    # Test with an invalid URL
    assert validate_url_reachability("https://invalid.url.that.does.not.exist") == False

def test_validate_source_citations():
    """Test source citation validation."""
    # Test with a valid URL
    assert validate_source_citations("https://httpbin.org/status/200") == True
    # Test with an invalid URL
    assert validate_source_citations("https://invalid.url.that.does.not.exist") == False

def test_derive_primary_anion_cation_group():
    """Test derivation of primary anion/cation group."""
    assert derive_primary_anion_cation_group("Al2O3") == "O-Al"
    assert derive_primary_anion_cation_group("ZrO2") == "O-Zr"
    assert derive_primary_anion_cation_group("SiC") == "C-Si"

def test_validate_entry():
    """Test entry validation against schema."""
    valid_entry = {
        'composition': 'Al2O3',
        'weibull_modulus': 10.5,
        'sample_count': 50,
        'sintering_temp': 1600.0,
        'primary_anion_cation_group': 'O-Al'
    }
    assert validate_entry(valid_entry) == True
    
    invalid_entry = {
        'composition': 'Invalid',
        'weibull_modulus': -1,  # Invalid value
        'sample_count': 50
    }
    assert validate_entry(invalid_entry) == False

def test_validate_no_missing_primary_predictors():
    """Test validation of no missing primary predictors."""
    df = pd.DataFrame({
        'composition': ['Al2O3', 'ZrO2'],
        'weibull_modulus': [10.5, 12.3],
        'sample_count': [50, 45]
    })
    assert validate_no_missing_primary_predictors(df) == True
    
    df_missing = pd.DataFrame({
        'composition': ['Al2O3', None],
        'weibull_modulus': [10.5, 12.3],
        'sample_count': [50, 45]
    })
    assert validate_no_missing_primary_predictors(df_missing) == False

def test_flag_high_variance_ranges():
    """Test flagging of high variance ranges."""
    df = pd.DataFrame({
        'composition': ['Al2O3', 'ZrO2', 'SiC'],
        'weibull_modulus': [10.5, 12.3, 8.7],
        'range_original': ['8-12', '10-15', '5-10'],
        'sample_count': [50, 45, 35]
    })
    filtered_df = flag_high_variance_ranges(df, threshold=0.5)
    assert len(filtered_df) <= len(df)

def test_generate_data_availability_report(tmp_path):
    """Test generation of data availability report."""
    import json
    report = generate_data_availability_report(25, 30)
    assert report['total_entries'] == 25
    assert report['required_entries'] == 30
    assert report['status'] == 'INSUFFICIENT'
    assert os.path.exists('data/reports/data_availability_report.json')

def test_validate_data_gap_insufficient(tmp_path, capsys):
    """Test data gap validation with insufficient data."""
    # Create count file with insufficient data
    count_file = Path("data/processed/final_count.txt")
    count_file.parent.mkdir(parents=True, exist_ok=True)
    count_file.write_text("25")
    
    # Mock sys.exit to capture the exit
    with pytest.raises(SystemExit) as excinfo:
        validate_data_gap()
    
    assert excinfo.value.code == 1
    assert os.path.exists('data/reports/data_availability_report.json')
    
    # Cleanup
    count_file.unlink()

def test_validate_data_gap_sufficient(tmp_path, capsys):
    """Test data gap validation with sufficient data."""
    # Create count file with sufficient data
    count_file = Path("data/processed/final_count.txt")
    count_file.parent.mkdir(parents=True, exist_ok=True)
    count_file.write_text("50")
    
    # Mock sys.exit to capture the exit
    with pytest.raises(SystemExit) as excinfo:
        validate_data_gap()
    
    assert excinfo.value.code == 0
    
    # Cleanup
    count_file.unlink()

def test_load_curated_literature_data(sample_csv, marker_file):
    """Test loading of curated literature data."""
    # Create the input file
    input_file = Path("data/raw/curated_literature.csv")
    sample_csv.rename(input_file)
    
    try:
        df = load_curated_literature_data()
        assert len(df) == 3
        assert 'composition' in df.columns
        assert 'weibull_modulus' in df.columns
        assert 'sample_count' in df.columns
        assert 'sintering_temp' in df.columns
        assert os.path.exists('data/raw/curated_literature_raw.json')
    finally:
        # Cleanup
        if input_file.exists():
            input_file.unlink()
        if Path('data/raw/curated_literature_raw.json').exists():
            Path('data/raw/curated_literature_raw.json').unlink()

def test_load_curated_literature_data_missing_marker(sample_csv):
    """Test loading when marker file is missing."""
    # Create the input file
    input_file = Path("data/raw/curated_literature.csv")
    sample_csv.rename(input_file)
    
    try:
        # Should raise an error if marker is missing and fetch fails
        with pytest.raises(RuntimeError):
            load_curated_literature_data()
    finally:
        # Cleanup
        if input_file.exists():
            input_file.unlink()
