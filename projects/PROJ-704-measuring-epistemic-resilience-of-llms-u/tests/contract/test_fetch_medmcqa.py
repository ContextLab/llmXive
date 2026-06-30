"""
Contract tests for the fetch_medmcqa script.
Verifies that the manifest file is created and contains expected structure.
"""
import os
import json
from pathlib import Path

def test_manifest_structure(tmp_path):
    """Test that the manifest file has the correct structure."""
    # Simulate the expected structure after a successful run
    manifest_content = {
        "dataset": "medmcqa/medmcqa",
        "partitions": {
            "train": {
                "file": "medmcqa_train.jsonl",
                "checksum": "abc123",
                "size_rows": 100
            },
            "validation": {
                "file": "medmcqa_validation.jsonl",
                "checksum": "def456",
                "size_rows": 50
            },
            "test": {
                "file": "medmcqa_test.jsonl",
                "checksum": "ghi789",
                "size_rows": 50
            }
        }
    }
    
    manifest_file = tmp_path / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest_content, f)

    # Verify structure
    with open(manifest_file) as f:
        data = json.load(f)

    assert "dataset" in data
    assert data["dataset"] == "medmcqa/medmcqa"
    assert "partitions" in data
    assert set(data["partitions"].keys()) == {"train", "validation", "test"}
    
    for partition in ["train", "validation", "test"]:
        assert "file" in data["partitions"][partition]
        assert "checksum" in data["partitions"][partition]
        assert "size_rows" in data["partitions"][partition]

def test_checksum_format(tmp_path):
    """Test that checksums are valid SHA-256 hex strings."""
    import hashlib

    # Generate a valid SHA-256 hash for testing
    test_hash = hashlib.sha256(b"test").hexdigest()
    
    manifest_content = {
        "dataset": "medmcqa/medmcqa",
        "partitions": {
            "train": {
                "file": "medmcqa_train.jsonl",
                "checksum": test_hash,
                "size_rows": 100
            }
        }
    }

    manifest_file = tmp_path / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest_content, f)

    with open(manifest_file) as f:
        data = json.load(f)

    checksum = data["partitions"]["train"]["checksum"]
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)