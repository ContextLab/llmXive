"""
Unit tests for model metadata functionality.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.model_metadata import (
    save_model_metadata,
    load_model_metadata,
    verify_dft_functional,
    embed_metadata_in_model,
    extract_metadata_from_model,
    EXPECTED_DFT_FUNCTIONAL
)
import pickle

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "dft_functional": "PBE",
        "model_type": "RandomForestRegressor",
        "feature_columns": ["tolerance_factor", "octahedral_factor"],
        "hyperparameters": {"max_depth": 15, "min_samples_leaf": 2},
        "training_stats": {"train_size": 5000, "test_rmse": 0.12}
    }

def test_save_and_load_metadata(temp_results_dir, sample_metadata):
    """Test saving and loading model metadata."""
    # Save metadata
    metadata_path = save_model_metadata(
        output_dir=temp_results_dir,
        dft_functional=sample_metadata["dft_functional"],
        model_type=sample_metadata["model_type"],
        feature_columns=sample_metadata["feature_columns"],
        hyperparameters=sample_metadata["hyperparameters"],
        training_stats=sample_metadata["training_stats"]
    )

    # Verify file exists
    assert metadata_path.exists()
    assert metadata_path.name == "model_metadata.json"

    # Load and verify
    loaded_metadata = load_model_metadata(temp_results_dir)
    assert loaded_metadata["dft_functional"] == "PBE"
    assert loaded_metadata["model_type"] == "RandomForestRegressor"
    assert loaded_metadata["feature_columns"] == sample_metadata["feature_columns"]
    assert loaded_metadata["hyperparameters"] == sample_metadata["hyperparameters"]
    assert loaded_metadata["training_stats"] == sample_metadata["training_stats"]

def test_verify_dft_functional_correct(temp_results_dir):
    """Test verification with correct DFT functional."""
    save_model_metadata(
        output_dir=temp_results_dir,
        dft_functional="PBE"
    )

    assert verify_dft_functional(temp_results_dir, "PBE") is True

def test_verify_dft_functional_wrong(temp_results_dir):
    """Test verification with incorrect DFT functional."""
    save_model_metadata(
        output_dir=temp_results_dir,
        dft_functional="LDA"  # Wrong functional
    )

    assert verify_dft_functional(temp_results_dir, "PBE") is False

def test_verify_dft_functional_missing(temp_results_dir):
    """Test verification when metadata file is missing."""
    # Don't create metadata file
    assert verify_dft_functional(temp_results_dir, "PBE") is False

def test_embed_and_extract_metadata(temp_results_dir):
    """Test embedding and extracting metadata from model."""
    # Create a dummy model object
    class DummyModel:
        pass

    model_path = Path(temp_results_dir) / "dummy_model.pkl"
    dummy_model = DummyModel()

    # Save dummy model
    with open(model_path, 'wb') as f:
        pickle.dump(dummy_model, f)

    # Embed metadata
    metadata = {"dft_functional": "PBE", "test_key": "test_value"}
    embed_metadata_in_model(str(model_path), metadata)

    # Extract and verify
    extracted = extract_metadata_from_model(str(model_path))
    assert extracted is not None
    assert extracted["dft_functional"] == "PBE"
    assert extracted["test_key"] == "test_value"

def test_extract_metadata_no_embedded(temp_results_dir):
    """Test extraction when no metadata is embedded."""
    # Create a dummy model without metadata
    class DummyModel:
        pass

    model_path = Path(temp_results_dir) / "dummy_model_no_meta.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(DummyModel(), f)

    # Extract should return None
    extracted = extract_metadata_from_model(str(model_path))
    assert extracted is None

def test_metadata_persistence(temp_results_dir):
    """Test that metadata persists across save/load cycles."""
    # Save metadata
    save_model_metadata(
        output_dir=temp_results_dir,
        dft_functional="PBE",
        model_type="RandomForestRegressor",
        hyperparameters={"max_depth": 20}
    )

    # Load multiple times
    for _ in range(3):
        loaded = load_model_metadata(temp_results_dir)
        assert loaded["dft_functional"] == "PBE"
        assert loaded["model_type"] == "RandomForestRegressor"
        assert loaded["hyperparameters"]["max_depth"] == 20
