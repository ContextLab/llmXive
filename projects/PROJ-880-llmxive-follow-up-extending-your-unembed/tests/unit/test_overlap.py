"""
Unit tests for overlap_calculator module.

Tests the overlap ratio calculation logic for T022.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

from overlap_calculator import (
    calculate_overlap_ratio,
    load_token_rankings,
    generate_overlap_report
)
from config import load_config


class TestCalculateOverlapRatio:
    """Tests for the calculate_overlap_ratio function."""

    def test_identical_lists(self):
        """Test overlap ratio when lists are identical."""
        list_a = ['token1', 'token2', 'token3']
        list_b = ['token1', 'token2', 'token3']

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 3
        assert result['ratio'] == 1.0
        assert result['size_a'] == 3
        assert result['size_b'] == 3
        assert result['overlap_tokens'] == ['token1', 'token2', 'token3']

    def test_no_overlap(self):
        """Test overlap ratio when lists have no common elements."""
        list_a = ['token1', 'token2', 'token3']
        list_b = ['token4', 'token5', 'token6']

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 0
        assert result['ratio'] == 0.0
        assert result['size_a'] == 3
        assert result['size_b'] == 3
        assert result['overlap_tokens'] == []

    def test_partial_overlap(self):
        """Test overlap ratio with partial overlap."""
        list_a = ['token1', 'token2', 'token3', 'token4']
        list_b = ['token3', 'token4', 'token5', 'token6']

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 2
        assert result['ratio'] == 0.5  # 2 / min(4, 4)
        assert set(result['overlap_tokens']) == {'token3', 'token4'}

    def test_different_sizes_with_overlap(self):
        """Test overlap ratio when lists have different sizes."""
        list_a = ['token1', 'token2', 'token3']  # size 3
        list_b = ['token1', 'token2', 'token3', 'token4', 'token5']  # size 5

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 3
        assert result['ratio'] == 1.0  # 3 / min(3, 5) = 3/3
        assert result['size_a'] == 3
        assert result['size_b'] == 5

    def test_with_k_parameter(self):
        """Test overlap ratio with k parameter to limit to top-k."""
        list_a = ['token1', 'token2', 'token3', 'token4', 'token5']
        list_b = ['token1', 'token2', 'token6', 'token7', 'token8']

        result = calculate_overlap_ratio(list_a, list_b, k=3)

        # After truncation: ['token1', 'token2', 'token3'] vs ['token1', 'token2', 'token6']
        assert result['overlap_count'] == 2
        assert result['ratio'] == 2/3
        assert result['size_a'] == 3
        assert result['size_b'] == 3

    def test_empty_lists(self):
        """Test overlap ratio with empty lists."""
        list_a = []
        list_b = []

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 0
        assert result['ratio'] == 0.0
        assert result['size_a'] == 0
        assert result['size_b'] == 0

    def test_one_empty_list(self):
        """Test overlap ratio when one list is empty."""
        list_a = ['token1', 'token2']
        list_b = []

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 0
        assert result['ratio'] == 0.0
        assert result['size_a'] == 2
        assert result['size_b'] == 0

    def test_jaccard_index(self):
        """Test that Jaccard index is calculated correctly."""
        list_a = ['token1', 'token2', 'token3']
        list_b = ['token2', 'token3', 'token4']

        result = calculate_overlap_ratio(list_a, list_b)

        # Intersection: {token2, token3} = 2
        # Union: {token1, token2, token3, token4} = 4
        expected_jaccard = 2 / 4
        assert abs(result['jaccard_index'] - expected_jaccard) < 1e-10

    def test_case_sensitivity(self):
        """Test that token comparison is case-sensitive."""
        list_a = ['Token1', 'token2']
        list_b = ['token1', 'Token2']

        result = calculate_overlap_ratio(list_a, list_b)

        assert result['overlap_count'] == 0
        assert result['ratio'] == 0.0

    def test_duplicate_tokens_in_list(self):
        """Test behavior with duplicate tokens in input lists."""
        list_a = ['token1', 'token1', 'token2']
        list_b = ['token1', 'token2', 'token2']

        result = calculate_overlap_ratio(list_a, list_b)

        # Sets are used internally, so duplicates are removed
        assert result['overlap_count'] == 2  # token1 and token2
        assert result['ratio'] == 1.0  # 2/2


class TestLoadTokenRankings:
    """Tests for the load_token_rankings function."""

    @patch('overlap_calculator.get_path')
    @patch('builtins.open', new_callable=MagicMock)
    def test_load_valid_rankings(self, mock_open, mock_get_path):
        """Test loading valid token rankings."""
        mock_get_path.return_value = '/fake/path/rankings.json'

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps({
            'token_rankings': {
                'en': ['token1', 'token2'],
                'fr': ['token3', 'token4']
            }
        })
        mock_open.return_value = mock_file

        config = {}
        rankings = load_token_rankings(config)

        assert 'en' in rankings
        assert 'fr' in rankings
        assert rankings['en'] == ['token1', 'token2']
        assert rankings['fr'] == ['token3', 'token4']

    @patch('overlap_calculator.get_path')
    @patch('pathlib.Path.exists', return_value=False)
    def test_file_not_found(self, mock_exists, mock_get_path):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        mock_get_path.return_value = '/fake/path/rankings.json'

        config = {}

        with pytest.raises(FileNotFoundError, match="Token attribution report not found"):
            load_token_rankings(config)

    @patch('overlap_calculator.get_path')
    @patch('builtins.open', new_callable=MagicMock)
    def test_invalid_format_missing_key(self, mock_open, mock_get_path):
        """Test that ValueError is raised when 'token_rankings' key is missing."""
        mock_get_path.return_value = '/fake/path/rankings.json'

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = json.dumps({
            'other_key': ['token1']
        })
        mock_open.return_value = mock_file

        config = {}

        with pytest.raises(ValueError, match="Invalid token attribution report format"):
            load_token_rankings(config)


class TestGenerateOverlapReport:
    """Tests for the generate_overlap_report function."""

    @patch('overlap_calculator.load_token_rankings')
    @patch('overlap_calculator.get_hyperparameter', return_value=10)
    @patch('overlap_calculator.get_path', return_value='/fake/output.json')
    @patch('overlap_calculator.ensure_dirs')
    @patch('builtins.open', new_callable=MagicMock)
    def test_generate_report_with_multiple_languages(
        self, mock_open, mock_ensure_dirs, mock_get_path, mock_get_hyper, mock_load_rankings
    ):
        """Test generating overlap report with multiple languages."""
        mock_load_rankings.return_value = {
            'en': ['token1', 'token2', 'token3', 'token4', 'token5'],
            'fr': ['token1', 'token2', 'token6', 'token7', 'token8'],
            'zh': ['token3', 'token4', 'token9', 'token10', 'token11']
        }

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        config = {'timestamp': 'test'}
        report = generate_overlap_report(config)

        assert 'comparisons' in report
        assert 'fr' in report['comparisons']
        assert 'zh' in report['comparisons']
        assert report['baseline_language'] == 'en'

        # Check fr overlap: token1, token2 shared with en
        fr_metrics = report['comparisons']['fr']
        assert fr_metrics['overlap_count'] == 2
        assert fr_metrics['top_k'] == 10

        # Verify file was written
        mock_open.assert_called_once()
        mock_ensure_dirs.assert_called_once()

    @patch('overlap_calculator.load_token_rankings')
    @patch('overlap_calculator.get_hyperparameter', return_value=10)
    @patch('overlap_calculator.get_path', return_value='/fake/output.json')
    @patch('overlap_calculator.ensure_dirs')
    @patch('builtins.open', new_callable=MagicMock)
    def test_no_english_baseline(self, mock_open, mock_ensure_dirs, mock_get_path, mock_get_hyper, mock_load_rankings):
        """Test that ValueError is raised when English is not in rankings."""
        mock_load_rankings.return_value = {
            'fr': ['token1', 'token2'],
            'zh': ['token3', 'token4']
        }

        config = {}

        with pytest.raises(ValueError, match="English.*not found in token rankings"):
            generate_overlap_report(config)

    @patch('overlap_calculator.load_token_rankings')
    @patch('overlap_calculator.get_hyperparameter', return_value=10)
    @patch('overlap_calculator.get_path', return_value='/fake/output.json')
    @patch('overlap_calculator.ensure_dirs')
    @patch('builtins.open', new_callable=MagicMock)
    def test_no_non_english_languages(self, mock_open, mock_ensure_dirs, mock_get_path, mock_get_hyper, mock_load_rankings):
        """Test handling when only English is present."""
        mock_load_rankings.return_value = {
            'en': ['token1', 'token2']
        }

        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        config = {}
        report = generate_overlap_report(config)

        assert report['comparisons'] == {}
        assert 'No non-English languages' in report['message']
        assert report['aggregate_statistics']['languages_compared'] == 0
