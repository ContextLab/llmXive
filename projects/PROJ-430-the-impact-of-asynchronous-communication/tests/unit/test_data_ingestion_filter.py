"""
Unit tests for T014: Project-level filtering for insufficient data.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from models import Event, EventType
from data_ingestion import fetch_and_process_project_data

class TestInsufficientDataFilter(unittest.TestCase):

    def test_project_filtered_when_events_below_threshold(self):
        """
        Verify that a project with fewer events than min_events returns None.
        """
        mock_events = [
            {"id": 1, "type": "IssuesEvent", "actor": {"login": "user1"}, "created_at": "2023-01-01T00:00:00Z", "payload": {}, "repo": {"name": "test"}},
            {"id": 2, "type": "IssuesEvent", "actor": {"login": "user2"}, "created_at": "2023-01-01T00:01:00Z", "payload": {}, "repo": {"name": "test"}},
        ]
        
        min_events = 5  # Threshold is 5, we have 2
        
        with patch('data_ingestion.fetch_repo_events', return_value=mock_events):
            result = fetch_and_process_project_data("P1", "owner", "repo", min_events)
            
        self.assertIsNone(result, "Project should be filtered out (return None) when events < min_events")

    def test_project_passed_when_events_meet_threshold(self):
        """
        Verify that a project with events >= min_events returns a result dict.
        """
        # Create enough events to pass the filter
        mock_events = [
            {
                "id": i, 
                "type": "IssuesEvent", 
                "actor": {"login": f"user{i%3}"}, 
                "created_at": f"2023-01-01T00:0{i}Z", 
                "payload": {}, 
                "repo": {"name": "test"}
            }
            for i in range(10) # 10 events
        ]
        
        min_events = 5  # Threshold is 5, we have 10
        
        # Mock the identify_pairs_and_calculate_metrics to avoid complex logic in unit test
        with patch('data_ingestion.fetch_repo_events', return_value=mock_events):
            with patch('data_ingestion.identify_pairs_and_calculate_metrics') as mock_calc:
                # Mock return value for pairs and metrics
                mock_pairs = ["pair1", "pair2"]
                mock_metrics = {"pair1": MagicMock(mean_delay=10.0, response_time_variance=5.0)}
                mock_calc.return_value = (mock_pairs, mock_metrics)
                
                result = fetch_and_process_project_data("P1", "owner", "repo", min_events)
                
        self.assertIsNotNone(result, "Project should be processed when events >= min_events")
        self.assertEqual(result['event_count'], 10)
        self.assertIn('project_id', result)

    def test_bot_events_excluded_before_threshold_check(self):
        """
        Verify that bot events are excluded from the count before checking min_events.
        """
        # 3 real users + 2 bots = 5 raw events
        # min_events = 4
        # Expected: 3 real events -> Filtered out
        mock_events = [
            {"id": 1, "type": "IssuesEvent", "actor": {"login": "user1"}, "created_at": "2023-01-01T00:00:00Z", "payload": {}, "repo": {"name": "test"}},
            {"id": 2, "type": "IssuesEvent", "actor": {"login": "user2"}, "created_at": "2023-01-01T00:01:00Z", "payload": {}, "repo": {"name": "test"}},
            {"id": 3, "type": "IssuesEvent", "actor": {"login": "user3"}, "created_at": "2023-01-01T00:02:00Z", "payload": {}, "repo": {"name": "test"}},
            {"id": 4, "type": "IssuesEvent", "actor": {"login": "bot-user[bot]"}, "created_at": "2023-01-01T00:03:00Z", "payload": {}, "repo": {"name": "test"}},
            {"id": 5, "type": "IssuesEvent", "actor": {"login": "app[GitHub App]"}, "created_at": "2023-01-01T00:04:00Z", "payload": {}, "repo": {"name": "test"}},
        ]
        
        min_events = 4  # Threshold is 4
        
        with patch('data_ingestion.fetch_repo_events', return_value=mock_events):
            result = fetch_and_process_project_data("P1", "owner", "repo", min_events)
            
        # Only 3 real events remain, which is < 4. Should be None.
        self.assertIsNone(result, "Project should be filtered after bot exclusion reduces count below threshold")
