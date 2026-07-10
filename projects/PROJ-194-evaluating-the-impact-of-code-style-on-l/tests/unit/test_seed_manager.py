"""
Unit tests for code/transform/seed_manager.py (Task T006).
Verifies Constitution Principle VI: Reproducibility.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to ensure the code/ directory is in the path if running from tests/
import sys
import importlib.util

# Dynamically load the module to avoid path issues during testing
spec = importlib.util.spec_from_file_location(
    "seed_manager",
    os.path.join(os.path.dirname(__file__), "..", "..", "code", "transform", "seed_manager.py")
)
seed_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_manager)

compute_mapping_hash = seed_manager.compute_mapping_hash
log_transform_seed = seed_manager.log_transform_seed
get_seed_entry = seed_manager.get_seed_entry
verify_reproducibility = seed_manager.verify_reproducibility
_ensure_data_dir = seed_manager._ensure_data_dir

@pytest.fixture
def temp_seed_log(tmp_path):
    """Create a temporary directory and set SEED_LOG_PATH for testing."""
    original_path = seed_manager.SEED_LOG_PATH
    original_data_dir = seed_manager.DATA_DIR
    
    temp_dir = str(tmp_path)
    temp_log = os.path.join(temp_dir, "transform_seeds.jsonl")
    
    # Monkey-patch the module's global constants
    seed_manager.DATA_DIR = temp_dir
    seed_manager.SEED_LOG_PATH = temp_log
    
    yield temp_log
    
    # Restore original values
    seed_manager.DATA_DIR = original_data_dir
    seed_manager.SEED_LOG_PATH = original_path

def test_compute_mapping_hash_deterministic():
    """Test that the hash is deterministic for the same mapping."""
    mapping = {"a": "1", "b": "2"}
    hash1 = compute_mapping_hash(mapping)
    hash2 = compute_mapping_hash(mapping)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length

def test_compute_mapping_hash_empty():
    """Test hash computation for an empty dictionary."""
    hash_val = compute_mapping_hash({})
    assert len(hash_val) == 64

def test_compute_mapping_hash_different():
    """Test that different mappings produce different hashes."""
    mapping1 = {"a": "1"}
    mapping2 = {"a": "2"}
    assert compute_mapping_hash(mapping1) != compute_mapping_hash(mapping2)

def test_log_transform_seed_creates_file(temp_seed_log):
    """Test that logging creates the file and writes a valid JSONL entry."""
    seed = 12345
    variant = "test_variant"
    
    result = log_transform_seed(seed, variant)
    
    assert os.path.exists(temp_seed_log)
    assert "identifier_mapping_hash" in result
    assert result["transform_seed"] == seed
    assert result["variant_type"] == variant
    
    # Verify file content
    with open(temp_seed_log, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["transform_seed"] == seed

def test_log_transform_seed_with_mapping(temp_seed_log):
    """Test logging with an identifier mapping computes the hash."""
    seed = 42
    variant = "naming_test"
    mapping = {"old_name": "new_name"}
    
    result = log_transform_seed(seed, variant, identifier_mapping=mapping)
    
    assert result["identifier_mapping_hash"] is not None
    assert result["identifier_mapping_hash"] == compute_mapping_hash(mapping)
    
    # Verify sample keys in metadata
    assert "mapping_sample" in result["metadata"]
    assert "old_name" in result["metadata"]["mapping_sample"]

def test_log_transform_seed_invalid_seed(temp_seed_log):
    """Test that non-integer seeds raise ValueError."""
    with pytest.raises(ValueError):
        log_transform_seed("not_an_int", "variant")

def test_get_seed_entry_found(temp_seed_log):
    """Test retrieving a logged entry."""
    seed = 999
    variant = "found_variant"
    log_transform_seed(seed, variant)
    
    entry = get_seed_entry(seed, variant)
    assert entry is not None
    assert entry["transform_seed"] == seed
    assert entry["variant_type"] == variant

def test_get_seed_entry_not_found(temp_seed_log):
    """Test retrieving a non-existent entry."""
    entry = get_seed_entry(12345, "non_existent")
    assert entry is None

def test_get_seed_entry_wrong_type(temp_seed_log):
    """Test retrieving with wrong variant type."""
    seed = 777
    variant = "type_a"
    log_transform_seed(seed, variant)
    
    entry = get_seed_entry(seed, "type_b")
    assert entry is None

def test_verify_reproducibility_success(temp_seed_log):
    """Test successful verification of seed and mapping."""
    seed = 555
    variant = "verify_test"
    mapping = {"x": "y"}
    
    log_transform_seed(seed, variant, identifier_mapping=mapping)
    
    assert verify_reproducibility(seed, mapping, variant) is True

def test_verify_reproducibility_wrong_hash(temp_seed_log):
    """Test verification failure with wrong mapping."""
    seed = 666
    variant = "verify_test"
    mapping = {"x": "y"}
    wrong_mapping = {"x": "z"}
    
    log_transform_seed(seed, variant, identifier_mapping=mapping)
    
    assert verify_reproducibility(seed, wrong_mapping, variant) is False

def test_verify_reproducibility_seed_not_found(temp_seed_log):
    """Test verification failure when seed is not logged."""
    mapping = {"x": "y"}
    assert verify_reproducibility(9999, mapping, "test") is False

def test_ensure_data_dir_creates_directory(tmp_path):
    """Test that _ensure_data_dir creates the directory."""
    new_dir = str(tmp_path / "new_data")
    with patch.object(seed_manager, 'DATA_DIR', new_dir):
        # Remove if exists
        if os.path.exists(new_dir):
            import shutil
            shutil.rmtree(new_dir)
        
        _ensure_data_dir()
        assert os.path.isdir(new_dir)