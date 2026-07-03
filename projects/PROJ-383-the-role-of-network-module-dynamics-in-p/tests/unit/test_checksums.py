import pytest
import tempfile
import json
from pathlib import Path
import hashlib

# Import the functions we want to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksums import (
    compute_file_checksum,
    compute_directory_checksum,
    save_checksums,
    load_checksums,
    verify_checksums,
    initialize_data_directories,
    generate_checksum_manifest,
    CHECKSUM_MANIFEST_FILE
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data layout."""
    # Create subdirectories
    for subdir in ["raw_fmri", "raw_behavior", "processed", "results"]:
        (tmp_path / subdir).mkdir(parents=True)
        # Add a test file
        test_file = tmp_path / subdir / "test_file.txt"
        test_file.write_text(f"Test content for {subdir}")
    return tmp_path

def test_compute_file_checksum():
    """Test that file checksums are computed correctly."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    checksum = compute_file_checksum(temp_path)
    
    # Verify it's a valid hex string
    assert len(checksum) == 64  # SHA256 produces 64 hex chars
    
    # Verify it matches expected hash
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected

def test_compute_directory_checksum(temp_data_dir):
    """Test directory checksum computation."""
    checksums = compute_directory_checksum(temp_data_dir)
    
    assert len(checksums) == 4  # One file per subdirectory
    
    # Verify all values are hex strings
    for rel_path, checksum in checksums.items():
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

def test_save_and_load_checksums(temp_data_dir, tmp_path):
    """Test saving and loading checksums to/from JSON."""
    checksums = compute_directory_checksum(temp_data_dir)
    output_path = tmp_path / "test_manifest.json"
    
    save_checksums(checksums, output_path)
    
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded == checksums

def test_initialize_data_directories(tmp_path):
    """Test that directory initialization creates the correct structure."""
    # Temporarily override the DATA_ROOT for testing
    import utils.checksums
    original_root = utils.checksums.DATA_ROOT
    utils.checksums.DATA_ROOT = tmp_path
    
    try:
        initialize_data_directories()
        
        for subdir in ["raw_fmri", "raw_behavior", "processed", "results"]:
            dir_path = tmp_path / subdir
            assert dir_path.exists()
            assert dir_path.is_dir()
            # Check for .gitkeep
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists()
    finally:
        utils.checksums.DATA_ROOT = original_root

def test_verify_checksums_success(temp_data_dir, tmp_path):
    """Test successful checksum verification."""
    # Create a manifest
    checksums = compute_directory_checksum(temp_data_dir)
    manifest_path = tmp_path / "manifest.json"
    save_checksums(checksums, manifest_path)
    
    # Temporarily override paths for testing
    import utils.checksums
    original_root = utils.checksums.DATA_ROOT
    original_manifest = utils.checksums.CHECKSUM_MANIFEST_FILE
    
    try:
        utils.checksums.DATA_ROOT = temp_data_dir
        utils.checksums.CHECKSUM_MANIFEST_FILE = manifest_path
        
        result = verify_checksums(manifest_path)
        assert result is True
    finally:
        utils.checksums.DATA_ROOT = original_root
        utils.checksums.CHECKSUM_MANIFEST_FILE = original_manifest

def test_verify_checksums_failure(temp_data_dir, tmp_path):
    """Test checksum verification with a modified file."""
    # Create a manifest
    checksums = compute_directory_checksum(temp_data_dir)
    manifest_path = tmp_path / "manifest.json"
    save_checksums(checksums, manifest_path)
    
    # Modify a file
    test_file = temp_data_dir / "raw_fmri" / "test_file.txt"
    test_file.write_text("Modified content")
    
    # Temporarily override paths for testing
    import utils.checksums
    original_root = utils.checksums.DATA_ROOT
    original_manifest = utils.checksums.CHECKSUM_MANIFEST_FILE
    
    try:
        utils.checksums.DATA_ROOT = temp_data_dir
        utils.checksums.CHECKSUM_MANIFEST_FILE = manifest_path
        
        result = verify_checksums(manifest_path)
        assert result is False
    finally:
        utils.checksums.DATA_ROOT = original_root
        utils.checksums.CHECKSUM_MANIFEST_FILE = original_manifest

def test_generate_checksum_manifest(temp_data_dir, tmp_path):
    """Test manifest generation."""
    import utils.checksums
    original_root = utils.checksums.DATA_ROOT
    
    try:
        utils.checksums.DATA_ROOT = temp_data_dir
        
        manifest = generate_checksum_manifest()
        
        assert len(manifest) == 4
        for subdir in ["raw_fmri", "raw_behavior", "processed", "results"]:
            assert subdir in manifest
            assert isinstance(manifest[subdir], dict)
    finally:
        utils.checksums.DATA_ROOT = original_root
