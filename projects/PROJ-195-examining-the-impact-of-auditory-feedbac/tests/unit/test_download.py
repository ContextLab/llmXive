import os
import sys
import tempfile
import hashlib
from pathlib import Path
import json

# We need to import the main logic. Since download.py is in code/,
# we add the code directory to path.
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download import calculate_sha256, get_available_space, parse_gitattributes

def test_calculate_sha256():
    """Test SHA256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    
    try:
        sha = calculate_sha256(temp_path)
        # Calculate expected hash for "test data"
        expected = hashlib.sha256(b"test data").hexdigest()
        assert sha == expected
    finally:
        os.unlink(temp_path)

def test_get_available_space():
    """Test space check returns a positive number."""
    space = get_available_space(".")
    assert space > 0
    assert isinstance(space, int)

def test_parse_gitattributes_empty():
    """Test parsing an empty gitattributes file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gitattributes', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        # Test parsing an empty file returns empty list
        result = parse_gitattributes(temp_path)
        assert result == []
    finally:
        os.unlink(temp_path)

def test_parse_gitattributes_with_entries():
    """Test parsing a gitattributes file with entries."""
    content = """
    *.nii.gz filter=lfs diff=lfs merge=lfs -text
    *.tsv filter=lfs diff=lfs merge=lfs -text
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gitattributes', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        result = parse_gitattributes(temp_path)
        # Should find at least the .nii.gz and .tsv entries
        assert len(result) >= 2
        # Check specific patterns
        patterns = [entry['pattern'] for entry in result]
        assert '*.nii.gz' in patterns
        assert '*.tsv' in patterns
    finally:
        os.unlink(temp_path)

def test_download_structure():
    """Verify that download.py exists and has main function."""
    download_path = Path(__file__).parent.parent / "code" / "download.py"
    assert download_path.exists()
    
    # Check if it can be imported without error (syntax check)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("download", download_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main')
    except Exception as e:
        raise AssertionError(f"Failed to import download.py: {e}")

def test_sha256_mismatch_detection():
    """Test that SHA256 mismatch is detected."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"original content")
        temp_path = f.name
    
    try:
        sha = calculate_sha256(temp_path)
        # Modify file content
        with open(temp_path, 'wb') as f:
            f.write(b"modified content")
        
        sha_after = calculate_sha256(temp_path)
        assert sha != sha_after
    finally:
        os.unlink(temp_path)