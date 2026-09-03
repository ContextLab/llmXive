import pytest
import pandas as pd
import os
import json
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Import functions to test
from ingest import (
    extract_resistance_column,
    convert_categorical_to_ordinal,
    check_herbivore_density_normalization,
    harmonize_dataset
)
from config import DATA_ROOT

def test_extract_resistance_column_missing():
    """Test that an error is raised if resistance column is missing."""
    df = pd.DataFrame({'sample_id': [1, 2], 'other': [3, 4]})
    with pytest.raises(ValueError, match="No quantifiable resistance metric found"):
        extract_resistance_column(df)

def test_convert_categorical_to_ordinal():
    """Test conversion of categorical resistance to ordinal."""
    data = {
        'resistance': ['Low', 'Medium', 'High'],
        'value': [1, 2, 3]
    }
    df = pd.DataFrame(data)
    
    # Mock the file writing to avoid actual I/O in unit test
    with patch('ingest.open', create=True):
        result_df = convert_categorical_to_ordinal(df)
    
    assert result_df['resistance'].tolist() == [1, 2, 3]
    assert result_df['resistance'].dtype == 'int64'

def test_check_herbivore_density_missing():
    """Test that metadata is updated when herbivore_density is missing."""
    df = pd.DataFrame({'sample_id': [1, 2], 'resistance': [1, 2]})
    
    # Ensure the interim directory exists for the test
    interim_path = os.path.join(DATA_ROOT, 'interim')
    os.makedirs(interim_path, exist_ok=True)
    
    result_df = check_herbivore_density_normalization(df)
    
    metadata_path = os.path.join(interim_path, 'metadata.json')
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert metadata.get('herbivore_density_missing') is True

def test_harmonize_dataset():
    """Test that harmonize_dataset adds the imputation_flag column."""
    df = pd.DataFrame({
        'Sample ID': [1, 2],
        'Resistance': [1, 2]
    })
    
    result_df = harmonize_dataset(df)
    
    assert 'imputation_flag' in result_df.columns
    assert result_df['imputation_flag'].tolist() == [False, False]
    # Check column name standardization
    assert 'sample_id' in result_df.columns
    assert 'resistance' in result_df.columns
