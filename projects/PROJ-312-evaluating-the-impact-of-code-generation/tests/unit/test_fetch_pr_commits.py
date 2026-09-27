"""
Unit tests for fetch_pr_commits.py (T012b implementation).
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json
import os

# Import the functions to test
# Note: These are imported from the module that will be created/updated
# We assume the module is named 'fetch_pr_commits'
import sys
from pathlib import Path

# Add the code directory to the path if needed
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from fetch_pr_commits import (
    parse_iso_datetime,
    calculate_turnaround_hours,
    extract_commit_messages,
    load_repos,
)


class TestParseIsoDatetime:
    def test_valid_iso_string(self):
        result = parse_iso_datetime("2023-01-01T12:00:00Z")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1

    def test_valid_iso_string_with_offset(self):
        result = parse_iso_datetime("2023-01-01T12:00:00+00:00")
        assert result is not None
        assert result.year == 2023

    def test_empty_string(self):
        result = parse_iso_datetime("")
        assert result is None

    def test_none_input(self):
        result = parse_iso_datetime(None)
        assert result is None

    def test_invalid_format(self):
        result = parse_iso_datetime("not-a-date")
        assert result is None


class TestCalculateTurnaroundHours:
    def test_simple_case(self):
        start = datetime(2023, 1, 1, 0, 0, 0)
        end = datetime(2023, 1, 1, 12, 0, 0)
        hours = calculate_turnaround_hours(start, end)
        assert hours == 12.0

    def test_negative_result_handled(self):
        # If merged before created, it should still calculate (mathematically negative)
        # but typically data is clean. We test the math.
        start = datetime(2023, 1, 1, 12, 0, 0)
        end = datetime(2023, 1, 1, 0, 0, 0)
        hours = calculate_turnaround_hours(start, end)
        assert hours == -12.0

    def test_missing_dates(self):
        assert calculate_turnaround_hours(None, datetime(2023, 1, 1)) is None
        assert calculate_turnaround_hours(datetime(2023, 1, 1), None) is None


class TestExtractCommitMessages:
    def test_extract_from_list(self):
        commits = [
            {"commit": {"message": "First commit"}},
            {"commit": {"message": "Second commit"}},
        ]
        messages = extract_commit_messages(commits)
        assert messages == ["First commit", "Second commit"]

    def test_empty_list(self):
        assert extract_commit_messages([]) == []

    def test_malformed_commit(self):
        commits = [{"other": "data"}]
        messages = extract_commit_messages(commits)
        assert messages == []

class TestLoadRepos:
    def test_load_from_valid_json(self, tmp_path):
        test_file = tmp_path / "repos.json"
        test_data = [{"name": "test/repo1", "stars": 100}]
        test_file.write_text(json.dumps(test_data))
        
        result = load_repos(test_file)
        assert result == test_data

    def test_load_missing_file(self, tmp_path):
        result = load_repos(tmp_path / "nonexistent.json")
        assert result == []