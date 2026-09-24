"""
Unit tests for T013: Partition Metadata Generation.

These tests verify that the metadata generation logic correctly:
1. Generates the expected JSON schema.
2. Handles valid FEMNIST data.
3. Rejects invalid datasets (Shakespeare).
4. Produces consistent output for the same seed.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
import numpy as np

# Import the function to test
from code.data.generate_partition_metadata import generate_metadata_for_configuration
from code.config import Config

@pytest.fixture
def mock_config():
    """Create a valid Config object for FEMNIST."""
    config = Config(seed=42, alpha=0.1, epsilon=1.0, dataset="femnist")
    return config

@pytest.fixture
def mock_raw_data(tmp_path):
    """Create a mock FEMNIST parquet file."""
    data_path = tmp_path / "femnist.parquet"
    # Create a simple mock dataframe with 'user' and 'label' columns
    # FEMNIST typically has 'user', 'label', and 'pixels' (or similar)
    users = [f"user_{i}" for i in range(10)]
    labels = [np.random.randint(0, 62) for _ in range(100)]  # 62 classes in FEMNIST
    # Create a dataframe where each user has some samples
    df_data = []
    for i in range(10):
        user = users[i]
        # Assign random number of samples per user
        n_samples = np.random.randint(5, 20)
        for _ in range(n_samples):
            df_data.append({"user": user, "label": np.random.randint(0, 62), "pixels": "dummy"})
    
    df = pd.DataFrame(df_data)
    df.to_parquet(data_path)
    return data_path

@pytest.fixture
def mock_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "partitions"
    output_dir.mkdir()
    return output_dir

def test_generate_metadata_valid(mock_config, mock_raw_data, mock_output_dir):
    """Test that metadata is generated correctly for valid inputs."""
    result = generate_metadata_for_configuration(
        config=mock_config,
        raw_data_path=mock_raw_data,
        output_dir=mock_output_dir,
        seed=mock_config.seed
    )

    assert "output_path" in result
    assert os.path.exists(result["output_path"])

    # Verify JSON schema
    with open(result["output_path"], 'r') as f:
        metadata = json.load(f)

    assert isinstance(metadata, list)
    assert len(metadata) > 0

    for entry in metadata:
        assert "client_id" in entry
        assert "label_distribution" in entry
        assert "total_samples" in entry
        assert isinstance(entry["client_id"], str)
        assert isinstance(entry["label_distribution"], dict)
        assert isinstance(entry["total_samples"], int)
        
        # Verify total_samples matches sum of label_distribution
        assert entry["total_samples"] == sum(entry["label_distribution"].values())

def test_generate_metadata_rejects_shakespeare(mock_output_dir, tmp_path):
    """Test that Shakespeare dataset is explicitly rejected (T000 constraint)."""
    config = Config(seed=42, alpha=0.1, epsilon=1.0, dataset="shakespeare")
    fake_data_path = tmp_path / "shakespeare.parquet"
    fake_data_path.touch()

    with pytest.raises(ValueError) as exc_info:
        generate_metadata_for_configuration(
            config=config,
            raw_data_path=fake_data_path,
            output_dir=mock_output_dir,
            seed=42
        )

    assert "Shakespeare" in str(exc_info.value)
    assert "excluded" in str(exc_info.value).lower()

def test_generate_metadata_missing_file(mock_config, mock_output_dir, tmp_path):
    """Test that a missing raw data file raises FileNotFoundError."""
    fake_data_path = tmp_path / "nonexistent.parquet"

    with pytest.raises(FileNotFoundError):
        generate_metadata_for_configuration(
            config=mock_config,
            raw_data_path=fake_data_path,
            output_dir=mock_output_dir,
            seed=42
        )

def test_filename_naming_convention(mock_config, mock_raw_data, mock_output_dir):
    """Test that the output filename follows the pattern partition_femnist_{seed}_{alpha}.json."""
    result = generate_metadata_for_configuration(
        config=mock_config,
        raw_data_path=mock_raw_data,
        output_dir=mock_output_dir,
        seed=mock_config.seed
    )

    filename = os.path.basename(result["output_path"])
    expected_pattern = f"partition_femnist_{mock_config.seed}_0_1.json"
    
    # Note: The code formats 0.1 as 0_1
    assert filename == expected_pattern, f"Expected {expected_pattern}, got {filename}"

def test_metadata_consistency_same_seed(mock_config, mock_raw_data, mock_output_dir):
    """Test that running twice with the same seed produces consistent metadata structure."""
    # Run once
    result1 = generate_metadata_for_configuration(
        config=mock_config,
        raw_data_path=mock_raw_data,
        output_dir=mock_output_dir,
        seed=mock_config.seed
    )
    
    # Load content
    with open(result1["output_path"], 'r') as f:
        content1 = json.load(f)
    
    # Run again (overwrite)
    result2 = generate_metadata_for_configuration(
        config=mock_config,
        raw_data_path=mock_raw_data,
        output_dir=mock_output_dir,
        seed=mock_config.seed
    )
    
    with open(result2["output_path"], 'r') as f:
        content2 = json.load(f)
    
    # The content should be identical because the seed is the same
    assert content1 == content2, "Metadata should be deterministic for the same seed"