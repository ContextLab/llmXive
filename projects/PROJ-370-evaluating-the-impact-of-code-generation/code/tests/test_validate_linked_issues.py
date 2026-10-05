"""
Unit tests for the linked issue validation logic (T016).
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.extraction.validate_linked_issues import (
    validate_linked_issues,
    process_pr_dataset
)


class TestValidateLinkedIssues:
    """Tests for the validate_linked_issues function."""

    def test_empty_linked_issues(self):
        """Test PR with no linked issues."""
        pr_data = {
            "pr_id": "123",
            "linked_issue_ids": []
        }
        result = validate_linked_issues(pr_data)
        
        assert result["linked_issues_status"] == []
        assert result["is_ground_truth"] is False
        assert result["validation_flag"] is True

    def test_single_linked_issue(self):
        """Test PR with a single linked issue."""
        pr_data = {
            "pr_id": "456",
            "linked_issue_ids": ["789"]
        }
        result = validate_linked_issues(pr_data)
        
        assert len(result["linked_issues_status"]) == 1
        assert result["linked_issues_status"][0]["issue_id"] == "789"
        assert result["linked_issues_status"][0]["status"] == "reported"
        assert result["linked_issues_status"][0]["is_ground_truth"] is False
        assert result["is_ground_truth"] is False
        assert result["validation_flag"] is True

    def test_multiple_linked_issues(self):
        """Test PR with multiple linked issues."""
        pr_data = {
            "pr_id": "101",
            "linked_issue_ids": ["102", "103", "104"]
        }
        result = validate_linked_issues(pr_data)
        
        assert len(result["linked_issues_status"]) == 3
        for i, status in enumerate(result["linked_issues_status"]):
            assert status["issue_id"] == f"10{i+2}"
            assert status["status"] == "reported"
            assert status["is_ground_truth"] is False
            assert status["validation_source"] == "extraction_phase"

    def test_missing_linked_issue_ids_key(self):
        """Test PR data without linked_issue_ids key."""
        pr_data = {
            "pr_id": "202"
        }
        result = validate_linked_issues(pr_data)
        
        assert result["linked_issues_status"] == []
        assert result["is_ground_truth"] is False
        assert result["validation_flag"] is True

    def test_invalid_pr_data_type(self):
        """Test with invalid pr_data type."""
        with patch('code.src.extraction.validate_linked_issues.logger') as mock_logger:
            result = validate_linked_issues("invalid_string")
            mock_logger.error.assert_called_once()
            assert result == "invalid_string"

    def test_ground_truth_flag_false(self):
        """Ensure is_ground_truth is explicitly False for linked issues."""
        pr_data = {
            "pr_id": "303",
            "linked_issue_ids": ["304"]
        }
        result = validate_linked_issues(pr_data)
        
        # Critical check: linked issues must NOT be ground truth at this stage
        assert result["is_ground_truth"] is False
        assert result["linked_issues_status"][0]["is_ground_truth"] is False


class TestProcessPrDataset:
    """Tests for the process_pr_dataset function."""

    def test_process_valid_dataset(self):
        """Test processing a valid dataset file."""
        sample_data = [
            {
                "pr_id": "1",
                "linked_issue_ids": ["10", "11"]
            },
            {
                "pr_id": "2",
                "linked_issue_ids": []
            },
            {
                "pr_id": "3",
                "linked_issue_ids": ["12"]
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            with open(input_path, 'w') as f:
                json.dump(sample_data, f)

            stats = process_pr_dataset(input_path, output_path)

            assert stats["total_prs"] == 3
            assert stats["prs_with_linked_issues"] == 2
            assert stats["total_linked_issues"] == 3
            assert stats["validation_errors"] == 0
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                output_data = json.load(f)
            
            assert len(output_data) == 3
            # Check that validation was applied
            assert output_data[0]["linked_issues_status"][0]["status"] == "reported"

    def test_missing_input_file(self):
        """Test processing with missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.json"
            output_path = Path(tmpdir) / "output.json"
            
            with pytest.raises(FileNotFoundError):
                process_pr_dataset(input_path, output_path)

    def test_invalid_json_structure(self):
        """Test processing with non-list JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            with open(input_path, 'w') as f:
                json.dump({"not": "a_list"}, f)
            
            with pytest.raises(ValueError):
                process_pr_dataset(input_path, output_path)
