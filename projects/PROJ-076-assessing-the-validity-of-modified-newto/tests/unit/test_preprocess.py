"""
Unit tests for the rotation curve parser and inclination filter logic.

These tests verify the parsing logic for SPARC data files,
ensuring correct extraction of radial distance, velocity, and uncertainty.
Additionally, they test the inclination filter logic to ensure galaxies
with inclination uncertainty >= 10° or fewer than 15 data points are excluded.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
from preprocess import parse_sparc_file, parse_galaxy_directory, extract_rotation_curves, apply_quality_filters

@pytest.fixture
def sample_sparc_file(tmp_path):
    """Create a sample SPARC data file for testing."""
    file_path = tmp_path / "test_galaxy.dat"
    
    # Create sample data with typical SPARC format
    data = """# Galaxy Test Galaxy
    # Radius(kpc) Vobs(km/s) Err(km/s)
    0.1 10.0 0.5
    0.5 25.0 0.8
    1.0 40.0 1.0
    2.0 65.0 1.5
    3.0 80.0 2.0
    4.0 90.0 2.5
    5.0 95.0 3.0
    6.0 98.0 3.5
    7.0 100.0 4.0
    8.0 102.0 4.5
    """
    
    file_path.write_text(data)
    return file_path

@pytest.fixture
def sample_sparc_file_no_error(tmp_path):
    """Create a sample SPARC data file without error column."""
    file_path = tmp_path / "test_galaxy_noerr.dat"
    
    data = """# Galaxy Test Galaxy No Error
    # Radius(kpc) Vobs(km/s)
    0.1 10.0
    0.5 25.0
    1.0 40.0
    2.0 65.0
    """
    
    file_path.write_text(data)
    return file_path

@pytest.fixture
def sample_sparc_file_malformed(tmp_path):
    """Create a malformed SPARC data file."""
    file_path = tmp_path / "malformed.dat"
    file_path.write_text("This is not valid data\nNot numbers here\nabc def ghi")
    return file_path

def test_parse_sparc_file_basic(sample_sparc_file):
    """Test basic parsing of a valid SPARC file."""
    df = parse_sparc_file(sample_sparc_file)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10  # 10 data points
    assert 'radius' in df.columns
    assert 'velocity' in df.columns
    assert 'uncertainty' in df.columns
    
    # Check data types
    assert df['radius'].dtype in [np.float64, np.int64]
    assert df['velocity'].dtype in [np.float64, np.int64]
    assert df['uncertainty'].dtype in [np.float64, np.int64]
    
    # Check values
    assert df['radius'].iloc[0] == 0.1
    assert df['velocity'].iloc[0] == 10.0
    assert df['uncertainty'].iloc[0] == 0.5

def test_parse_sparc_file_no_error_column(sample_sparc_file_no_error):
    """Test parsing when error column is missing."""
    df = parse_sparc_file(sample_sparc_file_no_error)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert 'radius' in df.columns
    assert 'velocity' in df.columns
    assert 'uncertainty' in df.columns
    
    # Uncertainty should be 0.0 when not provided
    assert all(df['uncertainty'] == 0.0)

def test_parse_sparc_file_nonexistent():
    """Test parsing a non-existent file."""
    with pytest.raises(FileNotFoundError):
        parse_sparc_file(Path("nonexistent_file.dat"))

def test_parse_sparc_file_malformed(sample_sparc_file_malformed):
    """Test parsing a malformed file."""
    with pytest.raises(ValueError):
        parse_sparc_file(sample_sparc_file_malformed)

def test_parse_sparc_file_empty(tmp_path):
    """Test parsing an empty file."""
    empty_file = tmp_path / "empty.dat"
    empty_file.write_text("")
    
    with pytest.raises(ValueError):
        parse_sparc_file(empty_file)

def test_parse_sparc_file_negative_values(tmp_path):
    """Test parsing handles negative values correctly."""
    file_path = tmp_path / "negative.dat"
    data = """# Galaxy Test
    # Radius(kpc) Vobs(km/s) Err(km/s)
    -1.0 10.0 0.5
    0.5 25.0 0.8
    1.0 -40.0 1.0
    """
    file_path.write_text(data)
    
    df = parse_sparc_file(file_path)
    
    # Negative radius and velocity should be filtered out
    assert all(df['radius'] >= 0)
    assert all(df['velocity'] >= 0)

def test_parse_galaxy_directory(tmp_path):
    """Test parsing all files in a galaxy directory."""
    # Create subdirectory structure
    galaxy_dir = tmp_path / "galaxy_test"
    galaxy_dir.mkdir()
    
    # Create multiple data files
    for i in range(3):
        file_path = galaxy_dir / f"curve_{i}.dat"
        file_path.write_text(f"""# Galaxy Test
        # Radius(kpc) Vobs(km/s) Err(km/s)
        {i*0.1} {10+i*5} 0.{i}
        """)
    
    result = parse_galaxy_directory(galaxy_dir)
    
    assert isinstance(result, dict)
    assert len(result) == 3
    assert all(isinstance(df, pd.DataFrame) for df in result.values())
    assert all(len(df) == 1 for df in result.values())

def test_extract_rotation_curves(tmp_path):
    """Test the main extraction function."""
    # Setup directory structures
    data_dir = tmp_path / "data"
    sparc_dir = data_dir / "raw"
    output_dir = tmp_path / "output"
    
    sparc_dir.mkdir(parents=True)
    
    # Create a test galaxy directory
    galaxy_dir = sparc_dir / "test_galaxy"
    galaxy_dir.mkdir()
    
    data_file = galaxy_dir / "test.dat"
    data_file.write_text("""# Galaxy Test
    # Radius(kpc) Vobs(km/s) Err(km/s)
    0.1 10.0 0.5
    0.5 25.0 0.8
    1.0 40.0 1.0
    """)
    
    # Run extraction
    total, successful = extract_rotation_curves(data_dir, output_dir)
    
    assert total == 1
    assert successful == 1
    assert (output_dir / "test.dat.csv").exists()
    
    # Verify output content
    output_df = pd.read_csv(output_dir / "test.dat.csv")
    assert len(output_df) == 3
    assert 'radius' in output_df.columns
    assert 'velocity' in output_df.columns
    assert 'uncertainty' in output_df.columns

# --- Tests for T011: Inclination Filter Logic ---

def test_apply_quality_filters_inclination_threshold():
    """Test that galaxies with inclination uncertainty >= 10% are filtered out."""
    # Create a DataFrame simulating parsed galaxy data with inclination info
    # Columns typically include: radius, velocity, uncertainty, inclination, inclination_err
    data = {
        'radius': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        'velocity': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        'uncertainty': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9],
        'inclination': [45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0],
        'inclination_err': [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0] # All < 10, should pass
    }
    df_good = pd.DataFrame(data)
    
    # Create a second galaxy with high inclination error (>= 10%)
    data_bad_incl = {
        'radius': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        'velocity': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0, 150.0],
        'uncertainty': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9],
        'inclination': [45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0],
        'inclination_err': [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0] # Exactly 10, should fail
    }
    df_bad_incl = pd.DataFrame(data_bad_incl)

    # Combine into a single DataFrame with a galaxy identifier
    df_good['galaxy_id'] = 'galaxy_good'
    df_bad_incl['galaxy_id'] = 'galaxy_bad'
    
    df_combined = pd.concat([df_good, df_bad_incl], ignore_index=True)
    
    # Apply filters
    filtered_df = apply_quality_filters(df_combined)
    
    # Verify results
    assert len(filtered_df) == 15  # Only the good galaxy should remain
    assert all(filtered_df['galaxy_id'] == 'galaxy_good')

def test_apply_quality_filters_min_points():
    """Test that galaxies with fewer than 15 data points are filtered out."""
    # Create a DataFrame with exactly 15 points (should pass)
    data_15 = {
        'radius': list(range(1, 16)),
        'velocity': list(range(10, 160, 10)),
        'uncertainty': [0.5] * 15,
        'inclination': [45.0] * 15,
        'inclination_err': [5.0] * 15,
        'galaxy_id': ['galaxy_15'] * 15
    }
    df_15 = pd.DataFrame(data_15)
    
    # Create a DataFrame with 14 points (should fail)
    data_14 = {
        'radius': list(range(1, 15)),
        'velocity': list(range(10, 150, 10)),
        'uncertainty': [0.5] * 14,
        'inclination': [45.0] * 14,
        'inclination_err': [5.0] * 14,
        'galaxy_id': ['galaxy_14'] * 14
    }
    df_14 = pd.DataFrame(data_14)
    
    df_combined = pd.concat([df_15, df_14], ignore_index=True)
    
    # Apply filters
    filtered_df = apply_quality_filters(df_combined)
    
    # Verify results
    assert len(filtered_df) == 15  # Only the 15-point galaxy should remain
    assert all(filtered_df['galaxy_id'] == 'galaxy_15')

def test_apply_quality_filters_combined_criteria():
    """Test filtering with both inclination and point count criteria."""
    # Galaxy A: Good points, Good inclination (Pass)
    data_a = {
        'radius': list(range(1, 20)),
        'velocity': list(range(10, 200, 10)),
        'uncertainty': [0.5] * 19,
        'inclination': [45.0] * 19,
        'inclination_err': [5.0] * 19,
        'galaxy_id': ['galaxy_A'] * 19
    }
    df_a = pd.DataFrame(data_a)
    
    # Galaxy B: Good points, Bad inclination (Fail)
    data_b = {
        'radius': list(range(1, 20)),
        'velocity': list(range(10, 200, 10)),
        'uncertainty': [0.5] * 19,
        'inclination': [45.0] * 19,
        'inclination_err': [12.0] * 19,
        'galaxy_id': ['galaxy_B'] * 19
    }
    df_b = pd.DataFrame(data_b)
    
    # Galaxy C: Bad points, Good inclination (Fail)
    data_c = {
        'radius': list(range(1, 10)),
        'velocity': list(range(10, 100, 10)),
        'uncertainty': [0.5] * 9,
        'inclination': [45.0] * 9,
        'inclination_err': [5.0] * 9,
        'galaxy_id': ['galaxy_C'] * 9
    }
    df_c = pd.DataFrame(data_c)
    
    # Galaxy D: Bad points, Bad inclination (Fail)
    data_d = {
        'radius': list(range(1, 10)),
        'velocity': list(range(10, 100, 10)),
        'uncertainty': [0.5] * 9,
        'inclination': [45.0] * 9,
        'inclination_err': [15.0] * 9,
        'galaxy_id': ['galaxy_D'] * 9
    }
    df_d = pd.DataFrame(data_d)
    
    df_combined = pd.concat([df_a, df_b, df_c, df_d], ignore_index=True)
    
    # Apply filters
    filtered_df = apply_quality_filters(df_combined)
    
    # Verify results: Only Galaxy A should remain
    assert len(filtered_df) == 19
    assert all(filtered_df['galaxy_id'] == 'galaxy_A')