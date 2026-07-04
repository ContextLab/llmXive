"""
Unit tests for the data download module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd

# Add src to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data import download
from src.utils.config import get_project_root


class TestDownloadModule(unittest.TestCase):

    @patch('src.data.download.fetch_url_content')
    def test_download_fivethirtyeight_polls_success(self, mock_fetch):
        """Test successful download of FiveThirtyEight polls."""
        mock_df = pd.DataFrame({'date': ['2020-10-01'], 'pollster': ['ABC']})
        mock_fetch.return_value = mock_df

        result = download.download_fivethirtyeight_polls()

        mock_fetch.assert_called_once_with(download.FIVETHIRYEIGHT_BASE_URL + "poll-data.csv")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch('src.data.download.fetch_url_content')
    def test_download_fivethirtyeight_polls_failure(self, mock_fetch):
        """Test handling of download failure."""
        mock_fetch.return_value = None

        result = download.download_fivethirtyeight_polls()

        self.assertIsNone(result)

    @patch('src.data.download.fetch_url_content')
    def test_download_election_outcomes_state_success(self, mock_fetch):
        """Test successful download of state outcomes."""
        mock_df = pd.DataFrame({'state': ['NY'], 'result': ['D']})
        # First call (State) returns data
        mock_fetch.side_effect = [mock_df, None]

        result = download.download_election_outcomes()

        # Should call State URL first
        self.assertEqual(mock_fetch.call_count, 1)
        self.assertIn('state_results', mock_fetch.call_args_list[0][0][0])
        self.assertIsInstance(result, pd.DataFrame)

    @patch('src.data.download.fetch_url_content')
    def test_download_election_outcomes_fallback_to_national(self, mock_fetch):
        """Test fallback to national outcomes when state fails."""
        mock_state_df = None
        mock_national_df = pd.DataFrame({'result': ['D']})
        # First call (State) returns None, second (National) returns data
        mock_fetch.side_effect = [mock_state_df, mock_national_df]

        result = download.download_election_outcomes()

        self.assertEqual(mock_fetch.call_count, 2)
        self.assertIn('national_results', mock_fetch.call_args_list[1][0][0])
        self.assertIsInstance(result, pd.DataFrame)

    @patch('src.data.download.get_raw_data_path')
    @patch('src.data.download.os.makedirs')
    @patch('src.data.download.download_fivethirtyeight_polls')
    @patch('src.data.download.download_election_outcomes')
    def test_run_download_pipeline(self, mock_outcomes, mock_polls, mock_makedirs, mock_get_path):
        """Test the full pipeline execution."""
        # Setup mocks
        mock_polls_df = pd.DataFrame({'col': [1]})
        mock_outcomes_df = pd.DataFrame({'col': [2]})
        mock_polls.return_value = mock_polls_df
        mock_outcomes.return_value = mock_outcomes_df
        mock_get_path.return_value = Path("/tmp/raw")

        success = download.run_download_pipeline()

        self.assertTrue(success)
        mock_makedirs.assert_called_once()
        # Verify save calls (mocked via to_csv on the dataframe)
        # We can't easily mock the file write without more complex setup, 
        # but we verify the logic flow.
        mock_polls.assert_called_once()
        mock_outcomes.assert_called_once()

    @patch('src.data.download.fetch_url_content')
    def test_run_download_pipeline_failure_polls(self, mock_fetch):
        """Test pipeline failure when polls cannot be downloaded."""
        mock_fetch.return_value = None
        
        # We need to patch get_raw_data_path and makedirs too
        with patch('src.data.download.get_raw_data_path') as mock_path, \
             patch('src.data.download.os.makedirs'):
            mock_path.return_value = Path("/tmp/raw")
            
            success = download.run_download_pipeline()
            self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()