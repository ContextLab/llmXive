"""
Unit tests for fetch_pr_commits.py
Tests pagination logic, commit extraction, and data processing.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from fetch_pr_commits import (
    parse_iso_datetime,
    calculate_turnaround_hours,
    extract_commit_messages,
    process_pr_data,
    fetch_prs_for_repo,
    fetch_commits_for_pr
)


class TestParseIsoDatetime:
    def test_parse_valid_iso(self):
        result = parse_iso_datetime("2023-10-01T12:00:00Z")
        assert result is not None
        assert result.year == 2023
        assert result.month == 10
        assert result.day == 1

    def test_parse_empty_string(self):
        assert parse_iso_datetime("") is None

    def test_parse_none(self):
        assert parse_iso_datetime(None) is None


class TestCalculateTurnaroundHours:
    def test_calculate_valid_turnaround(self):
        created = "2023-10-01T10:00:00Z"
        merged = "2023-10-01T12:00:00Z"
        hours = calculate_turnaround_hours(created, merged)
        assert hours == 2.0

    def test_calculate_partial_hours(self):
        created = "2023-10-01T10:00:00Z"
        merged = "2023-10-01T11:30:00Z"
        hours = calculate_turnaround_hours(created, merged)
        assert hours == 1.5

    def test_missing_dates(self):
        assert calculate_turnaround_hours(None, None) is None
        assert calculate_turnaround_hours("2023-10-01T10:00:00Z", None) is None


class TestExtractCommitMessages:
    def test_extract_messages(self):
        commits = [
            {"commit": {"message": "Fix bug"}},
            {"commit": {"message": "Add feature"}},
            {"commit": {}}
        ]
        messages = extract_commit_messages(commits)
        assert messages == ["Fix bug", "Add feature"]

    def test_empty_list(self):
        assert extract_commit_messages([]) == []


class TestFetchCommitsPagination:
    @patch('fetch_pr_commits.api_request_with_backoff')
    def test_fetch_all_pages(self, mock_request):
        # Simulate two pages of commits
        page1 = [{"commit": {"message": "commit 1"}}, {"commit": {"message": "commit 2"}}]
        page2 = [{"commit": {"message": "commit 3"}}]
        
        # Mock response for page 1 with Link header for next page
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = page1
        response1.headers = {"Link": '<url>; rel="next"'}

        # Mock response for page 2 (no next link)
        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = page2
        response2.headers = {}

        mock_request.side_effect = [response1, response2]

        commits = fetch_commits_for_pr("test/repo", 123)
        
        assert len(commits) == 3
        assert mock_request.call_count == 2
        # Verify page parameter was incremented
        assert mock_request.call_args_list[0][0][2]['page'] == 1
        assert mock_request.call_args_list[1][0][2]['page'] == 2

    @patch('fetch_pr_commits.api_request_with_backoff')
    def test_fetch_single_page(self, mock_request):
        commits_data = [{"commit": {"message": "commit 1"}}]
        response = Mock()
        response.status_code = 200
        response.json.return_value = commits_data
        response.headers = {}
        mock_request.return_value = response

        commits = fetch_commits_for_pr("test/repo", 123)
        assert len(commits) == 1
        assert mock_request.call_count == 1

class TestProcessPrData:
    @patch('fetch_pr_commits.fetch_commits_for_pr')
    def test_process_pr_with_commits(self, mock_fetch_commits):
        mock_fetch_commits.return_value = [
            {"commit": {"message": "Fix bug"}},
            {"commit": {"message": "Refactor"}}
        ]
        
        pr = {
            "number": 123,
            "created_at": "2023-10-01T10:00:00Z",
            "merged_at": "2023-10-01T12:00:00Z",
            "user": {"login": "test_user"}
        }
        
        result = process_pr_data("test/repo", pr)
        
        assert result is not None
        assert result["pr_id"] == "123"
        assert result["turnaround_hours"] == 2.0
        assert len(result["commit_messages"]) == 2
        assert "Fix bug" in result["commit_messages"]
        assert result["commit_count"] == 2

    def test_process_pr_missing_merged_at(self):
        pr = {
            "number": 123,
            "created_at": "2023-10-01T10:00:00Z",
            "merged_at": None
        }
        
        result = process_pr_data("test/repo", pr)
        assert result is None