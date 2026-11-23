import pytest
import yaml
import os
from pathlib import Path
import sys

# Add code to path for imports if running from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_state import create_state_structure

def test_state_directory_created():
    """Test that the state/projects directory is created."""
    create_state_structure()
    assert Path("state/projects").exists()

def test_project_yaml_created():
    """Test that the specific project YAML file is created."""
    project_id = "PROJ-122-identifying-structure-property-relations"
    create_state_structure(project_id)
    
    file_path = Path("state/projects") / f"{project_id}.yaml"
    assert file_path.exists()
    
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["project_id"] == project_id
    assert "created_at" in data
    assert data["status"] == "initialized"
    assert "artifacts" in data
    assert "checksums" in data

def test_project_yaml_structure():
    """Test that the YAML file contains the expected keys."""
    project_id = "PROJ-122-identifying-structure-property-relations"
    create_state_structure(project_id)
    
    file_path = Path("state/projects") / f"{project_id}.yaml"
    
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    required_keys = ["project_id", "created_at", "status", "artifacts", "checksums", "logs"]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    
    # Check artifacts structure
    required_artifacts = ["raw_data", "processed_data", "features", "models", "reports"]
    for artifact_key in required_artifacts:
        assert artifact_key in data["artifacts"]