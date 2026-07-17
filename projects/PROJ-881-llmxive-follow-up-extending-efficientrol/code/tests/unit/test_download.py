import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.data.download import (
    download_gsm8k_subset,
    download_minigrid_subset,
)

class TestDownloadModule:
    @patch('src.data.download.load_dataset')
    def test_download_gsm8k_subset(self, mock_load_dataset):
        mock_dataset = MagicMock()
        mock_dataset['train'] = [{'question': 'Test', 'answer': 'Ans'}]
        mock_load_dataset.return_value = mock_dataset

        data = download_gsm8k_subset(limit=10)
        assert len(data) == 10
        mock_load_dataset.assert_called_once()

    @patch('src.data.download.load_dataset')
    def test_download_minigrid_subset(self, mock_load_dataset):
        mock_dataset = MagicMock()
        mock_dataset['train'] = [{'instruction': 'Go', 'goal': 'Goal'}]
        mock_load_dataset.return_value = mock_dataset

        data = download_minigrid_subset(limit=10)
        assert len(data) == 10
        mock_load_dataset.assert_called_once()
