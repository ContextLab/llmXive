import os
import json
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

from extract_features import save_features

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

def test_save_features_creates_files(temp_output_dir):
    """Test that save_features creates features.npy and metadata.json."""
    # Prepare mock data
    latent_data = {
        "clip_001": np.random.rand(10, 128),
        "clip_002": np.random.rand(5, 128)
    }
    mask_data = {
        "clip_001": np.random.randint(0, 2, (10, 32)),
        "clip_002": np.random.randint(0, 2, (5, 32))
    }
    metadata = {
        "model_name": "test-model",
        "stats": {"total_clips": 2}
    }

    # Call function
    save_features(
        features_dir=temp_output_dir,
        latent_data=latent_data,
        mask_data=mask_data,
        metadata=metadata
    )

    # Verify files exist
    features_path = os.path.join(temp_output_dir, "features.npy")
    metadata_path = os.path.join(temp_output_dir, "metadata.json")

    assert os.path.exists(features_path), "features.npy was not created"
    assert os.path.exists(metadata_path), "metadata.json was not created"

    # Verify content integrity
    loaded_data = np.load(features_path, allow_pickle=True).item()
    assert "clip_001" in loaded_data
    assert "clip_002" in loaded_data
    assert np.array_equal(loaded_data["clip_001"]["latent"], latent_data["clip_001"])
    assert np.array_equal(loaded_data["clip_001"]["mask"], mask_data["clip_001"])

    with open(metadata_path, 'r') as f:
        loaded_metadata = json.load(f)
    assert loaded_metadata["model_name"] == "test-model"
    assert loaded_metadata["stats"]["total_clips"] == 2

def test_save_features_empty_data(temp_output_dir):
    """Test that save_features handles empty data gracefully."""
    save_features(
        features_dir=temp_output_dir,
        latent_data={},
        mask_data={},
        metadata={"status": "empty"}
    )

    features_path = os.path.join(temp_output_dir, "features.npy")
    metadata_path = os.path.join(temp_output_dir, "metadata.json")

    assert os.path.exists(features_path)
    assert os.path.exists(metadata_path)
    
    loaded_data = np.load(features_path, allow_pickle=True).item()
    assert len(loaded_data) == 0