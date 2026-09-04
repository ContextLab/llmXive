import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import yaml

# Import the functions to test
from code.data.preprocess import (
    filter_halos_by_particles,
    load_schema,
    validate_schema,
    stream_write_parquet,
    run_preprocessing_pipeline
)

@pytest.fixture
def sample_halo_data():
    """Create a sample DataFrame with halo data."""
    data = {
        'mass': [1e10, 1e11, 1e12, 1e9, 5e11],
        'position': [[0, 0, 0], [10, 10, 10], [20, 20, 20], [5, 5, 5], [15, 15, 15]],
        'velocity': [[100, 100, 100], [200, 200, 200], [300, 300, 300], [50, 50, 50], [250, 250, 250]],
        'particle_count': [100, 400, 500, 50, 350]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_schema_file(tmp_path):
    """Create a temporary JSON schema file for testing."""
    schema = {
        "type": "object",
        "properties": {
            "mass": {"type": "number"},
            "position": {"type": "array", "items": {"type": "number"}},
            "velocity": {"type": "array", "items": {"type": "number"}},
            "particle_count": {"type": "integer"}
        },
        "required": ["mass", "position", "velocity", "particle_count"]
    }
    schema_path = tmp_path / "test_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema, f)
    return str(schema_path)

def test_filter_halos_300_particles(sample_halo_data):
    """Test that filter_halos_by_particles correctly filters halos with < 300 particles."""
    filtered_df = filter_halos_by_particles(sample_halo_data, min_particles=300)
    
    # Check that all remaining halos have >= 300 particles
    assert all(filtered_df['particle_count'] >= 300)
    
    # Check that we removed the expected halos (100 and 50 particle counts)
    assert len(filtered_df) == 3
    
    # Verify the specific halos that should remain
    remaining_counts = set(filtered_df['particle_count'].tolist())
    assert remaining_counts == {400, 500, 350}

def test_filter_halos_no_removal(sample_halo_data):
    """Test filtering with a threshold that removes nothing."""
    filtered_df = filter_halos_by_particles(sample_halo_data, min_particles=50)
    assert len(filtered_df) == len(sample_halo_data)
    assert all(filtered_df['particle_count'] >= 50)

def test_filter_halos_all_removed(sample_halo_data):
    """Test filtering with a threshold that removes everything."""
    filtered_df = filter_halos_by_particles(sample_halo_data, min_particles=600)
    assert len(filtered_df) == 0

def test_filter_halos_missing_column(sample_halo_data):
    """Test that filtering raises an error if particle_count column is missing."""
    df_no_col = sample_halo_data.drop(columns=['particle_count'])
    with pytest.raises(ValueError, match="Input DataFrame must contain 'particle_count' column"):
        filter_halos_by_particles(df_no_col)

def test_load_schema(temp_schema_file):
    """Test loading a JSON schema."""
    schema = load_schema(temp_schema_file)
    assert 'type' in schema
    assert 'properties' in schema
    assert schema['type'] == 'object'

def test_validate_schema_valid(temp_schema_file, sample_halo_data):
    """Test validating a valid DataFrame against a schema."""
    schema = load_schema(temp_schema_file)
    result = validate_schema(sample_halo_data, schema)
    assert result is True

def test_validate_schema_invalid_structure(temp_schema_file):
    """Test validation fails for invalid data structure."""
    # Create data with wrong types
    invalid_data = pd.DataFrame({
        'mass': ['not a number'],
        'position': ['not', 'an', 'array'],
        'velocity': ['not', 'an', 'array'],
        'particle_count': ['not', 'an', 'integer']
    })
    schema = load_schema(temp_schema_file)
    with pytest.raises(Exception):  # jsonschema.ValidationError or similar
        validate_schema(invalid_data, schema)

def test_stream_write_parquet(sample_halo_data, tmp_path):
    """Test writing DataFrame to Parquet file."""
    output_path = tmp_path / "test_output.parquet"
    stream_write_parquet(sample_halo_data, str(output_path), chunk_size=2)
    
    # Verify file exists
    assert output_path.exists()
    
    # Read back and verify content
    df_read = pd.read_parquet(output_path)
    assert len(df_read) == len(sample_halo_data)
    assert list(df_read.columns) == ['mass', 'position', 'velocity', 'particle_count']

def test_run_preprocessing_pipeline(sample_halo_data, temp_schema_file, tmp_path):
    """Test the full preprocessing pipeline."""
    # Save sample data to a temporary parquet file to simulate input
    input_path = tmp_path / "input.parquet"
    sample_halo_data.to_parquet(input_path)
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    result_path = run_preprocessing_pipeline(
        input_path=str(input_path),
        output_dir=str(output_dir),
        min_particles=300,
        schema_path=temp_schema_file
    )
    
    # Verify output file exists
    assert Path(result_path).exists()
    
    # Verify content
    df_out = pd.read_parquet(result_path)
    assert all(df_out['particle_count'] >= 300)
    assert len(df_out) == 3
    assert list(df_out.columns) == ['mass', 'position', 'velocity', 'particle_count']
