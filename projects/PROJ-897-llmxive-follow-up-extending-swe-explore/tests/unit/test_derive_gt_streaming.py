"""
Unit tests for the streaming ground truth derivation logic.

These tests verify that the parsing logic works correctly on sample data
and that the streaming function signature is correct.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from data.derive_gt import (
    compute_sha256,
    parse_patch_basic,
    parse_patch_unidiff,
    derive_ground_truth
)

# Sample patch for testing
SAMPLE_PATCH = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,4 +1,5 @@
 def hello():
-    print("Hello")
+    print("Hello World")
+    return True
 
 def world():
     pass
"""

def test_compute_sha256():
    """Test SHA256 computation."""
    text = "test string"
    hash1 = compute_sha256(text)
    hash2 = compute_sha256(text)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    assert hash1 != compute_sha256("different string")

def test_parse_patch_basic():
    """Test basic patch parsing."""
    lines = parse_patch_basic(SAMPLE_PATCH)
    # The patch adds lines at 2 (modified) and 3 (new).
    # In the new file:
    # Line 1: def hello(): (context)
    # Line 2: + print("Hello World") (added)
    # Line 3: + return True (added)
    # Line 4: def world(): (context)
    # So we expect lines 2 and 3 to be marked.
    assert 2 in lines
    assert 3 in lines
    assert 1 not in lines
    assert 4 not in lines

def test_parse_patch_unidiff():
    """Test robust patch parsing."""
    lines = parse_patch_unidiff(SAMPLE_PATCH)
    assert 2 in lines
    assert 3 in lines

def test_parse_patch_empty():
    """Test parsing empty patch."""
    assert parse_patch_basic("") == []
    assert parse_patch_unidiff("") == []

def test_derive_ground_truth_success():
    """Test ground truth derivation with valid patch."""
    issue = {
        "issue_id": "test-001",
        "solution_patch": SAMPLE_PATCH
    }
    result = derive_ground_truth(issue)
    
    assert result["issue_id"] == "test-001"
    assert result["status"] == "success"
    assert len(result["ground_truth_lines"]) > 0

def test_derive_ground_truth_no_patch():
    """Test ground truth derivation with missing patch."""
    issue = {
        "issue_id": "test-002",
        "solution_patch": ""
    }
    result = derive_ground_truth(issue)
    
    assert result["issue_id"] == "test-002"
    assert result["status"] == "no_patch"
    assert result["ground_truth_lines"] == []

@patch('data.derive_gt.load_dataset')
@patch('data.derive_gt.open')
def test_stream_derive_gt_logic(mock_open, mock_load_dataset):
    """
    Test that the streaming function correctly iterates and writes.
    This is a logic test, not an integration test against HF.
    """
    from data.derive_gt import stream_derive_gt
    
    # Mock dataset iterator
    mock_record1 = {"issue_id": "1", "solution_patch": SAMPLE_PATCH}
    mock_record2 = {"issue_id": "2", "solution_patch": ""}
    mock_dataset = [mock_record1, mock_record2]
    
    mock_load_dataset.return_value.__iter__.return_value = iter(mock_dataset)
    
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        stream_derive_gt("fake_dataset", tmp_path)
        
        # Check that write was called twice
        assert mock_file.write.call_count == 2
        
        # Check the content of the writes
        calls = mock_file.write.call_args_list
        data1 = json.loads(calls[0][0][0])
        data2 = json.loads(calls[1][0][0])
        
        assert data1["issue_id"] == "1"
        assert data1["status"] == "success"
        
        assert data2["issue_id"] == "2"
        assert data2["status"] == "no_patch"
    finally:
        tmp_path.unlink()