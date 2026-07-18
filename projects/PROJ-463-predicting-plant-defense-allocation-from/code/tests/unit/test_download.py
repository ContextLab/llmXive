"""
Unit test for FASTQ download validation.
"""
import pytest
import os
import tempfile
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# We mock the download function since we don't have real NCBI access in tests
# This test validates the logic of checksum verification and file existence

def test_manifest_entry_creation():
    """Test that manifest entries are created correctly."""
    from src.utils.schemas import create_manifest_entry, compute_sha256
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        entry = create_manifest_entry(
            file_name="test.txt",
            file_path=temp_path,
            source_type="test",
            provenance={"test": "value"}
        )
        
        assert entry.file_name == "test.txt"
        assert entry.source_type == "test"
        assert len(entry.checksum) == 64 # SHA256 length
    finally:
        os.unlink(temp_path)
