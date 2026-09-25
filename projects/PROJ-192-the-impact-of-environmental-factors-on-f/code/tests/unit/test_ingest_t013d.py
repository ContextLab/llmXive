import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.ingest import (
    harmonize_metadata, 
    validate_metadata_columns,
    harmonize_biome_labels,
    load_and_harmonize_metadata,
    process_ingestion_from_df
)

@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'pH': [5.5, 6.2, 7.0, 5.8],
        'biome': ['temperate forest', 'grassland', 'desert', 'tropical forest'],
        'latitude': [45.0, 40.0, 35.0, 10.0],
        'longitude': [-120.0, -110.0, -100.0, -90.0],
        'nutrients': [10.5, 12.3, 5.2, 15.1]
    })

@pytest.fixture
def sample_metadata_with_nans(sample_metadata):
    """Create sample metadata with missing values."""
    df = sample_metadata.copy()
    df.loc[1, 'pH'] = None
    df.loc[2, 'nutrients'] = None
    return df

def test_validate_metadata_columns_valid(sample_metadata):
    """Test validation passes for valid metadata."""
    assert validate_metadata_columns(sample_metadata) is True

def test_validate_metadata_columns_invalid():
    """Test validation fails for missing columns."""
    df = pd.DataFrame({
        'sample_id': ['S1'],
        'pH': [5.5]
        # Missing biome, latitude, longitude
    })
    assert validate_metadata_columns(df) is False

def test_harmonize_biome_labels():
    """Test biome label harmonization."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'pH': [5.5, 6.0, 7.0],
        'biome': ['temperate forest', 'GRASSLAND', 'Desert'],
        'latitude': [45.0, 40.0, 35.0],
        'longitude': [-120.0, -110.0, -100.0]
    })
    
    result = harmonize_biome_labels(df)
    
    assert result['biome'].iloc[0] == 'Forest'
    assert result['biome'].iloc[1] == 'Grassland'
    assert result['biome'].iloc[2] == 'Desert'

def test_harmonize_metadata_basic(sample_metadata):
    """Test basic metadata harmonization."""
    result = harmonize_metadata(sample_metadata)
    
    # Check required columns exist
    assert 'sample_id' in result.columns
    assert 'pH' in result.columns
    assert 'biome' in result.columns
    assert 'latitude' in result.columns
    assert 'longitude' in result.columns
    
    # Check biome harmonization
    assert result['biome'].iloc[0] == 'Forest'
    assert result['biome'].iloc[1] == 'Grassland'
    
    # Check data types
    assert result['pH'].dtype in ['float64', 'int64']

def test_harmonize_metadata_with_nans(sample_metadata_with_nans):
    """Test harmonization handles missing values."""
    result = harmonize_metadata(sample_metadata_with_nans)
    
    # Should not crash
    assert len(result) == 4
    
    # NaNs should be preserved (for later imputation)
    assert pd.isna(result['pH'].iloc[1])

def test_harmonize_metadata_duplicate_ids():
    """Test handling of duplicate sample IDs."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S1', 'S2'],
        'pH': [5.5, 6.0, 7.0],
        'biome': ['forest', 'forest', 'grassland'],
        'latitude': [45.0, 45.0, 40.0],
        'longitude': [-120.0, -120.0, -110.0]
    })
    
    result = harmonize_metadata(df)
    
    # Should remove duplicates
    assert len(result) == 2
    assert list(result['sample_id']) == ['S1', 'S2']

def test_process_ingestion_from_df_creates_file(sample_metadata):
    """Test that processing creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = process_ingestion_from_df(sample_metadata, tmpdir)
        
        assert os.path.exists(output_path)
        assert output_path.endswith('harmonized_matrix.csv')
        
        # Verify file contents
        result_df = pd.read_csv(output_path)
        assert len(result_df) == 4
        assert 'biome' in result_df.columns

def test_load_and_harmonize_metadata(tmp_path):
    """Test loading from file and harmonizing."""
    # Create test input file
    input_file = tmp_path / "input_metadata.csv"
    df_input = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'pH': [5.5, 6.2],
        'biome': ['forest', 'grassland'],
        'latitude': [45.0, 40.0],
        'longitude': [-120.0, -110.0]
    })
    df_input.to_csv(input_file, index=False)
    
    output_dir = tmp_path / "output"
    output_path = load_and_harmonize_metadata(str(input_file), str(output_dir))
    
    assert os.path.exists(output_path)
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 2
    assert result_df['biome'].iloc[0] == 'Forest'

def test_harmonize_metadata_numeric_conversion():
    """Test that numeric columns are properly converted."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'pH': ['5.5', '6.2'],  # Strings
        'biome': ['forest', 'grassland'],
        'latitude': [45.0, 40.0],
        'longitude': [-120.0, -110.0],
        'nutrients': ['10.5', '12.3']  # Strings
    })
    
    result = harmonize_metadata(df)
    
    # Should be numeric
    assert result['pH'].dtype in ['float64', 'int64']
    assert result['nutrients'].dtype in ['float64', 'int64']
    assert result['pH'].iloc[0] == 5.5
    assert result['nutrients'].iloc[0] == 10.5

def test_harmonize_metadata_invalid_values():
    """Test handling of invalid numeric values."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'pH': ['5.5', 'invalid'],  # One invalid
        'biome': ['forest', 'grassland'],
        'latitude': [45.0, 40.0],
        'longitude': [-120.0, -110.0]
    })
    
    result = harmonize_metadata(df)
    
    # Invalid value should become NaN
    assert pd.isna(result['pH'].iloc[1])
    assert result['pH'].iloc[0] == 5.5
