"""
Unit tests for T024: save_model_artifact.py

Tests verify that the model artifact is saved correctly with proper metadata
and the FR-007 disclaimer.
"""
import os
import sys
import json
import pickle
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.errors import PipelineError
from modeling.save_model_artifact import (
    load_trained_model,
    add_metadata,
    save_final_model,
    MODEL_DISCLAIMER
)

@pytest.fixture
def temp_model_data():
    """Create a temporary model dictionary for testing."""
    return {
        "model": "MockRandomForestModel",
        "training_metrics": {"r2": 0.45, "mae": 12.3},
        "metadata": {
            "training_date": "2023-10-01",
            "hyperparameters": {"max_depth": 10, "n_estimators": 100}
        }
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_trained_model_success(temp_dir, temp_model_data):
    """Test successful loading of a model file."""
    model_path = temp_dir / "test_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(temp_model_data, f)
    
    loaded_data = load_trained_model(model_path)
    assert loaded_data["model"] == "MockRandomForestModel"
    assert loaded_data["training_metrics"]["r2"] == 0.45

def test_load_trained_model_file_not_found(temp_dir):
    """Test that loading a non-existent file raises PipelineError."""
    non_existent_path = temp_dir / "non_existent.pkl"
    with pytest.raises(PipelineError) as exc_info:
        load_trained_model(non_existent_path)
    assert "not found" in str(exc_info.value)

def test_add_metadata_adds_disclaimer(temp_model_data):
    """Test that metadata is added including the FR-007 disclaimer."""
    updated_data = add_metadata(temp_model_data)
    
    assert "metadata" in updated_data
    assert "disclaimer" in updated_data["metadata"]
    assert MODEL_DISCLAIMER in updated_data["metadata"]["disclaimer"]
    assert "saved_timestamp" in updated_data["metadata"]
    assert "artifact_version" in updated_data["metadata"]
    assert updated_data["metadata"]["task_id"] == "T024"

def test_add_metadata_preserves_existing_metadata(temp_model_data):
    """Test that existing metadata is preserved when adding new fields."""
    original_training_date = temp_model_data["metadata"]["training_date"]
    updated_data = add_metadata(temp_model_data)
    
    assert updated_data["metadata"]["training_date"] == original_training_date
    assert updated_data["metadata"]["hyperparameters"]["max_depth"] == 10

def test_add_metadata_creates_metadata_if_missing():
    """Test that metadata dict is created if it doesn't exist."""
    model_data_no_meta = {"model": "MockModel", "data": [1, 2, 3]}
    updated_data = add_metadata(model_data_no_meta)
    
    assert "metadata" in updated_data
    assert "disclaimer" in updated_data["metadata"]

def test_save_final_model_creates_files(temp_dir, temp_model_data):
    """Test that save_final_model creates both .pkl and .json files."""
    model_data = add_metadata(temp_model_data)
    output_path = temp_dir / "model.pkl"
    metadata_path = temp_dir / "model_metadata.json"
    
    save_final_model(model_data, output_path, metadata_path)
    
    assert output_path.exists()
    assert metadata_path.exists()
    
    # Verify contents
    with open(output_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model["model"] == "MockRandomForestModel"
    
    with open(metadata_path, 'r') as f:
        loaded_meta = json.load(f)
    assert loaded_meta["disclaimer"] == MODEL_DISCLAIMER

def test_save_final_model_creates_parent_directory(temp_dir, temp_model_data):
    """Test that save_final_model creates parent directories if needed."""
    model_data = add_metadata(temp_model_data)
    nested_output = temp_dir / "subdir" / "nested" / "model.pkl"
    nested_meta = temp_dir / "subdir" / "nested" / "model_metadata.json"
    
    save_final_model(model_data, nested_output, nested_meta)
    
    assert nested_output.exists()
    assert nested_meta.exists()

def test_model_disclaimer_content():
    """Test that the disclaimer contains required keywords."""
    assert "associational" in MODEL_DISCLAIMER.lower()
    assert "causal" in MODEL_DISCLAIMER.lower()
    assert "experimental validation" in MODEL_DISCLAIMER.lower()