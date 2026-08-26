"""
Unit tests for environment configuration management.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import hashlib

# Import the modules under test
from config_env import (
    EnvConfig,
    get_env_config,
    reset_env_config,
    get_data_path,
    get_datasets_path,
    get_annotations_path,
    get_results_path,
    verify_dataset,
    register_artifact,
    ensure_env_paths_exist,
    get_env_config_summary
)
from utils.env_manager import EnvManager, get_env_manager, setup_environment, verify_environment

@pytest.fixture
def temp_env():
    """Create a temporary environment for testing."""
    # Save original config
    original_config = None
    if hasattr(get_env_config, '_env_config'):
        original_config = get_env_config._env_config
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Note: In real tests, we'd mock the path resolution
        # For now, we test the logic with available functions
        yield tmp_path
    
    # Restore original config
    if original_config:
        get_env_config._env_config = original_config
    else:
        reset_env_config()

def test_env_config_initialization():
    """Test EnvConfig initialization."""
    config = EnvConfig()
    assert config.data_root == Path("data")
    assert config.datasets_dir == Path("data/raw")
    assert config.annotations_dir == Path("data/annotations")
    assert config.results_dir == Path("data/results")
    assert config.artifacts_dir == Path("data/artifacts")
    assert config.hashes_file == Path("data/artifacts/artifact_hashes.json")

def test_hash_computation():
    """Test file hash computation."""
    config = EnvConfig()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content for hashing")
        temp_path = Path(f.name)
    
    try:
        # Compute hash
        hash_value = config._compute_file_hash(temp_path)
        
        # Verify it's a valid hex string
        assert len(hash_value) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in hash_value)
        
        # Verify determinism
        hash_value2 = config._compute_file_hash(temp_path)
        assert hash_value == hash_value2
    finally:
        temp_path.unlink()

def test_artifact_registration():
    """Test artifact registration and retrieval."""
    config = EnvConfig()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test artifact content")
        temp_path = Path(f.name)
    
    try:
        # Register artifact
        hash_value = config._compute_file_hash(temp_path)
        config.register_artifact("test_artifact", temp_path, hash_value)
        
        # Retrieve artifact info
        info = config.get_artifact_info("test_artifact")
        assert info is not None
        assert info["hash"] == hash_value
        assert info["path"] == str(temp_path)
        
        # Verify artifact
        assert config.verify_artifact("test_artifact", temp_path)
    finally:
        temp_path.unlink()

def test_artifact_verification_failure():
    """Test artifact verification with wrong path."""
    config = EnvConfig()
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)
    
    try:
        hash_value = config._compute_file_hash(temp_path)
        config.register_artifact("test_verify", temp_path, hash_value)
        
        # Try to verify with non-existent path
        fake_path = Path("/nonexistent/path")
        assert not config.verify_artifact("test_verify", fake_path)
    finally:
        temp_path.unlink()

def test_registry_persistence():
    """Test that registry is saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        hashes_file = Path(tmpdir) / "test_hashes.json"
        config = EnvConfig(hashes_file=hashes_file)
        
        # Create and register artifact
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"persistent test")
            temp_path = Path(f.name)
        
        try:
            hash_value = config._compute_file_hash(temp_path)
            config.register_artifact("persistent_artifact", temp_path, hash_value)
            
            # Create new config instance (simulating restart)
            config2 = EnvConfig(hashes_file=hashes_file)
            
            # Verify artifact is still registered
            assert config2.verify_artifact("persistent_artifact", temp_path)
        finally:
            temp_path.unlink()

def test_verify_dataset_function():
    """Test the verify_dataset convenience function."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"verify test content")
        temp_path = Path(f.name)
    
    try:
        # First call should register
        is_valid, error = verify_dataset("test_func_verify", temp_path)
        assert is_valid
        assert error is None
        
        # Second call should verify
        is_valid2, error2 = verify_dataset("test_func_verify", temp_path)
        assert is_valid2
        assert error2 is None
    finally:
        temp_path.unlink()

def test_env_paths_exist():
    """Test that ensure_env_paths_exist creates directories."""
    # This test verifies the function runs without error
    # Actual directory creation is tested in integration tests
    try:
        ensure_env_paths_exist()
    except Exception as e:
        pytest.fail(f"ensure_env_paths_exist raised: {e}")

def test_env_manager():
    """Test EnvManager basic functionality."""
    manager = EnvManager()
    
    # Test artifact report generation
    report = manager.get_artifact_report()
    assert "mode" in report
    assert "total_artifacts" in report
    assert "artifacts" in report

def test_setup_environment():
    """Test environment setup."""
    result = setup_environment()
    assert result["status"] == "initialized"

def test_verify_environment():
    """Test environment verification."""
    is_valid, report = verify_environment()
    assert isinstance(is_valid, bool)
    assert "total_artifacts" in report

def test_get_env_config_summary():
    """Test config summary generation."""
    summary = get_env_config_summary()
    assert "mode" in summary
    assert "data_root" in summary
    assert "registered_artifacts" in summary
    assert "total_artifacts" in summary
