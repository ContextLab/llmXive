import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_data import fetch_prs_for_repo, parse_iso_datetime, extract_commit_keywords, check_labels

class TestFetchDataPagination(unittest.TestCase):
    
    def test_parse_iso_datetime(self):
        """Test ISO datetime parsing."""
        dt = parse_iso_datetime("2023-01-15T10:30:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 15)
    
    def test_extract_commit_keywords(self):
        """Test keyword extraction from commit messages."""
        msg = "Fix bug with copilot suggestion"
        keywords = extract_commit_keywords(msg)
        self.assertIn('copilot', keywords)
        
        msg = "AI generated code for feature"
        keywords = extract_commit_keywords(msg)
        self.assertIn('ai-generated', keywords)
        
        msg = "Regular commit message"
        keywords = extract_commit_keywords(msg)
        self.assertEqual(keywords, [])
    
    def test_check_labels(self):
        """Test label extraction."""
        labels = [{'name': 'ai-generated'}, {'name': 'bug'}]
        result = check_labels(labels)
        self.assertIn('ai-generated', result)
        self.assertNotIn('bug', result)
    
    @patch('fetch_data.api_request_with_backoff')
    def test_fetch_prs_pagination(self, mock_request):
        """Test that pagination logic correctly handles Link headers."""
        # Mock response for page 1
        page1_data = [{'number': 1, 'state': 'closed'}]
        page2_data = [{'number': 2, 'state': 'closed'}]
        page3_data = []  # Empty page indicates end
        
        # Setup mock responses
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_data
        mock_response1.headers = {
            'Link': '<https://api.github.com/repo/pulls?page=2>; rel="next"'
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2_data
        mock_response2.headers = {
            'Link': '<https://api.github.com/repo/pulls?page=3>; rel="next"'
        }
        
        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.json.return_value = page3_data
        mock_response3.headers = {}
        
        # Sequence of responses
        mock_request.side_effect = [mock_response1, mock_response2, mock_response3]
        
        # Call function
        result = fetch_prs_for_repo("test/repo")
        
        # Verify we got data from all pages
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['number'], 1)
        self.assertEqual(result[1]['number'], 2)
        
        # Verify api_request_with_backoff was called 3 times (3 pages)
        self.assertEqual(mock_request.call_count, 3)
    
    @patch('fetch_data.api_request_with_backoff')
    def test_fetch_prs_stop_condition_max_pages(self, mock_request):
        """Test that pagination stops at MAX_PAGES_PER_REPO."""
        # Create mock responses for 51 pages (should stop at 50)
        responses = []
        for i in range(51):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{'number': i}]
            if i < 50:
                mock_resp.headers = {'Link': f'<next>; rel="next"'}
            else:
                mock_resp.headers = {}
            responses.append(mock_resp)
        
        mock_request.side_effect = responses
        
        result = fetch_prs_for_repo("test/repo")
        
        # Should have fetched 50 pages
        self.assertEqual(len(result), 50)
        self.assertEqual(mock_request.call_count, 50)

if __name__ == '__main__':
    unittest.main()
