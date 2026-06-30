"""
Unit tests for the report generation module (src/report/generate.py).

Tests cover:
- Correlation direction determination
- Effect size magnitude classification
- Report generation from mock bootstrap data
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_dir))

from src.report.generate import (
    determine_correlation_direction,
    calculate_effect_size_magnitude,
    generate_primary_analysis_report,
    load_bootstrap_results
)


class TestCorrelationDirection(unittest.TestCase):
    """Tests for determine_correlation_direction function."""

    def test_positive_correlation(self):
        """Test detection of positive correlation."""
        self.assertEqual(determine_correlation_direction(0.5), "positive")
        self.assertEqual(determine_correlation_direction(0.001), "positive")
        self.assertEqual(determine_correlation_direction(1.0), "positive")

    def test_negative_correlation(self):
        """Test detection of negative correlation."""
        self.assertEqual(determine_correlation_direction(-0.5), "negative")
        self.assertEqual(determine_correlation_direction(-0.001), "negative")
        self.assertEqual(determine_correlation_direction(-1.0), "negative")

    def test_zero_correlation(self):
        """Test detection of zero correlation."""
        self.assertEqual(determine_correlation_direction(0.0), "zero")
        self.assertEqual(determine_correlation_direction(0.0005), "zero")


class TestEffectSizeMagnitude(unittest.TestCase):
    """Tests for calculate_effect_size_magnitude function."""

    def test_negligible(self):
        """Test classification of negligible effect size."""
        self.assertEqual(calculate_effect_size_magnitude(0.05), "negligible")
        self.assertEqual(calculate_effect_size_magnitude(0.09), "negligible")

    def test_small(self):
        """Test classification of small effect size."""
        self.assertEqual(calculate_effect_size_magnitude(0.10), "small")
        self.assertEqual(calculate_effect_size_magnitude(0.29), "small")

    def test_medium(self):
        """Test classification of medium effect size."""
        self.assertEqual(calculate_effect_size_magnitude(0.30), "medium")
        self.assertEqual(calculate_effect_size_magnitude(0.49), "medium")

    def test_large(self):
        """Test classification of large effect size."""
        self.assertEqual(calculate_effect_size_magnitude(0.50), "large")
        self.assertEqual(calculate_effect_size_magnitude(0.80), "large")


class TestGenerateReport(unittest.TestCase):
    """Tests for generate_primary_analysis_report function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bootstrap_data = {
            'r_value': 0.45,
            'p_value': 0.002,
            'ci_lower': 0.32,
            'ci_upper': 0.58,
            'bootstrap_count': 1000,
            'n_samples': 50
        }
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, 'test_report.json')

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        os.rmdir(self.temp_dir)

    def test_report_structure(self):
        """Test that the generated report has the expected structure."""
        report = generate_primary_analysis_report(self.mock_bootstrap_data, self.output_path)
        
        # Check top-level keys
        self.assertIn('analysis_type', report)
        self.assertIn('metrics', report)
        self.assertIn('sample_info', report)
        self.assertIn('interpretation', report)
        self.assertIn('metadata', report)

    def test_report_values(self):
        """Test that the report contains correct values."""
        report = generate_primary_analysis_report(self.mock_bootstrap_data, self.output_path)
        
        self.assertEqual(report['metrics']['correlation_coefficient'], 0.45)
        self.assertEqual(report['metrics']['p_value'], 0.002)
        self.assertEqual(report['metrics']['direction'], 'positive')
        self.assertEqual(report['metrics']['magnitude'], 'medium')
        self.assertEqual(report['sample_info']['total_participants'], 50)
        self.assertEqual(report['sample_info']['bootstrap_resamples'], 1000)

    def test_file_written(self):
        """Test that the report file is actually written to disk."""
        generate_primary_analysis_report(self.mock_bootstrap_data, self.output_path)
        
        self.assertTrue(os.path.exists(self.output_path))
        
        # Verify file content
        with open(self.output_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['metrics']['correlation_coefficient'], 0.45)

    def test_missing_r_value(self):
        """Test that ValueError is raised when r_value is missing."""
        bad_data = self.mock_bootstrap_data.copy()
        del bad_data['r_value']
        
        with self.assertRaises(ValueError):
            generate_primary_analysis_report(bad_data, self.output_path)


class TestLoadBootstrapResults(unittest.TestCase):
    """Tests for load_bootstrap_results function."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump({'r_value': 0.5}, temp_file)
        temp_file.close()
        
        try:
            data = load_bootstrap_results(temp_file.name)
            self.assertEqual(data['r_value'], 0.5)
        finally:
            os.unlink(temp_file.name)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_bootstrap_results('/nonexistent/path/file.json')


if __name__ == '__main__':
    unittest.main()