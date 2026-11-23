import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_data import (
    parse_iso_datetime,
    extract_commit_keywords,
    check_labels,
    classify_pr,
    calculate_turnaround_hours,
    fetch_prs_for_repo,
    fetch_commits_for_pr
)

class TestFetchDataEdgeCases(unittest.TestCase):

    def test_parse_iso_datetime_empty(self):
        """Test that empty string raises ValueError."""
        with self.assertRaises(ValueError):
            parse_iso_datetime("")

    def test_parse_iso_datetime_valid(self):
        """Test parsing valid ISO datetime."""
        dt = parse_iso_datetime("2023-10-01T12:00:00Z")
        self.assertIsNotNone(dt)

    def test_extract_commit_keywords_empty(self):
        """Test with empty list."""
        result = extract_commit_keywords([])
        self.assertEqual(result, [])

    def test_extract_commit_keywords_no_match(self):
        """Test with no matching keywords."""
        result = extract_commit_keywords(["fix bug", "update docs"])
        self.assertEqual(result, [])

    def test_extract_commit_keywords_match(self):
        """Test with matching keywords."""
        result = extract_commit_keywords(["fix copilot bug", "AI generated code"])
        self.assertIn("copilot", result)
        self.assertIn("ai-generated", result)

    def test_check_labels_empty(self):
        """Test with empty labels."""
        result = check_labels({})
        self.assertEqual(result, [])

    def test_check_labels_string_list(self):
        """Test with string labels."""
        pr_data = {"labels": ["ai-generated", "bug"]}
        result = check_labels(pr_data)
        self.assertIn("ai-generated", result)

    def test_check_labels_object_list(self):
        """Test with label objects."""
        pr_data = {"labels": [{"name": "copilot-assisted"}, {"name": "enhancement"}]}
        result = check_labels(pr_data)
        self.assertIn("copilot-assisted", result)

    def test_classify_pr_ai_commit(self):
        """Test classification based on commit messages."""
        pr_data = {
            "commit_messages": ["feat: add copilot suggestion"],
            "labels": []
        }
        is_ai, reason = classify_pr(pr_data)
        self.assertTrue(is_ai)
        self.assertIn("copilot", reason)

    def test_classify_pr_ai_label(self):
        """Test classification based on labels."""
        pr_data = {
            "commit_messages": ["fix: minor typo"],
            "labels": [{"name": "ai-generated"}]
        }
        is_ai, reason = classify_pr(pr_data)
        self.assertTrue(is_ai)
        self.assertIn("ai-generated", reason)

    def test_classify_pr_non_ai(self):
        """Test classification as non-AI."""
        pr_data = {
            "commit_messages": ["fix: typo"],
            "labels": [{"name": "bug"}]
        }
        is_ai, reason = classify_pr(pr_data)
        self.assertFalse(is_ai)
        self.assertEqual(reason, "No AI indicators found")

    def test_calculate_turnaround_hours_valid(self):
        """Test valid turnaround calculation."""
        hours = calculate_turnaround_hours("2023-10-01T00:00:00Z", "2023-10-01T02:00:00Z")
        self.assertEqual(hours, 2.0)

    def test_calculate_turnaround_hours_invalid(self):
        """Test invalid date strings."""
        hours = calculate_turnaround_hours("invalid", "2023-10-01T02:00:00Z")
        self.assertEqual(hours, -1.0)

    @patch('fetch_data.api_request_with_backoff')
    @patch('fetch_data.log_api_headers')
    def test_fetch_prs_for_repo_empty_response(self, mock_log, mock_backoff):
        """Test handling empty PR response."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_backoff.return_value = mock_response
        
        prs = fetch_prs_for_repo("test/repo", max_pages=1)
        self.assertEqual(len(prs), 0)

    @patch('fetch_data.api_request_with_backoff')
    @patch('fetch_data.log_api_headers')
    def test_fetch_commits_for_pr_empty(self, mock_log, mock_backoff):
        """Test fetching commits when API returns empty."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.headers = {}
        mock_backoff.return_value = mock_response
        
        messages = fetch_commits_for_pr("test/repo", 1)
        self.assertEqual(messages, [])

if __name__ == '__main__':
    unittest.main()