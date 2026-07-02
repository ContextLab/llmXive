"""
Unit tests for the state manager module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import yaml

import pytest

# We need to temporarily override PROJECT_ROOT for testing
# We'll use a fixture to set up a temporary directory structure

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root with required directories."""
    # Create the directory structure expected by config
    data_dirs = ["data/raw", "data/processed", "data/generated", "data/validation", "code", "tests"]
    for d in data_dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    
    # Create a dummy config.py that uses this temp root
    config_content = f"""
import os
from pathlib import Path

PROJECT_ROOT = Path(r"{tmp_path}")
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
DATA_VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"

def set_global_seed(seed=42):
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
"""
    (tmp_path / "code" / "config.py").write_text(config_content)
    
    return tmp_path


def test_initialize_state_file(temp_project_root):
    """Test that initialize_state_file creates a valid state.yaml."""
    # Import after setting up temp root
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    # Temporarily override the module's path
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    try:
        state_manager.initialize_state_file()
        
        state_file = temp_project_root / "state.yaml"
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        assert "version" in state
        assert state["version"] == "1.0"
        assert "created_at" in state
        assert "updated_at" in state
        assert "artifacts" in state
        assert isinstance(state["artifacts"], dict)
    finally:
        state_manager.STATE_FILE_PATH = original_path


def test_register_artifact(temp_project_root):
    """Test registering an artifact."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    # Initialize state first
    state_manager.initialize_state_file()
    
    # Create a dummy artifact
    artifact_path = temp_project_root / "data" / "processed" / "test_file.csv"
    artifact_path.write_text("col1,col2\n1,2\n3,4")
    
    try:
        state_manager.register_artifact(
            artifact_path, 
            "dataset", 
            "Test dataset",
            "T005"
        )
        
        state_file = temp_project_root / "state.yaml"
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        relative_path = "data/processed/test_file.csv"
        assert relative_path in state["artifacts"]
        
        artifact_info = state["artifacts"][relative_path]
        assert artifact_info["type"] == "dataset"
        assert artifact_info["description"] == "Test dataset"
        assert artifact_info["source_task_id"] == "T005"
        assert "hash" in artifact_info
        assert "size_bytes" in artifact_info
        assert artifact_info["size_bytes"] > 0
    finally:
        state_manager.STATE_FILE_PATH = original_path


def test_verify_artifact_valid(temp_project_root):
    """Test verifying a valid artifact."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    state_manager.initialize_state_file()
    
    artifact_path = temp_project_root / "data" / "processed" / "verify_test.csv"
    artifact_path.write_text("test,data\nhello,world")
    
    try:
        state_manager.register_artifact(artifact_path, "test_file")
        assert state_manager.verify_artifact(artifact_path) is True
    finally:
        state_manager.STATE_FILE_PATH = original_path


def test_verify_artifact_modified(temp_project_root):
    """Test verifying a modified artifact returns False."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    state_manager.initialize_state_file()
    
    artifact_path = temp_project_root / "data" / "processed" / "modify_test.csv"
    artifact_path.write_text("original")
    
    try:
        state_manager.register_artifact(artifact_path, "test_file")
        
        # Modify the file
        artifact_path.write_text("modified")
        
        assert state_manager.verify_artifact(artifact_path) is False
    finally:
        state_manager.STATE_FILE_PATH = original_path


def test_verify_artifact_missing(temp_project_root):
    """Test verifying a missing artifact returns False."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    state_manager.initialize_state_file()
    
    artifact_path = temp_project_root / "data" / "processed" / "nonexistent.csv"
    
    assert state_manager.verify_artifact(artifact_path) is False
    state_manager.STATE_FILE_PATH = original_path


def test_list_registered_artifacts(temp_project_root):
    """Test listing registered artifacts."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    state_manager.initialize_state_file()
    
    artifact1 = temp_project_root / "data" / "processed" / "art1.csv"
    artifact1.write_text("data1")
    
    artifact2 = temp_project_root / "data" / "generated" / "art2.csv"
    artifact2.write_text("data2")
    
    try:
        state_manager.register_artifact(artifact1, "dataset")
        state_manager.register_artifact(artifact2, "generated")
        
        artifacts = state_manager.list_registered_artifacts()
        
        assert len(artifacts) == 2
        assert "data/processed/art1.csv" in artifacts
        assert "data/generated/art2.csv" in artifacts
    finally:
        state_manager.STATE_FILE_PATH = original_path


def test_load_state_nonexistent_file(temp_project_root):
    """Test loading state when file doesn't exist."""
    import sys
    sys.path.insert(0, str(temp_project_root / "code"))
    
    import code.state_manager as state_manager
    original_path = state_manager.STATE_FILE_PATH
    state_manager.STATE_FILE_PATH = temp_project_root / "state.yaml"
    
    try:
        state = state_manager.load_state()
        
        assert "version" in state
        assert state["version"] == "1.0"
        assert "artifacts" in state
        assert state["artifacts"] == {}
    finally:
        state_manager.STATE_FILE_PATH = original_path