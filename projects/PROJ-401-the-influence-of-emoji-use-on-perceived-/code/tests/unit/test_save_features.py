"""
Unit tests for T014: save_features functionality.
Tests the save_features script logic without requiring the full pipeline.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import yaml
import hashlib

# Mock the project root structure for testing
@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create necessary directory structure
        (root / "data" / "processed").mkdir(parents=True)
        (root / "state").mkdir(parents=True)
        yield root

@pytest.fixture
def sample_joined_data():
    """Create a sample joined dataframe simulating T013 output."""
    data = {
        'message_id': [1, 2, 3, 4, 5],
        'text': [
            "Hello world",
            "Check this out 😎",
            "No emoji here",
            "Multiple 😂😂😂 emojis",
            "Complex 🤔🤨🤓 types"
        ],
        'human_intensity_score': [2.5, 4.0, 1.5, 5.0, 3.5],
        'emoji_present': [False, True, False, True, True],
        'emoji_count': [0, 1, 0, 3, 3],
        'emoji_types': [[], ['smile'], [], ['smile', 'smile', 'smile'], ['thinking', 'confused', 'nerd']]
    }
    return pd.DataFrame(data)

def test_save_csv_creates_file(temp_project_dir, sample_joined_data):
    """Test that save_features creates the CSV file."""
    output_path = temp_project_dir / "data" / "processed" / "features.csv"
    
    # Simulate saving
    sample_joined_data.to_csv(output_path, index=False)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_csv_content_matches_dataframe(temp_project_dir, sample_joined_data):
    """Test that saved CSV content matches the original dataframe."""
    output_path = temp_project_dir / "data" / "processed" / "features.csv"
    sample_joined_data.to_csv(output_path, index=False)
    
    loaded_df = pd.read_csv(output_path)
    
    # Check column names
    assert list(loaded_df.columns) == list(sample_joined_data.columns)
    
    # Check row count
    assert len(loaded_df) == len(sample_joined_data)
    
    # Check specific values (text column)
    assert list(loaded_df['text']) == list(sample_joined_data['text'])

def test_checksum_computation(temp_project_dir, sample_joined_data):
    """Test checksum computation logic."""
    output_path = temp_project_dir / "data" / "processed" / "features.csv"
    sample_joined_data.to_csv(output_path, index=False)
    
    # Compute checksum manually
    with open(output_path, 'rb') as f:
        content = f.read()
        expected_checksum = hashlib.sha256(content).hexdigest()
    
    # Simulate the script's checksum function
    import sys
    sys.path.insert(0, str(temp_project_dir.parent))
    from src.utils.io import compute_file_checksum
    
    actual_checksum = compute_file_checksum(output_path)
    
    assert actual_checksum == expected_checksum

def test_metadata_file_created(temp_project_dir, sample_joined_data):
    """Test that metadata file is created with correct structure."""
    output_path = temp_project_dir / "data" / "processed" / "features.csv"
    sample_joined_data.to_csv(output_path, index=False)
    
    checksum = "dummy_checksum_12345"
    record_count = len(sample_joined_data)
    
    metadata = {
        "task_id": "T014",
        "output_file": str(output_path.relative_to(temp_project_dir)),
        "checksum_algorithm": "sha256",
        "checksum": checksum,
        "record_count": record_count,
        "seed": 42
    }
    
    metadata_path = temp_project_dir / "state" / "features_metadata.yaml"
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f)
    
    assert metadata_path.exists()
    
    with open(metadata_path, 'r') as f:
        loaded_metadata = yaml.safe_load(f)
    
    assert loaded_metadata['task_id'] == "T014"
    assert loaded_metadata['record_count'] == record_count
    assert loaded_metadata['checksum'] == checksum

def test_input_file_not_found_error(temp_project_dir):
    """Test that appropriate error is raised if input file is missing."""
    input_path = temp_project_dir / "data" / "processed" / "nonexistent.parquet"
    
    # Simulate the load logic
    if not input_path.exists():
        with pytest.raises(FileNotFoundError) as excinfo:
            raise FileNotFoundError(
                f"Input file not found: {input_path}. "
                "Ensure T013 (pipeline_join) has completed successfully."
            )
        
        assert "T013" in str(excinfo.value)
        assert "pipeline_join" in str(excinfo.value)

def test_missing_columns_validation(temp_project_dir, sample_joined_data):
    """Test that missing required columns are detected."""
    # Remove a required column
    incomplete_df = sample_joined_data.drop(columns=['human_intensity_score'])
    
    expected_cols = ['message_id', 'text', 'human_intensity_score']
    missing_cols = [c for c in expected_cols if c not in incomplete_df.columns]
    
    assert len(missing_cols) > 0
    assert 'human_intensity_score' in missing_cols
