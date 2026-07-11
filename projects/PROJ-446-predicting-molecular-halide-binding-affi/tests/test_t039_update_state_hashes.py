"""
Tests for T039: Update state.yaml with final artifact hashes.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.state_manager import (
    load_state_yaml,
    get_project_state_path,
    calculate_file_hash
)

def test_state_yaml_exists():
    """Test that state.yaml exists after T039 execution."""
    state_path = get_project_state_path()
    assert state_path.exists(), "state.yaml should exist after T039"

def test_state_yaml_structure():
    """Test that state.yaml has the required structure."""
    state_path = get_project_state_path()
    state = load_state_yaml(state_path)
    
    assert state is not None, "state.yaml should be loadable"
    assert "artifacts" in state, "state.yaml should contain 'artifacts' key"
    assert isinstance(state["artifacts"], dict), "'artifacts' should be a dictionary"

def test_artifacts_have_hashes():
    """Test that all artifacts have valid SHA-256 hashes."""
    state_path = get_project_state_path()
    state = load_state_yaml(state_path)
    
    artifacts = state.get("artifacts", {})
    assert len(artifacts) > 0, "There should be at least one artifact"
    
    for path, hash_val in artifacts.items():
        assert isinstance(hash_val, str), f"Hash for {path} should be a string"
        assert len(hash_val) == 64, f"Hash for {path} should be 64 characters (SHA-256)"
        assert all(c in '0123456789abcdef' for c in hash_val.lower()), \
            f"Hash for {path} should be hexadecimal"

def test_known_artifacts_present():
    """Test that expected artifacts are present in state.yaml."""
    state_path = get_project_state_path()
    state = load_state_yaml(state_path)
    
    artifacts = state.get("artifacts", {})
    
    # Check for critical artifacts
    expected_artifacts = [
        "code",
        "data/processed",
    ]
    
    found_artifacts = set(artifacts.keys())
    
    for expected in expected_artifacts:
        # Check if the artifact or a path starting with it exists
        matches = [a for a in found_artifacts if a == expected or a.startswith(expected + "/")]
        if not matches:
            pytest.fail(f"Expected artifact '{expected}' not found in state.yaml. "
                      f"Found: {list(found_artifacts)}")

def test_hash_consistency():
    """Test that hashes are consistent with actual file contents."""
    state_path = get_project_state_path()
    state = load_state_yaml(state_path)
    
    artifacts = state.get("artifacts", {})
    
    for rel_path, stored_hash in artifacts.items():
        full_path = PROJECT_ROOT / rel_path
        
        if full_path.is_file():
            computed_hash = calculate_file_hash(full_path)
            assert computed_hash.lower() == stored_hash.lower(), \
                f"Hash mismatch for {rel_path}: stored={stored_hash}, computed={computed_hash}"

def test_state_yaml_is_valid_yaml():
    """Test that state.yaml is valid YAML."""
    state_path = get_project_state_path()
    
    with open(state_path, 'r') as f:
        try:
            content = yaml.safe_load(f)
            assert content is not None, "state.yaml should not be empty"
        except yaml.YAMLError as e:
            pytest.fail(f"state.yaml is not valid YAML: {e}")