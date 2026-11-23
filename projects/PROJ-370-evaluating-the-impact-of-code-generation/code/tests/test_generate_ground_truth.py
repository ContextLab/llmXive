"""
Unit tests for T017: generate_ground_truth.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.extraction.generate_ground_truth import (
    load_human_confirmations,
    is_senior_maintainer,
    triangulate_bugs,
    apply_fallback,
    run_ground_truth_generation
)

class TestLoadHumanConfirmations:
    def test_load_valid_confirmations(self, tmp_path):
        """Test loading valid human confirmations."""
        data = [
            {
                "pr_id": "123",
                "file_path": "src/main.py",
                "line_start": 10,
                "line_end": 15,
                "reviewer_id": "user1",
                "confirmation_type": "major"
            },
            {
                "pr_id": "123",
                "file_path": "src/main.py",
                "line_start": 10,
                "line_end": 15,
                "reviewer_id": "user2",
                "confirmation_type": "critical"
            }
        ]
        
        file_path = tmp_path / "human_confirmations.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_human_confirmations(file_path)
        assert len(result) == 2
        assert result[0]["pr_id"] == "123"

    def test_load_missing_file(self, tmp_path):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_human_confirmations(tmp_path / "nonexistent.json")

    def test_load_invalid_format(self, tmp_path):
        """Test loading non-list data raises error."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump({"not": "a list"}, f)
        
        with pytest.raises(ValueError):
            load_human_confirmations(file_path)

class TestIsSeniorMaintainer:
    def test_senior_keywords(self):
        """Test senior maintainer detection."""
        assert is_senior_maintainer("core-maintainer") is True
        assert is_senior_maintainer("owner-bot") is True
        assert is_senior_maintainer("senior-dev") is True
        assert is_senior_maintainer("admin-user") is True

    def test_non_senior(self):
        """Test non-senior users."""
        assert is_senior_maintainer("regular-user") is False
        assert is_senior_maintainer("contributor") is False

class TestTriangulateBugs:
    def test_strict_triangulation_two_reviewers(self):
        """Test triangulation with 2 independent reviewers."""
        confirmations = [
            {
                "pr_id": "100",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user1",
                "confirmation_type": "major"
            },
            {
                "pr_id": "100",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user2",
                "confirmation_type": "minor"
            }
        ]
        
        bugs, count = triangulate_bugs(confirmations)
        assert count == 1
        assert bugs[0]["is_verified"] is True
        assert bugs[0]["verification_method"] == "strict_triangulation"
        assert bugs[0]["severity"] == "major" # Most severe

    def test_strict_triangulation_senior(self):
        """Test triangulation with 1 senior maintainer."""
        confirmations = [
            {
                "pr_id": "200",
                "file_path": "file.py",
                "line_start": 10,
                "line_end": 15,
                "reviewer_id": "core-maintainer",
                "confirmation_type": "critical"
            }
        ]
        
        bugs, count = triangulate_bugs(confirmations)
        assert count == 1
        assert bugs[0]["is_verified"] is True
        assert bugs[0]["verification_method"] == "strict_triangulation"

    def test_no_triangulation(self):
        """Test case with insufficient reviewers."""
        confirmations = [
            {
                "pr_id": "300",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user1",
                "confirmation_type": "minor"
            }
        ]
        
        bugs, count = triangulate_bugs(confirmations)
        assert count == 0
        assert bugs[0]["is_verified"] is False
        assert bugs[0]["verification_method"] == "pending_fallback"

    def test_multiple_locations(self):
        """Test handling of multiple distinct bug locations."""
        confirmations = [
            {
                "pr_id": "400",
                "file_path": "file1.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user1",
                "confirmation_type": "minor"
            },
            {
                "pr_id": "400",
                "file_path": "file1.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user2",
                "confirmation_type": "major"
            },
            {
                "pr_id": "400",
                "file_path": "file2.py",
                "line_start": 10,
                "line_end": 15,
                "reviewer_id": "user1",
                "confirmation_type": "minor"
            },
            {
                "pr_id": "400",
                "file_path": "file2.py",
                "line_start": 10,
                "line_end": 15,
                "reviewer_id": "user2",
                "confirmation_type": "minor"
            }
        ]
        
        bugs, count = triangulate_bugs(confirmations)
        assert count == 2
        assert len(bugs) == 2
        assert all(b["is_verified"] for b in bugs)

class TestApplyFallback:
    def test_fallback_match(self):
        """Test fallback to closed issue with bug label."""
        candidate_bugs = [
            {
                "pr_id": "500",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "severity": "minor",
                "is_verified": False,
                "verification_method": "pending_fallback",
                "reviewer_count": 1,
                "senior_count": 0
            }
        ]
        
        fallback_issues = [
            {
                "number": "500",
                "state": "closed",
                "labels": [{"name": "bug"}],
                "title": "Bug in file"
            }
        ]
        
        updated, count = apply_fallback(candidate_bugs, fallback_issues)
        assert count == 1
        assert updated[0]["is_verified"] is True
        assert updated[0]["verification_method"] == "fallback_closed_issue"

    def test_fallback_no_match(self):
        """Test fallback when no matching issue exists."""
        candidate_bugs = [
            {
                "pr_id": "600",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "severity": "minor",
                "is_verified": False,
                "verification_method": "pending_fallback",
                "reviewer_count": 1,
                "senior_count": 0
            }
        ]
        
        fallback_issues = []
        
        updated, count = apply_fallback(candidate_bugs, fallback_issues)
        assert count == 0
        assert updated[0]["is_verified"] is False
        assert updated[0]["verification_method"] == "insufficient_data"

    def test_already_verified_unchanged(self):
        """Test that already verified bugs are not modified."""
        candidate_bugs = [
            {
                "pr_id": "700",
                "file_path": "file.py",
                "line_start": 1,
                "line_end": 5,
                "severity": "major",
                "is_verified": True,
                "verification_method": "strict_triangulation",
                "reviewer_count": 2,
                "senior_count": 0
            }
        ]
        
        fallback_issues = [
            {
                "number": "700",
                "state": "closed",
                "labels": [{"name": "bug"}]
            }
        ]
        
        updated, count = apply_fallback(candidate_bugs, fallback_issues)
        assert count == 0
        assert updated[0]["is_verified"] is True
        assert updated[0]["verification_method"] == "strict_triangulation"

class TestRunGroundTruthGeneration:
    @patch('code.src.extraction.generate_ground_truth.get_paths')
    @patch('code.src.extraction.generate_ground_truth.ensure_directories')
    def test_run_full_pipeline(self, mock_ensure, mock_get_paths, tmp_path):
        """Test full execution of ground truth generation."""
        # Setup mock paths
        paths = {
            "derived": tmp_path / "derived",
            "raw": tmp_path / "raw",
            "logs": tmp_path / "logs"
        }
        mock_get_paths.return_value = paths
        paths["derived"].mkdir()
        paths["raw"].mkdir()
        
        # Create input data
        confirmations = [
            {
                "pr_id": "800",
                "file_path": "test.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user1",
                "confirmation_type": "major"
            },
            {
                "pr_id": "800",
                "file_path": "test.py",
                "line_start": 1,
                "line_end": 5,
                "reviewer_id": "user2",
                "confirmation_type": "critical"
            }
        ]
        
        input_file = paths["derived"] / "human_confirmations.json"
        with open(input_file, 'w') as f:
            json.dump(confirmations, f)
        
        # Run the function
        run_ground_truth_generation()
        
        # Verify output
        output_file = paths["derived"] / "human_baseline.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert len(result) == 1
        assert result[0]["is_verified"] is True
        assert result[0]["verification_method"] == "strict_triangulation"
        assert result[0]["severity"] == "critical"