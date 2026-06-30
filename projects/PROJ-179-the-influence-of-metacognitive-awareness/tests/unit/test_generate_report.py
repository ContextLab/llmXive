import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.report.generate import (
    apply_bonferroni_correction,
    apply_bh_correction,
    generate_robustness_report,
    load_bootstrap_results
)

class TestMultipleComparisonCorrection(unittest.TestCase):
    """Test cases for multiple comparison correction methods."""

    def test_bonferroni_correction_single(self):
        """Test Bonferroni correction with a single p-value."""
        p_values = [0.05]
        corrected = apply_bonferroni_correction(p_values)
        self.assertEqual(len(corrected), 1)
        self.assertEqual(corrected[0], 0.05)

    def test_bonferroni_correction_multiple(self):
        """Test Bonferroni correction with multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        corrected = apply_bonferroni_correction(p_values)
        # With m=3, corrections should be 0.03, 0.15, 0.30
        self.assertAlmostEqual(corrected[0], 0.03, places=5)
        self.assertAlmostEqual(corrected[1], 0.15, places=5)
        self.assertAlmostEqual(corrected[2], 0.30, places=5)

    def test_bonferroni_capped_at_one(self):
        """Test that Bonferroni correction caps at 1.0."""
        p_values = [0.5, 0.6]
        corrected = apply_bonferroni_correction(p_values)
        self.assertEqual(corrected[0], 1.0)
        self.assertEqual(corrected[1], 1.0)

    def test_bh_correction_single(self):
        """Test BH correction with a single p-value."""
        p_values = [0.05]
        corrected = apply_bh_correction(p_values)
        self.assertEqual(len(corrected), 1)
        self.assertEqual(corrected[0], 0.05)

    def test_bh_correction_multiple(self):
        """Test BH correction with multiple p-values."""
        p_values = [0.01, 0.05, 0.10]
        corrected = apply_bh_correction(p_values)
        # BH is more lenient than Bonferroni
        self.assertLessEqual(corrected[0], 0.03)
        self.assertLessEqual(corrected[1], 0.075)
        self.assertLessEqual(corrected[2], 0.10)

    def test_bh_monotonicity(self):
        """Test that BH corrected p-values are monotonic."""
        p_values = [0.01, 0.05, 0.10, 0.20]
        corrected = apply_bh_correction(p_values)
        # The corrected p-values should maintain the order of original p-values
        sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
        for i in range(len(sorted_indices) - 1):
            idx1, idx2 = sorted_indices[i], sorted_indices[i+1]
            self.assertLessEqual(corrected[idx1], corrected[idx2])

    def test_empty_p_values(self):
        """Test correction methods with empty input."""
        self.assertEqual(apply_bonferroni_correction([]), [])
        self.assertEqual(apply_bh_correction([]), [])

class TestRobustnessReportGeneration(unittest.TestCase):
    """Test cases for robustness report generation."""

    def setUp(self):
        """Set up temporary files and test data."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.results_dir = Path(self.temp_dir.name)
        
        # Create a mock bootstrap results CSV
        self.mock_csv = self.results_dir / "mock_bootstrap.csv"
        data = {
            'modality': ['visual', 'auditory'],
            'r': [0.45, 0.32],
            'p_value': [0.001, 0.04],
            'ci_lower': [0.25, 0.10],
            'ci_upper': [0.65, 0.54]
        }
        pd.DataFrame(data).to_csv(self.mock_csv, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_generate_robustness_report_bonferroni(self):
        """Test robustness report generation with Bonferroni correction."""
        output_file = self.results_dir / "robustness_report.json"
        
        report = generate_robustness_report(
            bootstrap_results_path=str(self.mock_csv),
            output_path=str(output_file),
            correction_method="bonferroni"
        )
        
        # Verify file was created
        self.assertTrue(output_file.exists())
        
        # Verify report structure
        self.assertIn('analysis_type', report)
        self.assertEqual(report['analysis_type'], 'modality_specific_robustness')
        self.assertIn('correction_method', report)
        self.assertEqual(report['correction_method'], 'bonferroni')
        self.assertIn('results', report)
        self.assertEqual(len(report['results']), 2)
        
        # Verify correction was applied
        for result in report['results']:
            self.assertIn('corrected_p_value', result)
            self.assertIn('raw_p_value', result)
            self.assertGreaterEqual(result['corrected_p_value'], result['raw_p_value'])

    def test_generate_robustness_report_bh(self):
        """Test robustness report generation with BH correction."""
        output_file = self.results_dir / "robustness_report_bh.json"
        
        report = generate_robustness_report(
            bootstrap_results_path=str(self.mock_csv),
            output_path=str(output_file),
            correction_method="bh"
        )
        
        # Verify file was created
        self.assertTrue(output_file.exists())
        
        # Verify correction method
        self.assertEqual(report['correction_method'], 'bh')
        
        # Verify BH is less conservative than Bonferroni
        report_bonf = generate_robustness_report(
            bootstrap_results_path=str(self.mock_csv),
            output_path=str(self.results_dir / "robustness_bonf.json"),
            correction_method="bonferroni"
        )
        
        for i, result_bh in enumerate(report['results']):
            result_bonf = report_bonf['results'][i]
            self.assertLessEqual(result_bh['corrected_p_value'], result_bonf['corrected_p_value'])

    def test_missing_input_file(self):
        """Test that appropriate error is raised for missing input file."""
        output_file = self.results_dir / "error_report.json"
        
        with self.assertRaises(FileNotFoundError):
            generate_robustness_report(
                bootstrap_results_path="nonexistent.csv",
                output_path=str(output_file)
            )

    def test_invalid_correction_method(self):
        """Test that appropriate error is raised for invalid correction method."""
        output_file = self.results_dir / "error_report.json"
        
        with self.assertRaises(ValueError):
            generate_robustness_report(
                bootstrap_results_path=str(self.mock_csv),
                output_path=str(output_file),
                correction_method="invalid_method"
            )

    def test_summary_statistics(self):
        """Test that summary statistics are correctly calculated."""
        output_file = self.results_dir / "summary_report.json"
        
        report = generate_robustness_report(
            bootstrap_results_path=str(self.mock_csv),
            output_path=str(output_file),
            correction_method="bonferroni"
        )
        
        # Check summary counts
        self.assertEqual(report['total_comparisons'], 2)
        # With p-values 0.001 and 0.04, Bonferroni corrected would be 0.002 and 0.08
        # Only one should be significant at 0.05 threshold
        self.assertEqual(report['significant_after_correction'], 1)

if __name__ == '__main__':
    unittest.main()