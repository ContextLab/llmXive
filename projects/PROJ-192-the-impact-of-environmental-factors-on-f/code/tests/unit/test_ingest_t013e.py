import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.ingest import harmonize_metadata, load_and_harmonize_metadata, validate_metadata_columns

def test_harmonize_metadata_basic():
    """Test basic harmonization of metadata."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'biome': ['temperate forest', 'grassland', 'agricultural'],
        'pH': [6.5, 7.2, 5.8],
        'nutrients': [10.0, 15.5, 8.2]
    }
    df = pd.DataFrame(data)
    result = harmonize_metadata(df)
    
    assert 'biome' in result.columns
    assert result.loc[0, 'biome'] == 'Forest'
    assert result.loc[1, 'biome'] == 'Grassland'
    assert result.loc[2, 'biome'] == 'Agricultural'
    assert result.loc[0, 'pH'] == 6.5
    assert result.loc[1, 'nutrients'] == 15.5

def test_harmonize_metadata_case_insensitive():
    """Test that harmonization is case insensitive."""
    data = {
        'sample_id': ['S1'],
        'biome': ['TEMPERATE FOREST'],
        'pH': [6.5],
        'nutrients': [10.0]
    }
    df = pd.DataFrame(data)
    result = harmonize_metadata(df)
    
    assert result.loc[0, 'biome'] == 'Forest'

def test_harmonize_metadata_numeric_conversion():
    """Test that numeric columns are converted correctly."""
    data = {
        'sample_id': ['S1'],
        'biome': ['Forest'],
        'pH': ['6.5'],
        'nutrients': ['10.0']
    }
    df = pd.DataFrame(data)
    result = harmonize_metadata(df)
    
    assert isinstance(result.loc[0, 'pH'], (int, float))
    assert isinstance(result.loc[0, 'nutrients'], (int, float))

def test_harmonize_metadata_invalid_values():
    """Test handling of invalid numeric values."""
    data = {
        'sample_id': ['S1'],
        'biome': ['Forest'],
        'pH': ['invalid'],
        'nutrients': ['10.0']
    }
    df = pd.DataFrame(data)
    result = harmonize_metadata(df)
    
    assert pd.isna(result.loc[0, 'pH'])
    assert result.loc[0, 'nutrients'] == 10.0

def test_harmonize_metadata_duplicate_ids():
    """Test handling of duplicate sample IDs."""
    data = {
        'sample_id': ['S1', 'S1', 'S2'],
        'biome': ['Forest', 'Grassland', 'Forest'],
        'pH': [6.5, 7.0, 6.5],
        'nutrients': [10.0, 15.0, 10.0]
    }
    df = pd.DataFrame(data)
    result = harmonize_metadata(df)
    
    # Should keep the last occurrence
    assert len(result) == 2
    assert result.loc[result[result['sample_id'] == 'S1'].index[0], 'biome'] == 'Grassland'

def test_load_and_harmonize_metadata_creates_file():
    """Test that load_and_harmonize_metadata creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.csv')
        output_path = os.path.join(tmpdir, 'output.csv')
        
        data = {
            'sample_id': ['S1'],
            'biome': ['Forest'],
            'pH': [6.5],
            'nutrients': [10.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        result = load_and_harmonize_metadata(input_path, output_path)
        
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 1
        assert loaded_df.loc[0, 'biome'] == 'Forest'

def test_validate_metadata_columns_valid():
    """Test validation with all required columns present."""
    data = {
        'sample_id': ['S1'],
        'biome': ['Forest'],
        'pH': [6.5],
        'nutrients': [10.0]
    }
    df = pd.DataFrame(data)
    is_valid, missing = validate_metadata_columns(df, ['pH', 'nutrients'])
    assert is_valid
    assert len(missing) == 0

def test_validate_metadata_columns_invalid():
    """Test validation with missing required columns."""
    data = {
        'sample_id': ['S1'],
        'biome': ['Forest'],
        'pH': [6.5]
    }
    df = pd.DataFrame(data)
    is_valid, missing = validate_metadata_columns(df, ['pH', 'nutrients'])
    assert not is_valid
    assert 'nutrients' in missing