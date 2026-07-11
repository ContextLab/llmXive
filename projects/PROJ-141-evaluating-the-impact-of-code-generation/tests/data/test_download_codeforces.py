"""
Tests for code/data/download_codeforces.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.download_codeforces import (
    compute_file_hash, 
    validate_json_structure, 
    save_metadata,
    DATA_DIR,
    METADATA_FILE
)

def test_compute_file_hash():
    """Test SHA-256 hash computation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"hello world")
        tmp_path = Path(tmp.name)
    
    try:
        hash_val = compute_file_hash(tmp_path)
        # Known hash for "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert hash_val == expected, f"Expected {expected}, got {hash_val}"
    finally:
        os.unlink(tmp_path)

def test_validate_json_structure_list():
    """Test validation with a list structure."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump([{"id": 1}, {"id": 2}], tmp)
        tmp_path = Path(tmp.name)
    
    try:
        assert validate_json_structure(tmp_path) is True
    finally:
        os.unlink(tmp_path)

def test_validate_json_structure_dict():
    """Test validation with a dict structure containing 'problems'."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump({"problems": [{"id": 1}]}, tmp)
        tmp_path = Path(tmp.name)
    
    try:
        assert validate_json_structure(tmp_path) is True
    finally:
        os.unlink(tmp_path)

def test_validate_json_structure_invalid():
    """Test validation with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write("not json")
        tmp_path = Path(tmp.name)
    
    try:
        assert validate_json_structure(tmp_path) is False
    finally:
        os.unlink(tmp_path)

def test_save_metadata():
    """Test metadata saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy file to hash
        dummy_file = Path(tmpdir) / "dummy.json"
        dummy_file.write_text("test")
        
        metadata_path = Path(tmpdir) / "metadata.json"
        
        # Mock the function to use our temp path
        # We can't easily override the global METADATA_FILE, so we test the logic
        # by calling save_metadata and checking the file it creates
        # Note: The actual function writes to a global METADATA_FILE.
        # For strict unit testing, we might need to refactor to pass paths,
        # but here we verify the file creation and content structure.
        
        # Temporarily override global for this test
        original_path = METADATA_FILE
        # We can't easily change the global inside the module without re-import or patching
        # Instead, we rely on the fact that the function creates the file.
        # We will patch the module's METADATA_FILE variable if possible, 
        # or just check that the function runs without error in the temp dir context.
        
        # Let's just verify the function runs and creates a valid JSON file
        # by temporarily changing the global in the module namespace
        import data.download_codeforces as mod
        mod.METADATA_FILE = metadata_path
        mod.DATA_DIR = Path(tmpdir) # Ensure directory exists
        
        try:
            save_metadata(dummy_file, "http://test.com", "v1", True)
            
            assert metadata_path.exists(), "Metadata file not created"
            
            with open(metadata_path, 'r') as f:
                meta = json.load(f)
            
            assert meta["dataset"] == "Codeforces Problems"
            assert meta["source_url"] == "http://test.com"
            assert meta["success"] is True
            assert "file_hash" in meta
            assert "download_timestamp" in meta
        finally:
            # Restore
            mod.METADATA_FILE = original_path
            mod.DATA_DIR = DATA_DIR