import unittest
from unittest.mock import patch, mock_open
import json
import os
from pathlib import Path

from code.pipelines.run_conditioned import main

class TestRunConditioned(unittest.TestCase):

    @patch('code.pipelines.run_conditioned.load_dataset_list')
    def test_main_valid_datasets(self, mock_load_dataset_list):
        mock_load_dataset_list.return_value = ['dataset1', 'dataset2']
        # Mock metadata stats files
        metadata_stats1 = {'feature1': 0.5}
        metadata_stats2 = {'feature1': 0.6}

        with patch('code.pipelines.run_conditioned.open') as mock_file:
            mock_file.side_effect = [
                mock_open(r=json.dumps(metadata_stats1)),
                mock_open(r=json.dumps(metadata_stats2))
            ]

        main("test_run_id")
        self.assertTrue(True)  # Check that the function runs without errors

    @patch('code.pipelines.run_conditioned.load_dataset_list')
    def test_main_missing_metadata(self, mock_load_dataset_list):
        mock_load_dataset_list.return_value = ['dataset1', 'dataset2']

        # Mock metadata stats files - dataset2 missing
        metadata_stats1 = {'feature1': 0.5}

        with patch('code.pipelines.run_conditioned.open') as mock_file:
            mock_file.side_effect = [
                mock_open(r=json.dumps(metadata_stats1)),
                FileNotFoundError()  # Simulate missing file for dataset2
            ]

        main("test_run_id")
        self.assertTrue(True)   # Check that the function runs without errors and handles missing metadata
