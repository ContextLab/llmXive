"""
Unit tests for the filter module (T026).

Tests the functionality of splitting data by stimulus modality.
"""
import os
import sys
import json
import tempfile
import unittest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path so we can import the module
# We assume this test runs from the project root or code directory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.filter import (
    filter_by_modality, 
    load_trial_data, 
    write_output,
    VALID_MODALITIES,
    REQUIRED_COLUMNS
)

class TestFilterModality(unittest.TestCase):
    """Tests for the filter_by_modality function."""

    def setUp(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'trial_id': [1, 2, 3, 4],
            'stimulus_modality': ['visual', 'auditory', 'visual', 'auditory'],
            'source_label': ['internal', 'external', 'internal', 'external'],
            'participant_response': [1, 0, 1, 1],
            'confidence_rating': [0.8, 0.6, 0.9, 0.5]
        })

    def test_filter_visual(self):
        """Test filtering for visual modality."""
        result = filter_by_modality(self.test_data, 'visual')
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result['stimulus_modality'] == 'visual'))
        self.assertEqual(set(result['trial_id']), {1, 3})

    def test_filter_auditory(self):
        """Test filtering for auditory modality."""
        result = filter_by_modality(self.test_data, 'auditory')
        self.assertEqual(len(result), 2)
        self.assertTrue(all(result['stimulus_modality'] == 'auditory'))
        self.assertEqual(set(result['trial_id']), {2, 4})

    def test_filter_case_insensitive(self):
        """Test that filtering is case insensitive."""
        result = filter_by_modality(self.test_data, 'VISUAL')
        self.assertEqual(len(result), 2)
        result = filter_by_modality(self.test_data, 'Visual')
        self.assertEqual(len(result), 2)

    def test_filter_invalid_modality(self):
        """Test that an invalid modality raises ValueError."""
        with self.assertRaises(ValueError):
            filter_by_modality(self.test_data, 'tactile')
        
    def test_filter_empty_result(self):
        """Test filtering when no data matches."""
        result = filter_by_modality(self.test_data, 'tactile')
        self.assertEqual(len(result), 0)

class TestFilterHelpers(unittest.TestCase):
    """Tests for helper functions in the filter module."""

    def test_write_output(self):
        """Test writing output to a CSV file."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            write_output(df, tmp_path)
            self.assertTrue(tmp_path.exists())
            loaded_df = pd.read_csv(tmp_path)
            self.assertEqual(len(loaded_df), 3)
            self.assertEqual(list(loaded_df.columns), ['col1', 'col2'])
        finally:
            if tmp_path.exists():
                os.unlink(tmp_path)

if __name__ == '__main__':
    unittest.main()