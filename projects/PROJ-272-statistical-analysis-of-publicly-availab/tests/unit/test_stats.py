"""
Unit tests for the statistical testing module (stats.py).
Tests Mann-Whitney U calculation and Bonferroni correction logic.
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import tempfile
import os
import warnings

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import (
    load_feature_matrix,
    prepare_group_data,
    run_mann_whitney_u,
    run_group_comparisons,
    apply_bonferroni_correction,
    save_results
)

class TestPrepareGroupData(unittest.TestCase):
    
    def setUp(self):
        self.data = pd.DataFrame({
            'participant_id': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
            'label': ['Control', 'AD', 'Control', 'MCI', 'AD', 'Control'],
            'feature_x': [1.0, 2.0, 1.5, 3.0, 2.5, 1.2],
            'feature_y': [10.0, 20.0, 15.0, 30.0, 25.0, 12.0]
        })

    def test_extract_correct_groups(self):
        g1, g2 = prepare_group_data(self.data, 'feature_x', 'Control', 'AD')
        self.assertEqual(len(g1), 3)  # 3 Controls
        self.assertEqual(len(g2), 2)  # 2 ADs
        self.assertAlmostEqual(g1.mean(), (1.0 + 1.5 + 1.2) / 3)
        self.assertAlmostEqual(g2.mean(), (2.0 + 2.5) / 2)

    def test_missing_feature_column(self):
        with self.assertRaises(ValueError):
            prepare_group_data(self.data, 'non_existent_feature', 'Control', 'AD')

    def test_missing_group(self):
        df_no_mci = self.data[self.data['label'] != 'MCI']
        with self.assertRaises(ValueError):
            prepare_group_data(df_no_mci, 'feature_x', 'Control', 'MCI')

class TestRunMannWhitneyU(unittest.TestCase):
    
    def test_basic_test(self):
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([10, 11, 12, 13, 14])
        result = run_mann_whitney_u(group1, group2)
        
        self.assertIn('statistic', result)
        self.assertIn('pvalue', result)
        self.assertIsInstance(result['statistic'], float)
        self.assertIsInstance(result['pvalue'], float)
        # With completely separated groups, p-value should be very small
        self.assertLess(result['pvalue'], 0.01)

    def test_identical_groups(self):
        group1 = np.array([1, 1, 1])
        group2 = np.array([1, 1, 1])
        # Should not raise, but might warn
        result = run_mann_whitney_u(group1, group2)
        self.assertIn('pvalue', result)
        # P-value should be 1.0 for identical distributions
        self.assertEqual(result['pvalue'], 1.0)

    def test_insufficient_samples(self):
        group1 = np.array([1])
        group2 = np.array([2, 3])
        with self.assertRaises(ValueError):
            run_mann_whitney_u(group1, group2)

class TestBonferroniCorrection(unittest.TestCase):
    
    def test_simple_correction(self):
        raw_pvalues = [0.01, 0.04, 0.05, 0.001]
        n_tests = len(raw_pvalues)
        corrected = apply_bonferroni_correction(raw_pvalues, n_tests)
        
        self.assertEqual(len(corrected), n_tests)
        # Check that corrected values are raw * n_tests, capped at 1.0
        for i, p in enumerate(corrected):
            expected = min(raw_pvalues[i] * n_tests, 1.0)
            self.assertAlmostEqual(p, expected)

    def test_single_test(self):
        raw_pvalues = [0.05]
        corrected = apply_bonferroni_correction(raw_pvalues, 1)
        self.assertAlmostEqual(corrected[0], 0.05)

    def test_large_pvalue_capping(self):
        raw_pvalues = [0.9, 0.95]
        corrected = apply_bonferroni_correction(raw_pvalues, 2)
        # 0.9 * 2 = 1.8 -> capped at 1.0
        self.assertEqual(corrected[0], 1.0)
        self.assertEqual(corrected[1], 1.0)

class TestRunGroupComparisons(unittest.TestCase):
    
    def setUp(self):
        self.data = pd.DataFrame({
            'participant_id': [f'p{i}' for i in range(10)],
            'label': ['Control'] * 4 + ['AD'] * 3 + ['MCI'] * 3,
            'feat1': np.random.rand(10),
            'feat2': np.random.rand(10) * 10
        })

    def test_multiple_features(self):
        features = ['feat1', 'feat2']
        comparisons = [('Control', 'AD')]
        results = run_group_comparisons(self.data, features, comparisons)
        
        self.assertIn('feat1', results)
        self.assertIn('feat2', results)
        self.assertIn('Control_vs_AD', results['feat1'])
        self.assertIn('statistic', results['feat1']['Control_vs_AD'])

    def test_multiple_comparisons(self):
        features = ['feat1']
        comparisons = [('Control', 'AD'), ('Control', 'MCI')]
        results = run_group_comparisons(self.data, features, comparisons)
        
        self.assertIn('Control_vs_AD', results['feat1'])
        self.assertIn('Control_vs_MCI', results['feat1'])

class TestSaveResults(unittest.TestCase):
    
    def test_save_and_load(self):
        test_results = {
            'metadata': {'test': 'value'},
            'results': {'feat1': {'Control_vs_AD': {'statistic': 1.0, 'pvalue': 0.5}}}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_results.json')
            save_results(test_results, output_path)
            
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['metadata']['test'], 'value')
            self.assertAlmostEqual(loaded['results']['feat1']['Control_vs_AD']['statistic'], 1.0)

if __name__ == '__main__':
    unittest.main()