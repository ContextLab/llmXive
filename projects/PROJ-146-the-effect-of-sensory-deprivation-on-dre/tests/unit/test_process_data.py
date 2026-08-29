import os
import tempfile
import pytest
import pandas as pd
import yaml

# Import the functions to test
from code.process_data import (
    load_protocol, 
    derive_condition_column, 
    process_data_for_threshold,
    main
)

@pytest.fixture
def sample_protocol():
    return {
        'strict_threshold_label': 'strict (complete isolation)',
        'moderate_threshold_label': 'moderate (partial sensory reduction)',
        'partial_threshold_label': 'partial (minimal sensory reduction)',
        'N': 200
    }

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'participant_id': [1, 2, 3],
        'recall': [1, 0, 1],
        'bizarreness': [5, 3, 6],
        'deprivation_intensity': [0.9, 0.5, 0.2]
    })

def test_derive_condition_column(sample_df):
    """Test that the condition column is correctly set to the label."""
    label = "strict (complete isolation)"
    result_df = derive_condition_column(sample_df, label)
    
    assert 'condition' in result_df.columns
    assert all(result_df['condition'] == label)

def test_process_data_for_threshold(sample_df, sample_protocol, tmp_path):
    """Test the full processing pipeline for a single threshold."""
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    
    sample_df.to_csv(input_path, index=False)
    
    label = sample_protocol['strict_threshold_label']
    
    process_data_for_threshold(
        input_data_path=str(input_path),
        output_path=str(output_path),
        threshold_label=label,
        protocol=sample_protocol
    )
    
    assert os.path.exists(output_path)
    result_df = pd.read_csv(output_path)
    
    assert 'condition' in result_df.columns
    assert all(result_df['condition'] == label)
    assert len(result_df) == len(sample_df)

def test_load_protocol_missing_file():
    """Test that load_protocol raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        load_protocol("non_existent_path.yaml")