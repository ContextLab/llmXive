"""
Unit tests for fetch_pr_commits.py functions.
These tests verify the logic of commit extraction and turnaround calculation
without making actual API calls.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fetch_pr_commits import (
    parse_iso_datetime,
    calculate_turnaround_hours,
    process_pr_data
)

class TestParseIsoDatetime:
    def test_parse_standard_iso(self):
        result = parse_iso_datetime("2023-10-01T12:00:00Z")
        assert result is not None
        assert result.year == 2023
        assert result.month == 10
        assert result.day == 1
    
    def test_parse_with_microseconds(self):
        result = parse_iso_datetime("2023-10-01T12:00:00.123456Z")
        assert result is not None
    
    def test_parse_empty_string(self):
        result = parse_iso_datetime("")
        assert result is None
    
    def test_parse_none(self):
        result = parse_iso_datetime(None)
        assert result is None

class TestCalculateTurnaroundHours:
    def test_calculation(self):
        # 2 hours difference
        start = "2023-10-01T10:00:00Z"
        end = "2023-10-01T12:00:00Z"
        result = calculate_turnaround_hours(start, end)
        assert result == 2.0
    
    def test_fractional_hours(self):
        # 1.5 hours difference
        start = "2023-10-01T10:00:00Z"
        end = "2023-10-01T11:30:00Z"
        result = calculate_turnaround_hours(start, end)
        assert result == 1.5
    
    def test_invalid_dates(self):
        result = calculate_turnaround_hours("invalid", "2023-10-01T12:00:00Z")
        assert result is None

class TestProcessPrData:
    def test_process_valid_pr(self):
        pr = {
            "number": 123,
            "state": "closed",
            "merged_at": "2023-10-01T12:00:00Z",
            "created_at": "2023-10-01T10:00:00Z",
            "labels": [{"name": "bug"}],
            "user": {"login": "test_user"}
        }
        
        mock_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "message": "Fix bug #123",
                    "author": {"name": "Test User"}
                }
            },
            {
                "sha": "def456",
                "commit": {
                    "message": "Copilot: add tests",
                    "author": {"name": "Test User"}
                }
            }
        ]
        
        with patch('fetch_pr_commits.fetch_commits_for_pr', return_value=mock_commits):
            result = process_pr_data("test/repo", pr)
            
            assert result is not None
            assert result["pr_id"] == "123"
            assert result["repo_name"] == "test/repo"
            assert result["turnaround_hours"] == 2.0
            assert "bug" in result["labels"]
            assert len(result["commit_messages"]) == 2
            assert "Fix bug #123" in result["commit_messages"]
            assert "Copilot: add tests" in result["commit_messages"]
    
    def test_skip_unmerged_pr(self):
        pr = {
            "number": 456,
            "state": "open",
            "created_at": "2023-10-01T10:00:00Z",
            "labels": []
        }
        result = process_pr_data("test/repo", pr)
        assert result is None
    
    def test_skip_pr_without_merged_at(self):
        pr = {
            "number": 789,
            "state": "closed",
            "created_at": "2023-10-01T10:00:00Z",
            "merged_at": None,
            "labels": []
        }
        result = process_pr_data("test/repo", pr)
        assert result is None