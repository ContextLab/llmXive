#!/usr/bin/env python
"""
Unit tests for expert_reinference module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.expert_reinference import (
    load_tree_predictions,
    generate_velocity_vectors,
    save_velocity_vectors
)
from models.expert_loader import get_known_expert_ids

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'prompt_embedding': [np.random.rand(512).tolist() for _ in range(10)],
        'noise_level': [0.1 * i for i in range(10)],
        'predicted_routing_label': ['expert_0', 'expert_1', 'expert_2'] * 3 + ['expert_0']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_tree_predictions_valid_file(sample_data, temp_output_dir):
    """Test loading valid tree predictions."""
    input_path = os.path.join(temp_output_dir, 'test_input.parquet')
    sample_data.to_parquet(input_path)
    
    df = load_tree_predictions(input_path, 'dummy_tree_path')
    
    assert len(df) == 10
    assert 'prompt_embedding' in df.columns
    assert 'noise_level' in df.columns
    assert 'predicted_routing_label' in df.columns

def test_load_tree_predictions_missing_file():
    """Test loading from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_tree_predictions('non_existent.parquet', 'dummy_path')

def test_load_tree_predictions_missing_columns(sample_data, temp_output_dir):
    """Test loading file with missing required columns."""
    # Remove a required column
    df_incomplete = sample_data.drop(columns=['predicted_routing_label'])
    input_path = os.path.join(temp_output_dir, 'incomplete.parquet')
    df_incomplete.to_parquet(input_path)
    
    with pytest.raises(ValueError):
        load_tree_predictions(input_path, 'dummy_path')

def test_generate_velocity_vectors_valid(sample_data, temp_output_dir):
    """Test generating velocity vectors from valid predictions."""
    config = {
        'step_size': 0.1,
        'steps': 10
    }
    
    velocity_df = generate_velocity_vectors(sample_data, config)
    
    assert 'velocity_vector' in velocity_df.columns
    assert len(velocity_df) > 0
    
    # Check that velocity vectors are lists of floats
    for i, row in velocity_df.iterrows():
        assert isinstance(row['velocity_vector'], list)
        assert len(row['velocity_vector']) > 0
        assert all(isinstance(v, float) for v in row['velocity_vector'])

def test_generate_velocity_vectors_invalid_labels(sample_data, temp_output_dir):
    """Test handling of invalid routing labels."""
    # Add some invalid labels
    sample_data.loc[0, 'predicted_routing_label'] = 'invalid_expert'
    sample_data.loc[1, 'predicted_routing_label'] = 'another_invalid'
    
    config = {
        'step_size': 0.1,
        'steps': 10
    }
    
    velocity_df = generate_velocity_vectors(sample_data, config)
    
    # Should have fewer rows than input due to skipped invalid labels
    assert len(velocity_df) < len(sample_data)
    
    # All remaining labels should be valid
    known_ids = get_known_expert_ids()
    for label in velocity_df['predicted_routing_label']:
        assert label in known_ids

def test_save_velocity_vectors(sample_data, temp_output_dir):
    """Test saving velocity vectors to parquet."""
    # First generate some velocity vectors
    config = {'step_size': 0.1, 'steps': 10}
    velocity_df = generate_velocity_vectors(sample_data, config)
    
    output_path = os.path.join(temp_output_dir, 'output.parquet')
    save_velocity_vectors(velocity_df, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify we can load it back
    loaded_df = pd.read_parquet(output_path)
    assert len(loaded_df) == len(velocity_df)
    assert 'velocity_vector' in loaded_df.columns

def test_generate_velocity_vectors_empty_result():
    """Test that an error is raised if no valid vectors are generated."""
    # Create data with only invalid labels
    invalid_data = pd.DataFrame({
        'prompt_embedding': [np.random.rand(512).tolist() for _ in range(5)],
        'noise_level': [0.1, 0.2, 0.3, 0.4, 0.5],
        'predicted_routing_label': ['invalid_1', 'invalid_2', 'invalid_3', 'invalid_4', 'invalid_5']
    })
    
    config = {'step_size': 0.1, 'steps': 10}
    
    with pytest.raises(RuntimeError, match="No valid velocity vectors were generated"):
        generate_velocity_vectors(invalid_data, config)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])