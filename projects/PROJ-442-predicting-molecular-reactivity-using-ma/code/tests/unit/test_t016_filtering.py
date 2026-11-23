import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from src.data.ingestion import filter_by_class_sample_size

def test_filter_by_class_sample_size():
    """Test that classes with < 1000 samples are removed."""
    # Create a dataframe with 3 classes: A (2000), B (500), C (1500)
    data = {
        'reaction_smiles': ['CCO'] * 3500,
        'reaction_type': ['A'] * 2000 + ['B'] * 500 + ['C'] * 1000,
        'target': [1.0] * 3500
    }
    # Add more rows for C to make it 1500
    data['reaction_type'] += ['C'] * 500
    
    df = pd.DataFrame(data)
    
    # Filter
    filtered_df = filter_by_class_sample_size(df, min_size=1000)
    
    # Check results
    assert 'B' not in filtered_df['reaction_type'].values
    assert 'A' in filtered_df['reaction_type'].values
    assert 'C' in filtered_df['reaction_type'].values
    assert len(filtered_df) == 3500  # 2000 + 1500
    assert filtered_df['reaction_type'].value_counts()['B'] == 0 if 'B' in filtered_df['reaction_type'].values else True

def test_filter_by_class_sample_size_all_removed():
    """Test that if all classes are < 1000, the result is empty."""
    data = {
        'reaction_smiles': ['CCO'] * 500,
        'reaction_type': ['X'] * 500,
        'target': [1.0] * 500
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_by_class_sample_size(df, min_size=1000)
    
    assert filtered_df.empty

def test_filter_by_class_sample_size_none_removed():
    """Test that if all classes are >= 1000, nothing is removed."""
    data = {
        'reaction_smiles': ['CCO'] * 3000,
        'reaction_type': ['A'] * 1000 + ['B'] * 1000 + ['C'] * 1000,
        'target': [1.0] * 3000
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_by_class_sample_size(df, min_size=1000)
    
    assert len(filtered_df) == 3000
    assert set(filtered_df['reaction_type'].unique()) == {'A', 'B', 'C'}
