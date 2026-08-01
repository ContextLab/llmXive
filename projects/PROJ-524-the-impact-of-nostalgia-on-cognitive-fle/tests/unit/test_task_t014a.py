"""
Unit tests for code/task_t014a_create_cleaned_dataset.py.
Tests cleaned dataset creation logic.
"""
import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t014a_create_cleaned_dataset import (
    load_exclusion_log,
    load_mmse_flag,
    create_cleaned_dataset,
    save_cleaned_dataset
)


class TestLoadExclusionLog:
    def test_load_exclusion_log_exists(self):
        """Test loading existing exclusion log."""
        exclusion_data = {
            'ERR_MISSING_AGE_FIELD': 5,
            'ERR_MISSING_BIRTH_YEAR': 2,
            'ERR_MISSING_SCORE': 3
        }

        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = json.dumps(exclusion_data)
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            result = load_exclusion_log(Path("test.json"))
            assert result == exclusion_data

    def test_load_exclusion_log_missing(self):
        """Test loading missing exclusion log returns empty dict."""
        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            result = load_exclusion_log(Path("missing.json"))
            assert result == {}


class TestLoadMMSEFlag:
    def test_load_mmse_flag_true(self):
        """Test loading MMSE flag when true."""
        config_data = {'has_mmse': True}

        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = json.dumps(config_data)
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            result = load_mmse_flag(Path("config.json"))
            assert result is True

    def test_load_mmse_flag_false(self):
        """Test loading MMSE flag when false."""
        config_data = {'has_mmse': False}

        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.read_text.return_value = json.dumps(config_data)
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            result = load_mmse_flag(Path("config.json"))
            assert result is False

    def test_load_mmse_flag_missing(self):
        """Test loading MMSE flag when config is missing."""
        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_path.return_value.exists.return_value = False

            result = load_mmse_flag(Path("missing.json"))
            assert result is False


class TestCreateCleanedDataset:
    def test_create_cleaned_dataset_basic(self):
        """Test basic cleaned dataset creation."""
        raw_data = {
            'participant_id': ['P1', 'P2', 'P3'],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [10, 12, 8],
            'categories_completed': [5, 6, 7],
            'age': [65, 70, 75]
        }
        df = pd.DataFrame(raw_data)

        result = create_cleaned_dataset(df)

        assert 'participant_id' in result.columns
        assert 'stimulus_type' in result.columns
        assert 'perseverative_errors' in result.columns
        assert 'categories_completed' in result.columns
        assert 'age' in result.columns

    def test_create_cleaned_dataset_with_mmse(self):
        """Test cleaned dataset creation with MMSE column."""
        raw_data = {
            'participant_id': ['P1', 'P2'],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 6],
            'age': [65, 70],
            'MMSE': [28, 25]
        }
        df = pd.DataFrame(raw_data)

        result = create_cleaned_dataset(df)

        assert 'MMSE' in result.columns


class TestSaveCleanedDataset:
    def test_save_cleaned_dataset(self):
        """Test saving cleaned dataset to CSV."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'stimulus_type': ['nostalgia', 'control'],
            'perseverative_errors': [10, 12],
            'categories_completed': [5, 6],
            'age': [65, 70]
        })

        with patch('code.task_t014a_create_cleaned_dataset.Path') as mock_path:
            mock_file = MagicMock()
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            save_cleaned_dataset(df, Path("output.csv"))

            mock_file.to_csv.assert_called_once()
