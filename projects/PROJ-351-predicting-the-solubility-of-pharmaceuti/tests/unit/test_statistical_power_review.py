"""
Unit tests for T049: Statistical Power Review module.

Tests the statistical power review logic without requiring actual
statistical test results from T028.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.statistical_power_review import (
    interpret_statistical_power,
    analyze_effect_size,
    generate_power_review_report,
    load_statistical_results
)


class TestInterpretStatisticalPower(unittest.TestCase):
    """Tests for interpret_statistical_power function."""

    def test_power_above_threshold(self):
        """Test interpretation when power exceeds threshold."""
        result = interpret_statistical_power(power=0.85, threshold=0.8)
        
        self.assertTrue(result['meets_threshold'])
        self.assertEqual(result['interpretation'], 'SUFFICIENT')
        self.assertIn('adequate statistical power', result['impact_statement'].lower())

    def test_power_below_threshold(self):
        """Test interpretation when power is below threshold."""
        result = interpret_statistical_power(power=0.65, threshold=0.8)
        
        self.assertFalse(result['meets_threshold'])
        self.assertEqual(result['interpretation'], 'INSUFFICIENT')
        self.assertIn('low statistical power', result['impact_statement'].lower())
        self.assertIn('type ii error', result['impact_statement'].lower())

    def test_power_at_threshold(self):
        """Test interpretation when power equals threshold."""
        result = interpret_statistical_power(power=0.8, threshold=0.8)
        
        self.assertTrue(result['meets_threshold'])
        self.assertEqual(result['interpretation'], 'SUFFICIENT')

    def test_custom_threshold(self):
        """Test with custom threshold value."""
        result = interpret_statistical_power(power=0.75, threshold=0.7)
        
        self.assertTrue(result['meets_threshold'])
        self.assertEqual(result['threshold'], 0.7)


class TestAnalyzeEffectSize(unittest.TestCase):
    """Tests for analyze_effect_size function."""

    def test_negligible_effect(self):
        """Test negligible effect size (|d| < 0.2)."""
        result = analyze_effect_size(cohens_d=0.15)
        
        self.assertEqual(result['magnitude'], 'negligible')
        self.assertAlmostEqual(result['cohens_d'], 0.15)

    def test_small_effect(self):
        """Test small effect size (0.2 <= |d| < 0.5)."""
        result = analyze_effect_size(cohens_d=0.35)
        
        self.assertEqual(result['magnitude'], 'small')

    def test_medium_effect(self):
        """Test medium effect size (0.5 <= |d| < 0.8)."""
        result = analyze_effect_size(cohens_d=0.65)
        
        self.assertEqual(result['magnitude'], 'medium')

    def test_large_effect(self):
        """Test large effect size (|d| >= 0.8)."""
        result = analyze_effect_size(cohens_d=1.2)
        
        self.assertEqual(result['magnitude'], 'large')

    def test_negative_effect_size(self):
        """Test negative Cohen's d (magnitude should be positive)."""
        result = analyze_effect_size(cohens_d=-0.65)
        
        self.assertEqual(result['magnitude'], 'medium')
        self.assertEqual(result['cohens_d'], -0.65)


class TestGeneratePowerReviewReport(unittest.TestCase):
    """Tests for generate_power_review_report function."""

    def test_high_power_significant_result(self):
        """Test report generation with high power and significant p-value."""
        stats_results = {
            'p_value': 0.03,
            'effect_size_cohens_d': 0.65,
            'statistical_power': 0.85,
            't_statistic': 2.45,
            'degrees_of_freedom': 1100,
            'test_type': 'nadeau_corrected_ttest'
        }
        
        report = generate_power_review_report(stats_results)
        
        self.assertEqual(report['task_id'], 'T049')
        self.assertTrue(report['power_analysis']['meets_threshold'])
        self.assertIn('STATISTICALLY SIGNIFICANT AND ROBUST', report['conclusion']['status'])

    def test_low_power_non_significant_result(self):
        """Test report generation with low power and non-significant p-value."""
        stats_results = {
            'p_value': 0.15,
            'effect_size_cohens_d': 0.25,
            'statistical_power': 0.55,
            't_statistic': 1.45,
            'degrees_of_freedom': 1100,
            'test_type': 'nadeau_corrected_ttest'
        }
        
        report = generate_power_review_report(stats_results)
        
        self.assertFalse(report['power_analysis']['meets_threshold'])
        self.assertIn('NOT SIGNIFICANT AND LOW POWER', report['conclusion']['status'])
        self.assertGreater(len(report['limitations']), 0)

    def test_report_structure(self):
        """Test that report contains all required fields."""
        stats_results = {
            'p_value': 0.04,
            'effect_size_cohens_d': 0.45,
            'statistical_power': 0.78,
            't_statistic': 2.1,
            'degrees_of_freedom': 1100,
            'test_type': 'nadeau_corrected_ttest'
        }
        
        report = generate_power_review_report(stats_results)
        
        required_fields = [
            'task_id', 'review_type', 'statistical_results_summary',
            'power_analysis', 'effect_size_analysis', 'conclusion',
            'limitations', 'next_steps'
        ]
        
        for field in required_fields:
            self.assertIn(field, report)


class TestLoadStatisticalResults(unittest.TestCase):
    """Tests for load_statistical_results function."""

    def test_load_valid_results(self):
        """Test loading valid statistical results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'p_value': 0.03,
                'effect_size_cohens_d': 0.65,
                'statistical_power': 0.85,
                't_statistic': 2.45,
                'degrees_of_freedom': 1100,
                'test_type': 'nadeau_corrected_ttest'
            }, f)
            temp_path = Path(f.name)
        
        try:
            # Mock logger
            mock_logger = MagicMock()
            results = load_statistical_results(temp_path, mock_logger)
            
            self.assertEqual(results['p_value'], 0.03)
            self.assertEqual(results['statistical_power'], 0.85)
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Test error handling for missing file."""
        mock_logger = MagicMock()
        non_existent_path = Path('/non/existent/path/results.json')
        
        with self.assertRaises(FileNotFoundError):
            load_statistical_results(non_existent_path, mock_logger)

    def test_missing_required_fields(self):
        """Test error handling for missing required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'p_value': 0.03,
                # Missing other required fields
            }, f)
            temp_path = Path(f.name)
        
        try:
            mock_logger = MagicMock()
            
            with self.assertRaises(ValueError) as context:
                load_statistical_results(temp_path, mock_logger)
            
            self.assertIn('missing required fields', str(context.exception).lower())
        finally:
            temp_path.unlink()

    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_path = Path(f.name)
        
        try:
            mock_logger = MagicMock()
            
            with self.assertRaises(json.JSONDecodeError):
                load_statistical_results(temp_path, mock_logger)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main()