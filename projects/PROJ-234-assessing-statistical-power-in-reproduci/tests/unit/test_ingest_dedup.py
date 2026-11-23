"""
Unit tests for T014: Deduplication and Checksum generation logic.
"""
import json
import hashlib
import tempfile
import os
from pathlib import Path
import pytest

# Import the functions to test from the script module
# Note: In a real environment, this would be from code.01_ingest_openml
# but for unit testing isolated logic, we often import the functions directly.
# Since the script defines them at module level, we can import them.
import sys
import importlib.util

# Load the module from the code directory
spec = importlib.util.spec_from_file_location(
    "ingest_module", 
    Path(__file__).parent.parent.parent / "code" / "01_ingest_openml.py"
)
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)

filter_datasets = ingest_module.filter_datasets
deduplicate_datasets = ingest_module.deduplicate_datasets
generate_checksums = ingest_module.generate_checksums


def test_filter_keeps_valid():
    """Test that filter_datasets keeps entries with link OR task_id."""
    data = [
        {"dataset_id": 1, "publication_link": "http://a.com", "task_id": None},
        {"dataset_id": 2, "publication_link": None, "task_id": 100},
        {"dataset_id": 3, "publication_link": None, "task_id": None}, # Should drop
        {"dataset_id": 4, "publication_link": "", "task_id": 200}, # Empty link, has task -> keep
    ]
    
    result = filter_datasets(data)
    assert len(result) == 3
    ids = [r["dataset_id"] for r in result]
    assert 3 not in ids
    assert 1 in ids
    assert 2 in ids
    assert 4 in ids


def test_deduplicate_keeps_highest_count():
    """Test T014: Deduplication keeps highest download_count."""
    data = [
        {"dataset_id": 101, "download_count": 50, "name": "A"},
        {"dataset_id": 101, "download_count": 200, "name": "B"}, # Higher count
        {"dataset_id": 101, "download_count": 10, "name": "C"},  # Lower count
        {"dataset_id": 102, "download_count": 30, "name": "D"},
    ]
    
    result = deduplicate_datasets(data)
    assert len(result) == 2
    
    # Find entry for 101
    entry_101 = next((r for r in result if r["dataset_id"] == 101), None)
    assert entry_101 is not None
    assert entry_101["name"] == "B"
    assert entry_101["download_count"] == 200


def test_deduplicate_handles_none_counts():
    """Test that None download_count is treated as 0."""
    data = [
        {"dataset_id": 201, "download_count": None, "name": "A"},
        {"dataset_id": 201, "download_count": 0, "name": "B"},
        {"dataset_id": 201, "download_count": 10, "name": "C"},
    ]
    
    result = deduplicate_datasets(data)
    entry = next(r for r in result if r["dataset_id"] == 201)
    assert entry["name"] == "C"


def test_checksum_generation():
    """Test that checksums are generated correctly and written to file."""
    data = [{"id": 1, "val": "test"}]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_path = Path(tmpdir) / "checksums.txt"
        generate_checksums(data, checksum_path)
        
        assert checksum_path.exists()
        
        content = checksum_path.read_text()
        # Verify format: "hash  filename\n"
        parts = content.split()
        assert len(parts) == 2
        assert parts[1] == "openml_metadata_filtered.json"
        
        # Verify hash correctness manually
        json_str = json.dumps(data, sort_keys=True, indent=2)
        expected_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
        assert parts[0] == expected_hash
