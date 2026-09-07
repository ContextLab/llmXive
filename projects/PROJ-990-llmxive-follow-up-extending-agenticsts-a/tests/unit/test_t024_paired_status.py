"""
Unit tests for T024: Verify Paired Status.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to import from the module, but since it's a script, we might need to adjust
# For now, we assume the script is in code/ and we import the logic
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from t024_verify_paired_status import extract_key_pairs, verify_paired_status

class TestExtractKeyPairs:
    def test_extract_basic_pairs(self):
        logs = [
            {"trajectory_id": "t1", "initial_state_hash": "hash1"},
            {"trajectory_id": "t2", "initial_state_hash": "hash2"}
        ]
        pairs = extract_key_pairs(logs)
        assert len(pairs) == 2
        assert ("t1", "hash1") in pairs
        assert ("t2", "hash2") in pairs

    def test_extract_alternative_keys(self):
        logs = [
            {"id": "t1", "initial_hash": "hash1"},
            {"traj_id": "t2", "state_hash": "hash2"}
        ]
        pairs = extract_key_pairs(logs)
        assert len(pairs) == 2
        assert ("t1", "hash1") in pairs
        assert ("t2", "hash2") in pairs

    def test_extract_mixed_valid_invalid(self):
        logs = [
            {"trajectory_id": "t1", "initial_state_hash": "hash1"},
            {"trajectory_id": "t2"},  # Missing hash
            {"initial_state_hash": "hash3"},  # Missing ID
            {"id": "t4", "initial_hash": "hash4"}
        ]
        pairs = extract_key_pairs(logs)
        assert len(pairs) == 2
        assert ("t1", "hash1") in pairs
        assert ("t4", "hash4") in pairs

class TestVerifyPairedStatus:
    def test_fully_paired(self, tmp_path):
        # Create temporary files
        dynamic_path = tmp_path / "dynamic.json"
        static_path = tmp_path / "static.json"
        output_path = tmp_path / "paired_status.json"

        # Write identical logs
        logs = [
            {"trajectory_id": "t1", "initial_state_hash": "h1"},
            {"trajectory_id": "t2", "initial_state_hash": "h2"}
        ]
        with open(dynamic_path, 'w') as f:
            json.dump(logs, f)
        with open(static_path, 'w') as f:
            json.dump(logs, f)

        result = verify_paired_status(dynamic_path, static_path, output_path)
        
        assert result["is_paired"] is True
        assert len(result["valid_trajectory_ids"]) == 2
        assert len(result["excluded_trajectory_ids"]) == 0
        assert output_path.exists()

    def test_unpaired_logs(self, tmp_path):
        dynamic_path = tmp_path / "dynamic.json"
        static_path = tmp_path / "static.json"
        output_path = tmp_path / "paired_status.json"

        # Different logs
        dynamic_logs = [
            {"trajectory_id": "t1", "initial_state_hash": "h1"},
            {"trajectory_id": "t2", "initial_state_hash": "h2"}
        ]
        static_logs = [
            {"trajectory_id": "t1", "initial_state_hash": "h1"},
            {"trajectory_id": "t3", "initial_state_hash": "h3"}  # t3 instead of t2
        ]
        
        with open(dynamic_path, 'w') as f:
            json.dump(dynamic_logs, f)
        with open(static_path, 'w') as f:
            json.dump(static_logs, f)

        result = verify_paired_status(dynamic_path, static_path, output_path)
        
        assert result["is_paired"] is False
        assert "t1" in result["valid_trajectory_ids"]
        assert "t2" in result["excluded_trajectory_ids"]
        assert "t3" in result["excluded_trajectory_ids"]

    def test_missing_file(self, tmp_path):
        dynamic_path = tmp_path / "dynamic.json"
        static_path = tmp_path / "nonexistent.json"
        output_path = tmp_path / "paired_status.json"

        with open(dynamic_path, 'w') as f:
            json.dump([], f)

        with pytest.raises(FileNotFoundError):
            verify_paired_status(dynamic_path, static_path, output_path)