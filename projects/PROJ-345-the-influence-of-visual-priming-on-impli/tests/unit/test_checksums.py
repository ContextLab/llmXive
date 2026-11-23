"""
Unit tests for checksum verification and linked metadata percentage calculation (T018).
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.state.checksums import (
    calculate_file_checksum,
    load_state_yaml,
    save_state_yaml,
    verify_and_record_checksums,
    calculate_linked_metadata_percentage
)
from code.config import get_path


class TestCalculateFileChecksum:
    def test_calculate_checksum_known_file(self, tmp_path):
        """Test checksum calculation for a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = calculate_file_checksum(test_file)

        # SHA256 of "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert checksum == expected

    def test_calculate_checksum_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            calculate_file_checksum(non_existent)

    def test_calculate_checksum_large_file(self, tmp_path):
        """Test checksum calculation for a larger file (chunked reading)."""
        test_file = tmp_path / "large.txt"
        # Create a 1MB file
        test_content = b"X" * (1024 * 1024)
        test_file.write_bytes(test_content)

        checksum = calculate_file_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex string length


class TestStateYamlOperations:
    def test_load_nonexistent_state(self, tmp_path):
        """Test loading a non-existent state file returns empty state."""
        non_existent = tmp_path / "nonexistent.yaml"

        state = load_state_yaml(non_existent)

        assert "artifacts" in state
        assert "checksums" in state
        assert "metadata" in state

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state data."""
        state_file = tmp_path / "state.yaml"
        test_data = {
            "artifacts": {"test": "value"},
            "checksums": {"raw_data": {"file.txt": {"checksum": "abc123"}}},
            "metadata": {"version": "1.0"}
        }

        save_state_yaml(test_data, state_file)

        assert state_file.exists()

        loaded = load_state_yaml(state_file)

        assert loaded == test_data


class TestVerifyAndRecordChecksums:
    def test_verify_checksums_empty_dir(self, tmp_path, tmp_path_state):
        """Test checksum verification with empty directory."""
        state_file = tmp_path_state / "state.yaml"
        checksums = verify_and_record_checksums(tmp_path, state_file)

        assert checksums == {}

    def test_verify_checksums_with_files(self, tmp_path, tmp_path_state):
        """Test checksum verification with files in directory."""
        state_file = tmp_path_state / "state.yaml"

        # Create test files
        (tmp_path / "file1.txt").write_bytes(b"content1")
        (tmp_path / "file2.txt").write_bytes(b"content2")

        checksums = verify_and_record_checksums(tmp_path, state_file)

        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums

        # Verify state file was updated
        state = load_state_yaml(state_file)
        assert "checksums" in state
        assert "raw_data" in state["checksums"]
        assert "file1.txt" in state["checksums"]["raw_data"]


class TestCalculateLinkedMetadataPercentage:
    def test_calculate_percentage_all_linked(self, tmp_path):
        """Test calculation when all trials have linked metadata."""
        linked_file = tmp_path / "linked_trials.csv"

        # Create test data with all valid stimulus_ids
        data = {
            "trial_id": [1, 2, 3, 4, 5],
            "response_time": [500, 600, 550, 700, 450],
            "stimulus_id": ["img1", "img2", "img3", "img4", "img5"],
            "prime_condition": ["positive", "negative", "positive", "negative", "positive"],
            "participant_id": ["p1", "p1", "p2", "p2", "p3"]
        }
        pd.DataFrame(data).to_csv(linked_file, index=False)

        result = calculate_linked_metadata_percentage(linked_file, threshold=0.95)

        assert result["total_trials"] == 5
        assert result["linked_trials"] == 5
        assert result["linked_percentage"] == 1.0
        assert result["meets_threshold"] is True

    def test_calculate_percentage_partial_linked(self, tmp_path):
        """Test calculation when some trials lack linked metadata."""
        linked_file = tmp_path / "linked_trials.csv"

        # Create test data with some missing stimulus_ids
        data = {
            "trial_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "response_time": [500] * 10,
            "stimulus_id": ["img1", "", "img3", None, "img5", "img6", "", "img8", "img9", "img10"],
            "prime_condition": ["positive"] * 10,
            "participant_id": ["p1"] * 10
        }
        pd.DataFrame(data).to_csv(linked_file, index=False)

        result = calculate_linked_metadata_percentage(linked_file, threshold=0.95)

        assert result["total_trials"] == 10
        assert result["linked_trials"] == 8  # 2 are missing/empty
        assert result["linked_percentage"] == 0.8
        assert result["meets_threshold"] is False  # 0.8 < 0.95

    def test_calculate_percentage_meets_threshold(self, tmp_path):
        """Test calculation when percentage meets a lower threshold."""
        linked_file = tmp_path / "linked_trials.csv"

        # 9 out of 10 = 90%
        data = {
            "trial_id": list(range(1, 11)),
            "response_time": [500] * 10,
            "stimulus_id": ["img" + str(i) if i != 5 else "" for i in range(1, 11)],
            "prime_condition": ["positive"] * 10,
            "participant_id": ["p1"] * 10
        }
        pd.DataFrame(data).to_csv(linked_file, index=False)

        # With threshold 0.85, 0.9 should pass
        result = calculate_linked_metadata_percentage(linked_file, threshold=0.85)

        assert result["linked_percentage"] == 0.9
        assert result["meets_threshold"] is True

    def test_calculate_percentage_empty_file(self, tmp_path):
        """Test that ValueError is raised for empty file."""
        linked_file = tmp_path / "linked_trials.csv"

        # Create empty file with just headers
        pd.DataFrame(columns=["trial_id", "response_time", "stimulus_id"]).to_csv(
            linked_file, index=False
        )

        with pytest.raises(ValueError, match="Linked trials file is empty"):
            calculate_linked_metadata_percentage(linked_file)

    def test_calculate_percentage_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.csv"

        with pytest.raises(FileNotFoundError):
            calculate_linked_metadata_percentage(non_existent)


@pytest.fixture
def tmp_path_state(tmp_path):
    """Create a temporary directory for state files."""
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir
