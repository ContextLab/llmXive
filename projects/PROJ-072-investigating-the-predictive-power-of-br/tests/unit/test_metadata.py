"""
Unit tests for metadata generation module (T015).

Tests the parsing logic and mapping generation without requiring
the full dataset to be present (mocking file system interactions).
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.metadata import (
    parse_diagnostic_label,
    load_exclusion_log,
    generate_subject_labels_mapping,
    save_subject_labels
)

class TestDiagnosticLabelParsing(unittest.TestCase):
    """Test the parse_diagnostic_label function."""

    def test_valid_control_labels(self):
        """Test various strings that should map to '0' (Control)."""
        valid_controls = ['0', 'control', 'hc', 'healthy', 'healthy_control', 'Control', 'HC']
        for label in valid_controls:
            with self.subTest(label=label):
                self.assertEqual(parse_diagnostic_label(label), '0')

    def test_valid_patient_labels(self):
        """Test various strings that should map to '1' (Schizophrenia)."""
        valid_patients = ['1', 'sz', 'schizophrenia', 'patient', 'schizophrenic', 'SZ', 'Patient']
        for label in valid_patients:
            with self.subTest(label=label):
                self.assertEqual(parse_diagnostic_label(label), '1')

    def test_invalid_labels(self):
        """Test that invalid labels return None."""
        invalid_labels = ['unknown', 'missing', '2', 'other', '']
        for label in invalid_labels:
            with self.subTest(label=label):
                self.assertIsNone(parse_diagnostic_label(label))

    def test_none_input(self):
        """Test that None input returns None."""
        self.assertIsNone(parse_diagnostic_label(None))

class TestExclusionLogLoading(unittest.TestCase):
    """Test loading the exclusion log."""

    def test_log_not_exists(self):
        """Test behavior when exclusion log does not exist."""
        with patch('preprocessing.metadata.EXCLUSION_LOG_FILE', Path('/nonexistent/path.txt')):
            result = load_exclusion_log()
            self.assertEqual(result, [])

    def test_log_with_entries(self):
        """Test loading a log with entries."""
        mock_content = "# Exclusion Log\nsub-01\nsub-02\n# Reason: Motion\nsub-03\n"
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with patch('preprocessing.metadata.EXCLUSION_LOG_FILE', Path('/fake/path.txt')):
                result = load_exclusion_log()
                self.assertEqual(result, ['sub-01', 'sub-02', 'sub-03'])

class TestSaveSubjectLabels(unittest.TestCase):
    """Test saving the subject labels CSV."""

    def test_save_creates_file(self):
        """Test that the function creates the file and writes correct headers."""
        mapping = {'01': '0', '02': '1', '03': '0'}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_labels.csv'
            
            save_subject_labels(mapping, output_path)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                self.assertEqual(headers, ['subject_id', 'label'])
                
                rows = list(reader)
                self.assertEqual(len(rows), 3)
                # Check sorting
                self.assertEqual(rows[0][0], '01')
                self.assertEqual(rows[1][0], '02')
                self.assertEqual(rows[2][0], '03')

    def test_save_empty_mapping(self):
        """Test saving an empty mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'empty_labels.csv'
            save_subject_labels({}, output_path)
            
            self.assertTrue(output_path.exists())
            with open(output_path, 'r') as f:
                content = f.read()
                self.assertIn('subject_id,label', content)
                self.assertEqual(len(content.strip().split('\n')), 1) # Only header

class TestGenerateSubjectLabelsMapping(unittest.TestCase):
    """Test the full mapping generation logic."""

    @patch('preprocessing.metadata.get_all_subject_ids')
    @patch('preprocessing.metadata.load_exclusion_log')
    @patch('preprocessing.metadata.load_subject_status')
    @patch('preprocessing.metadata.get_diagnostic_labels_from_participants')
    def test_full_mapping_generation(
        self, 
        mock_get_labels, 
        mock_load_status, 
        mock_load_excl, 
        mock_get_all
    ):
        """Test the end-to-end logic of mapping generation."""
        # Setup mocks
        mock_get_all.return_value = ['01', '02', '03', '04']
        mock_load_excl.return_value = ['02'] # Exclude 02
        mock_load_status.return_value = {'01': {'flag': 'OK'}}
        mock_get_labels.return_value = {
            '01': '0', # Control
            '02': '1', # Patient (but excluded)
            '03': None, # Missing label
            '04': '1'  # Patient
        }

        result = generate_subject_labels_mapping()

        # 02 is excluded, 03 has no label
        self.assertEqual(len(result), 2)
        self.assertEqual(result['01'], '0')
        self.assertEqual(result['04'], '1')
        self.assertNotIn('02', result)
        self.assertNotIn('03', result)

    @patch('preprocessing.metadata.get_all_subject_ids')
    @patch('preprocessing.metadata.load_exclusion_log')
    @patch('preprocessing.metadata.load_subject_status')
    @patch('preprocessing.metadata.get_diagnostic_labels_from_participants')
    def test_missing_labels_excluded(
        self, 
        mock_get_labels, 
        mock_load_status, 
        mock_load_excl, 
        mock_get_all
    ):
        """Test that subjects with missing labels are excluded."""
        mock_get_all.return_value = ['01']
        mock_load_excl.return_value = []
        mock_load_status.return_value = {}
        mock_get_labels.return_value = {'01': None}

        result = generate_subject_labels_mapping()
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()