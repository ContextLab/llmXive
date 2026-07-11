"""
Unit tests for the statistics module.

These tests verify:
- Power analysis calculations
- Two-proportion z-test
- Fisher's Exact Test
- Test selection logic
- Contradiction rate verification
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import numpy as np

# Import the module under test
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from code.analysis.statistics import (
    power_analysis_two_proportions,
    two_proportion_z_test,
    fisher_exact_test,
    select_statistical_test,
    calculate_effect_size,
    verify_contradiction_rate,
    calculate_contradiction_rate,
    StudyInvalidError,
    ALPHA,
    POWER_TARGET,
    EFFECT_SIZE,
    CONTRADICTION_RATE_THRESHOLD
)


class TestPowerAnalysis(unittest.TestCase):
    """Tests for power analysis functions."""
    
    def test_power_analysis_default_parameters(self):
        """Test power analysis with default parameters."""
        result = power_analysis_two_proportions()
        
        self.assertIn('required_sample_size_per_group', result)
        self.assertIn('achieved_power', result)
        self.assertIn('power_achieved', result)
        self.assertGreater(result['required_sample_size_per_group'], 0)
        self.assertGreaterEqual(result['achieved_power'], POWER_TARGET - 0.01)
        
    def test_power_analysis_custom_effect_size(self):
        """Test power analysis with custom effect size."""
        result = power_analysis_two_proportions(effect_size=0.5)
        
        # Larger effect size should require smaller sample size
        self.assertLess(result['required_sample_size_per_group'], 
                       power_analysis_two_proportions(effect_size=0.2)['required_sample_size_per_group'])
        
    def test_power_analysis_low_power(self):
        """Test power analysis with low target power."""
        result = power_analysis_two_proportions(power_target=0.5)
        
        # Lower power target should require smaller sample size
        self.assertLess(result['required_sample_size_per_group'],
                       power_analysis_two_proportions(power_target=0.8)['required_sample_size_per_group'])


class TestTwoProportionZTest(unittest.TestCase):
    """Tests for two-proportion z-test."""
    
    def test_z_test_equal_proportions(self):
        """Test z-test with equal proportions."""
        z_stat, p_value = two_proportion_z_test(50, 100, 50, 100)
        
        self.assertAlmostEqual(z_stat, 0.0, places=5)
        self.assertAlmostEqual(p_value, 1.0, places=5)
        
    def test_z_test_different_proportions(self):
        """Test z-test with different proportions."""
        z_stat, p_value = two_proportion_z_test(70, 100, 50, 100)
        
        self.assertNotAlmostEqual(p_value, 1.0, places=2)
        self.assertGreater(z_stat, 0)
        
    def test_z_test_one_sided_larger(self):
        """Test z-test with one-sided alternative (larger)."""
        z_stat, p_value = two_proportion_z_test(70, 100, 50, 100, alternative="larger")
        
        # One-sided p-value should be half of two-sided for same direction
        z_stat_two, p_value_two = two_proportion_z_test(70, 100, 50, 100, alternative="two-sided")
        self.assertAlmostEqual(p_value, p_value_two / 2, places=5)
        
    def test_z_test_invalid_sample_size(self):
        """Test z-test with zero sample size."""
        with self.assertRaises(ValueError):
            two_proportion_z_test(50, 0, 50, 100)
            
    def test_z_test_zero_standard_error(self):
        """Test z-test with zero standard error."""
        # Both groups have 100% success rate
        z_stat, p_value = two_proportion_z_test(100, 100, 100, 100)
        
        self.assertEqual(z_stat, 0.0)
        self.assertEqual(p_value, 1.0)


class TestFisherExactTest(unittest.TestCase):
    """Tests for Fisher's Exact Test."""
    
    def test_fisher_test_equal_odds(self):
        """Test Fisher's test with equal odds."""
        odds_ratio, p_value = fisher_exact_test(50, 50, 50, 50)
        
        self.assertAlmostEqual(odds_ratio, 1.0, places=5)
        self.assertAlmostEqual(p_value, 1.0, places=5)
        
    def test_fisher_test_different_odds(self):
        """Test Fisher's test with different odds."""
        odds_ratio, p_value = fisher_exact_test(80, 20, 40, 60)
        
        self.assertGreater(odds_ratio, 1.0)
        self.assertLess(p_value, 0.05)
        
    def test_fisher_test_one_sided(self):
        """Test Fisher's test with one-sided alternative."""
        odds_ratio, p_value = fisher_exact_test(80, 20, 40, 60, alternative="greater")
        
        # One-sided p-value should be smaller
        _, p_value_two = fisher_exact_test(80, 20, 40, 60, alternative="two-sided")
        self.assertLess(p_value, p_value_two)
        
class TestTestSelection(unittest.TestCase):
    """Tests for statistical test selection logic."""
    
    def test_select_z_test_large_samples(self):
        """Test selection of z-test for large samples."""
        test_type = select_statistical_test(50, 100, 50, 100)
        
        self.assertEqual(test_type, "z-test")
        
    def test_select_fisher_small_samples(self):
        """Test selection of Fisher's test for small samples."""
        # Small cell counts should trigger Fisher's test
        test_type = select_statistical_test(2, 10, 2, 10)
        
        self.assertEqual(test_type, "fisher")
        
    def test_select_fisher_imbalanced_samples(self):
        """Test selection of Fisher's test for imbalanced samples."""
        # Very imbalanced samples with low success rates
        test_type = select_statistical_test(1, 20, 1, 20)
        
        self.assertEqual(test_type, "fisher")
        
class TestEffectSize(unittest.TestCase):
    """Tests for effect size calculations."""
    
    def test_cohens_h_equal_proportions(self):
        """Test Cohen's h with equal proportions."""
        effect_size = calculate_effect_size(0.5, 0.5)
        
        self.assertAlmostEqual(effect_size, 0.0, places=5)
        
    def test_cohens_h_different_proportions(self):
        """Test Cohen's h with different proportions."""
        effect_size = calculate_effect_size(0.7, 0.5)
        
        self.assertGreater(effect_size, 0.0)
        
    def test_cohens_h_symmetric(self):
        """Test that Cohen's h is symmetric."""
        effect_size1 = calculate_effect_size(0.7, 0.5)
        effect_size2 = calculate_effect_size(0.5, 0.7)
        
        self.assertAlmostEqual(effect_size1, effect_size2, places=5)
        
class TestContradictionRate(unittest.TestCase):
    """Tests for contradiction rate verification."""
    
    def test_verify_contradiction_rate_acceptable(self):
        """Test verification with acceptable contradiction rate."""
        result = verify_contradiction_rate(0.03)
        
        self.assertTrue(result)
        
    def test_verify_contradiction_rate_exceeds_threshold(self):
        """Test verification with rate exceeding threshold."""
        result = verify_contradiction_rate(0.06)
        
        self.assertFalse(result)
        
    def test_verify_contradiction_rate_exact_threshold(self):
        """Test verification with rate exactly at threshold."""
        result = verify_contradiction_rate(CONTRADICTION_RATE_THRESHOLD)
        
        self.assertTrue(result)
        
class TestCalculateContradictionRate(unittest.TestCase):
    """Tests for contradiction rate calculation from log file."""
    
    def test_calculate_rate_from_log(self):
        """Test calculation from existing log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["scene1", "scene2", "scene3"], f)
            log_path = f.name
            
        try:
            count, scenes = calculate_contradiction_rate(log_path)
            
            self.assertEqual(count, 3)
            self.assertEqual(len(scenes), 3)
            self.assertIn("scene1", scenes)
        finally:
            os.unlink(log_path)
            
    def test_calculate_rate_empty_log(self):
        """Test calculation from empty log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            log_path = f.name
            
        try:
            count, scenes = calculate_contradiction_rate(log_path)
            
            self.assertEqual(count, 0)
            self.assertEqual(len(scenes), 0)
        finally:
            os.unlink(log_path)
            
    def test_calculate_rate_nonexistent_file(self):
        """Test calculation from non-existent file."""
        count, scenes = calculate_contradiction_rate("/nonexistent/file.json")
        
        self.assertEqual(count, 0)
        self.assertEqual(len(scenes), 0)
        
    def test_calculate_rate_invalid_json(self):
        """Test calculation from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            log_path = f.name
            
        try:
            count, scenes = calculate_contradiction_rate(log_path)
            
            self.assertEqual(count, 0)
            self.assertEqual(len(scenes), 0)
        finally:
            os.unlink(log_path)
            
if __name__ == '__main__':
    unittest.main()