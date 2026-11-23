"""
Unit tests for the main pipeline orchestrator.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main_pipeline import (
    calculate_sha256,
    calculate_file_size,
    verify_artifacts_exist,
    generate_manifest,
    load_yaml_config,
    save_yaml_config,
    update_project_timestamp
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_sha256(temp_dir):
    """Test SHA-256 calculation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    actual_hash = calculate_sha256(test_file)
    
    assert actual_hash == expected_hash

def test_calculate_file_size(temp_dir):
    """Test file size calculation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    size = calculate_file_size(test_file)
    assert size == len(test_content)

def test_verify_artifacts_exist(temp_dir):
    """Test artifact verification."""
    existing_file = temp_dir / "existing.txt"
    existing_file.write_text("content")
    
    artifacts = [existing_file, temp_dir / "nonexistent.txt"]
    results = verify_artifacts_exist(artifacts)
    
    assert results["existing.txt"] is True
    assert results["nonexistent.txt"] is False

def test_generate_manifest(temp_dir):
    """Test manifest generation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    
    artifacts = [test_file]
    manifest = generate_manifest(artifacts, MagicMock())
    
    assert "generated_at" in manifest
    assert "project_id" in manifest
    assert "artifacts" in manifest
    assert "test.txt" in str(manifest["artifacts"])

def test_load_yaml_config(temp_dir):
    """Test YAML config loading."""
    config_file = temp_dir / "config.yaml"
    config_content = """
    section1:
      key1: value1
      key2: value2
    section2:
      key3: value3
    """
    config_file.write_text(config_content)
    
    config = load_yaml_config(config_file)
    
    assert "section1" in config
    assert config["section1"]["key1"] == "value1"
    assert config["section2"]["key3"] == "value3"

def test_save_yaml_config(temp_dir):
    """Test YAML config saving."""
    config_file = temp_dir / "config.yaml"
    config = {
        "section1": {"key1": "value1"},
        "section2": {"key2": "value2"}
    }
    
    save_yaml_config(config_file, config)
    
    assert config_file.exists()
    loaded_config = load_yaml_config(config_file)
    assert loaded_config["section1"]["key1"] == "value1"
    assert loaded_config["section2"]["key2"] == "value2"

def test_update_project_timestamp(temp_dir, monkeypatch):
    """Test project timestamp update."""
    # Mock the PROJECT_STATE_FILE path
    project_state_file = temp_dir / "projects" / "PROJ-1030-llmxive-follow-up-extending-scaling-mixt.yaml"
    project_state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Patch the global variable
    import main_pipeline
    original_state_file = main_pipeline.PROJECT_STATE_FILE
    main_pipeline.PROJECT_STATE_FILE = project_state_file
    
    try:
        update_project_timestamp()
        
        assert project_state_file.exists()
        config = load_yaml_config(project_state_file)
        assert "state" in config
        assert "updated_at" in config["state"]
    finally:
        main_pipeline.PROJECT_STATE_FILE = original_state_file