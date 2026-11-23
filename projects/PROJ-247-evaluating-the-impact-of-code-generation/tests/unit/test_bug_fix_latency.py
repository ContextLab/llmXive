import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_02_metric_extraction import extract_bug_fix_latency, COMMIT_FIX_REGEX

class TestBugFixLatency(unittest.TestCase):

    def test_regex_matches_fixes(self):
        """Test that regex correctly matches 'Fixes #N' pattern."""
        message = "Fix critical bug in auth module. Fixes #123"
        match = COMMIT_FIX_REGEX.search(message)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "123")

    def test_regex_matches_closes(self):
        """Test that regex correctly matches 'Closes #N' pattern."""
        message = "Merge pull request #456. Closes #456"
        match = COMMIT_FIX_REGEX.search(message)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "456")

    def test_regex_case_insensitive(self):
        """Test that regex is case insensitive."""
        message = "fixes #789"
        match = COMMIT_FIX_REGEX.search(message)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "789")

    @patch('code_02_metric_extraction.requests')
    def test_extract_latency_success(self, mock_requests):
        """Test successful latency calculation."""
        # Mock commit
        commit = {
            'date': datetime(2023, 1, 1, 12, 0, 0),
            'message': 'Fix login issue. Fixes #100'
        }
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'state': 'closed',
            'closed_at': '2023, 1, 11, 12, 0, 0' # 10 days later
        }
        mock_requests.get.return_value = mock_response
        
        # Mock parse_date to return a datetime
        with patch('code_02_metric_extraction.parse_date') as mock_parse:
            mock_parse.side_effect = lambda x: datetime(2023, 1, 11, 12, 0, 0) if 'closed_at' in x else datetime(2023, 1, 1, 12, 0, 0)
            
            result = extract_bug_fix_latency(commit, 'owner', 'repo')
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 10) # latency_days
            self.assertEqual(result[1], 100) # issue_id

    def test_no_fix_pattern(self):
        """Test that None is returned when no fix pattern is found."""
        commit = {
            'date': datetime(2023, 1, 1),
            'message': 'Update documentation'
        }
        result = extract_bug_fix_latency(commit, 'owner', 'repo')
        self.assertIsNone(result)

    def test_issue_not_closed(self):
        """Test that None is returned when issue is not closed."""
        commit = {
            'date': datetime(2023, 1, 1),
            'message': 'Fix bug. Fixes #200'
        }
        
        with patch('code_02_metric_extraction.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'state': 'open'}
            mock_requests.get.return_value = mock_response
            
            result = extract_bug_fix_latency(commit, 'owner', 'repo')
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()