import json
import os
import tempfile
from pathlib import Path
import pytest

from code.data.logging_integration import (
    log_candidate_to_file,
    load_all_candidates,
    get_candidates_by_task,
    get_candidates_by_validity,
    get_candidates_by_type,
    generate_sensitivity_summary
)


class TestLoggingIntegration:
    """Unit tests for logging integration functionality."""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary file for testing."""
        return str(tmp_path / "test_candidates.json")

    def test_log_candidate_to_file_creates_file(self, temp_log_file):
        """Test that logging a candidate creates the file."""
        candidate = {
            "task_id": "test_001",
            "perturbation_type": "synonym",
            "raw_score": 0.98,
            "is_valid": True,
            "reason": "Test reason"
        }
        
        log_candidate_to_file(candidate, temp_log_file)
        
        assert os.path.exists(temp_log_file)
        
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            loaded = json.loads(lines[0])
            assert loaded == candidate

    def test_log_candidate_to_file_appends(self, temp_log_file):
        """Test that multiple candidates are appended."""
        candidates = [
            {"task_id": "test_001", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "reason": "Reason 1"},
            {"task_id": "test_002", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": False, "reason": "Reason 2"}
        ]
        
        for c in candidates:
            log_candidate_to_file(c, temp_log_file)
        
        loaded = load_all_candidates(temp_log_file)
        assert len(loaded) == 2
        assert loaded[0] == candidates[0]
        assert loaded[1] == candidates[1]

    def test_load_all_candidates_empty_file(self, temp_log_file):
        """Test loading from an empty or non-existent file."""
        # Non-existent file
        result = load_all_candidates(temp_log_file)
        assert result == []
        
        # Empty file
        Path(temp_log_file).touch()
        result = load_all_candidates(temp_log_file)
        assert result == []

    def test_get_candidates_by_task(self, temp_log_file):
        """Test filtering candidates by task_id."""
        candidates = [
            {"task_id": "task_001", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "reason": "R1"},
            {"task_id": "task_002", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": False, "reason": "R2"},
            {"task_id": "task_001", "perturbation_type": "rephrase", "raw_score": 0.96, "is_valid": True, "reason": "R3"}
        ]
        
        for c in candidates:
            log_candidate_to_file(c, temp_log_file)
        
        task_001 = get_candidates_by_task(load_all_candidates(temp_log_file), "task_001")
        assert len(task_001) == 2
        assert all(c["task_id"] == "task_001" for c in task_001)

    def test_get_candidates_by_validity(self, temp_log_file):
        """Test filtering candidates by validity."""
        candidates = [
            {"task_id": "task_001", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "reason": "R1"},
            {"task_id": "task_002", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": False, "reason": "R2"},
            {"task_id": "task_003", "perturbation_type": "rephrase", "raw_score": 0.96, "is_valid": True, "reason": "R3"}
        ]
        
        for c in candidates:
            log_candidate_to_file(c, temp_log_file)
        
        valid = get_candidates_by_validity(load_all_candidates(temp_log_file), True)
        invalid = get_candidates_by_validity(load_all_candidates(temp_log_file), False)
        
        assert len(valid) == 2
        assert len(invalid) == 1
        assert all(c["is_valid"] for c in valid)
        assert all(not c["is_valid"] for c in invalid)

    def test_get_candidates_by_type(self, temp_log_file):
        """Test filtering candidates by perturbation type."""
        candidates = [
            {"task_id": "task_001", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "reason": "R1"},
            {"task_id": "task_002", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": False, "reason": "R2"},
            {"task_id": "task_003", "perturbation_type": "synonym", "raw_score": 0.97, "is_valid": True, "reason": "R3"}
        ]
        
        for c in candidates:
            log_candidate_to_file(c, temp_log_file)
        
        synonyms = get_candidates_by_type(load_all_candidates(temp_log_file), "synonym")
        typos = get_candidates_by_type(load_all_candidates(temp_log_file), "typo")
        
        assert len(synonyms) == 2
        assert len(typos) == 1
        assert all(c["perturbation_type"] == "synonym" for c in synonyms)
        assert all(c["perturbation_type"] == "typo" for c in typos)

    def test_generate_sensitivity_summary(self, temp_log_file):
        """Test sensitivity summary generation."""
        candidates = [
            {"task_id": "task_001", "perturbation_type": "synonym", "raw_score": 0.98, "is_valid": True, "reason": "R1"},
            {"task_id": "task_002", "perturbation_type": "typo", "raw_score": 0.92, "is_valid": False, "reason": "R2"},
            {"task_id": "task_003", "perturbation_type": "synonym", "raw_score": 0.97, "is_valid": True, "reason": "R3"},
            {"task_id": "task_004", "perturbation_type": "rephrase", "raw_score": 0.96, "is_valid": True, "reason": "R4"}
        ]
        
        for c in candidates:
            log_candidate_to_file(c, temp_log_file)
        
        loaded = load_all_candidates(temp_log_file)
        summary = generate_sensitivity_summary(loaded)
        
        assert summary["total_candidates"] == 4
        assert summary["valid_candidates"] == 3
        assert summary["invalid_candidates"] == 1
        assert summary["distribution_by_type"]["synonym"] == 2
        assert summary["distribution_by_type"]["typo"] == 1
        assert summary["distribution_by_type"]["rephrase"] == 1