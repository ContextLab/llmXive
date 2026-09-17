import os
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil
import hashlib

from code.utils.data_loader import (
    validate_episode,
    load_schema,
    validate_checksum,
    compute_file_hash,
    compute_directory_hash,
    ensure_dirs,
    RAW_DATA_DIR,
    STATE_DIR,
    ARTIFACT_HASHES_FILE,
    VALID_DOMAINS
)

@pytest.fixture
def setup_test_env():
    """Create a temporary test environment."""
    # Create temporary directories
    test_raw_dir = Path(tempfile.mkdtemp()) / 'data' / 'raw'
    test_state_dir = Path(tempfile.mkdtemp()) / 'state'
    
    # Override global paths for testing
    global RAW_DATA_DIR, STATE_DIR, ARTIFACT_HASHES_FILE
    original_raw = RAW_DATA_DIR
    original_state = STATE_DIR
    original_hash_file = ARTIFACT_HASHES_FILE
    
    RAW_DATA_DIR = test_raw_dir
    STATE_DIR = test_state_dir
    ARTIFACT_HASHES_FILE = test_state_dir / 'artifact_hashes.yaml'
    
    ensure_dirs()
    
    yield {
        'raw_dir': test_raw_dir,
        'state_dir': test_state_dir,
        'hash_file': ARTIFACT_HASHES_FILE
    }
    
    # Cleanup
    RAW_DATA_DIR = original_raw
    STATE_DIR = original_state
    ARTIFACT_HASHES_FILE = original_hash_file
    shutil.rmtree(test_raw_dir.parent)
    shutil.rmtree(test_state_dir.parent)

@pytest.fixture
def valid_episode():
    """Create a valid test episode."""
    return {
        'leak-target': 'allowed',
        'roles': ['doctor', 'nurse'],
        'domains': ['medical'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }

@pytest.fixture
def invalid_domain_episode():
    """Create an episode with invalid domain."""
    return {
        'leak-target': 'allowed',
        'roles': ['doctor'],
        'domains': ['invalid_domain'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }

@pytest.fixture
def invalid_role_episode():
    """Create an episode with invalid role format."""
    return {
        'leak-target': 'allowed',
        'roles': ['doctor@invalid'],
        'domains': ['medical'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }

@pytest.fixture
def missing_field_episode():
    """Create an episode with missing required field."""
    return {
        'leak-target': 'allowed',
        'roles': ['doctor'],
        'domains': ['medical'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5}
        # Missing 'covariates'
    }

def test_validate_episode_valid(setup_test_env, valid_episode):
    """Test validation of a valid episode."""
    schema = load_schema()
    result = validate_episode(valid_episode, schema)
    assert result is True

def test_validate_episode_invalid_domain(setup_test_env, invalid_domain_episode):
    """Test validation rejects invalid domain."""
    schema = load_schema()
    result = validate_episode(invalid_domain_episode, schema)
    assert result is False

def test_validate_episode_invalid_role(setup_test_env, invalid_role_episode):
    """Test validation rejects invalid role format."""
    schema = load_schema()
    result = validate_episode(invalid_role_episode, schema)
    assert result is False

def test_validate_episode_missing_field(setup_test_env, missing_field_episode):
    """Test validation rejects missing required field."""
    schema = load_schema()
    result = validate_episode(missing_field_episode, schema)
    assert result is False

def test_validate_checksum_first_run(setup_test_env):
    """Test checksum validation on first run (no checksum file)."""
    # Ensure no checksum file exists
    if ARTIFACT_HASHES_FILE.exists():
        ARTIFACT_HASHES_FILE.unlink()
    
    # Should return True without raising
    result = validate_checksum()
    assert result is True

def test_validate_checksum_mismatch(setup_test_env):
    """Test checksum validation raises on mismatch."""
    # Create a dummy file in raw data
    dummy_file = RAW_DATA_DIR / 'dummy.jsonl'
    dummy_file.write_text('{"test": 1}\n')
    
    # Create checksum file with wrong hash
    wrong_hash = "0" * 64
    with open(ARTIFACT_HASHES_FILE, 'w') as f:
        yaml.dump({'gatemem_test': wrong_hash}, f)
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="Checksum mismatch"):
        validate_checksum()

def test_validate_checksum_match(setup_test_env):
    """Test checksum validation passes on match."""
    # Create a dummy file in raw data
    dummy_file = RAW_DATA_DIR / 'dummy.jsonl'
    dummy_file.write_text('{"test": 1}\n')
    
    # Compute correct hash
    correct_hash = compute_directory_hash(RAW_DATA_DIR)
    
    # Create checksum file with correct hash
    with open(ARTIFACT_HASHES_FILE, 'w') as f:
        yaml.dump({'gatemem_test': correct_hash}, f)
    
    # Should return True
    result = validate_checksum()
    assert result is True

def test_compute_file_hash(setup_test_env):
    """Test file hash computation."""
    test_file = RAW_DATA_DIR / 'test.txt'
    content = "test content"
    test_file.write_text(content)
    
    computed_hash = compute_file_hash(test_file)
    
    # Verify against hashlib
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    assert computed_hash == expected_hash

def test_compute_directory_hash(setup_test_env):
    """Test directory hash computation."""
    file1 = RAW_DATA_DIR / 'file1.txt'
    file2 = RAW_DATA_DIR / 'file2.txt'
    
    file1.write_text("content1")
    file2.write_text("content2")
    
    dir_hash = compute_directory_hash(RAW_DATA_DIR)
    
    # Verify it's a valid SHA256 hash
    assert len(dir_hash) == 64
    assert all(c in '0123456789abcdef' for c in dir_hash)

def test_validate_episode_multiple_domains(setup_test_env):
    """Test validation with multiple domains."""
    episode = {
        'leak-target': 'allowed',
        'roles': ['doctor'],
        'domains': ['medical', 'office'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }
    
    schema = load_schema()
    result = validate_episode(episode, schema)
    assert result is True

def test_validate_episode_single_domain_as_string(setup_test_env):
    """Test validation with domain as string instead of list."""
    episode = {
        'leak-target': 'allowed',
        'roles': ['doctor'],
        'domains': 'medical',
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }
    
    schema = load_schema()
    result = validate_episode(episode, schema)
    assert result is True

def test_validate_episode_single_role_as_string(setup_test_env):
    """Test validation with role as string instead of list."""
    episode = {
        'leak-target': 'allowed',
        'roles': 'doctor',
        'domains': ['medical'],
        'outcome': {'success': True},
        'predictors': {'feature1': 0.5},
        'covariates': {'age': 30}
    }
    
    schema = load_schema()
    result = validate_episode(episode, schema)
    assert result is True
