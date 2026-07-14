"""
Unit tests for code/data/derive_gt.py
"""

import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.derive_gt import derive_ground_truth, parse_patch_unidiff, compute_sha256


def test_compute_sha256():
    """Test SHA256 computation."""
    content = "hello world"
    # Pre-calculated hash for "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert compute_sha256(content) == expected


def test_parse_patch_simple_deletion():
    """Test parsing a patch with a simple deletion."""
    original = "line1\nline2\nline3\n"
    patch = """--- a/file.py
    +++ b/file.py
    @@ -1,3 +1,2 @@
     line1
    -line2
     line3
    """
    lines = parse_patch_unidiff(patch, original.splitlines())
    # line2 is at index 1 (1-based: 2)
    assert 2 in lines
    assert len(lines) == 1


def test_parse_patch_simple_addition():
    """Test parsing a patch with a simple addition."""
    original = "line1\nline2\n"
    patch = """--- a/file.py
    +++ b/file.py
    @@ -1,2 +1,3 @@
     line1
    +line_new
     line2
    """
    lines = parse_patch_unidiff(patch, original.splitlines())
    # The addition happens at line 1 (after line1, before line2)
    # Our logic maps insertion to the context line (1) or 2?
    # In the test logic: if current_orig_line < len, add current_orig_line + 1.
    # Context: "line1" is at index 0. current_orig_line starts at 0.
    # Insertion: adds 0 + 1 = 1.
    assert 1 in lines


def test_parse_patch_modification():
    """Test parsing a patch that modifies a line (delete + add)."""
    original = "line1\nline2\nline3\n"
    patch = """--- a/file.py
    +++ b/file.py
    @@ -1,3 +1,3 @@
     line1
    -line2
    +line2_modified
     line3
    """
    lines = parse_patch_unidiff(patch, original.splitlines())
    # Line 2 is deleted and a new one added at same spot.
    # We expect 2 to be in ground truth.
    assert 2 in lines
    assert len(lines) == 1


def test_derive_ground_truth_success():
    """Test full derivation on a valid record."""
    record = {
        "issue_id": "TEST-001",
        "file": "test.py",
        "original_file": "def foo():\n    pass\n",
        "patch": """--- a/test.py
        +++ b/test.py
        @@ -1,2 +1,3 @@
         def foo():
        +    x = 1
             pass
        """
    }
    
    result = derive_ground_truth(record)
    
    assert result is not None
    assert result["issue_id"] == "TEST-001"
    assert result["file_path"] == "test.py"
    assert "ground_truth_lines" in result
    assert "original_hash" in result
    assert "patch_hash" in result
    # The addition happens at line 1
    assert 1 in result["ground_truth_lines"]


def test_derive_ground_truth_no_patch():
    """Test derivation when patch is missing."""
    record = {
        "issue_id": "TEST-002",
        "file": "test.py",
        "original_file": "code",
        "patch": ""
    }
    
    result = derive_ground_truth(record)
    assert result is None


def test_derive_ground_truth_invalid_json():
    """Test derivation with missing ID."""
    record = {
        "file": "test.py",
        "patch": "diff..."
    }
    
    result = derive_ground_truth(record)
    assert result is None


def test_parse_patch_empty_hunk():
    """Test parsing a patch with no changes (should return empty)."""
    original = "line1\n"
    patch = """--- a/file.py
    +++ b/file.py
    @@ -1 +1 @@
     line1
    """
    lines = parse_patch_unidiff(patch, original.splitlines())
    assert lines == []