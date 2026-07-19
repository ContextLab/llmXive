"""
Unit tests for stratified_analysis.py (T029)
"""

import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'code')))

from models.stratified_analysis import (
    load_processed_data,
    calculate_group_stats,
    assess_variance_heterogeneity,
    run_stratified_analysis
)

class TestLoadProcessedData(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "processed_data.csv")
        
        # Create a valid test CSV
        data = {
            'alloy_type': ['Al-6061', 'Al-6061', 'Ti-64', 'Ti-64'],
            'yield_strength': [250.0, 260.0, 800.0, 820.0],
            'ductility': [15.0, 14.0, 10.0, 11.0]
        }
        pd.DataFrame(data).to_csv(self.test_file, index=False)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_load_valid_data(self):
        df, targets = load_processed_data(self.test_file)
        self.assertEqual(len(df), 4)
        self.assertIn('yield_strength', targets)
        self.assertIn('ductility', targets)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_processed_data("non_existent.csv")

    def test_missing_alloy_type(self):
        # Create CSV without alloy_type
        bad_data = {'yield_strength': [250.0], 'ductility': [15.0]}
        bad_file = os.path.join(self.temp_dir, "bad.csv")
        pd.DataFrame(bad_data).to_csv(bad_file, index=False)
        
        with self.assertRaises(ValueError):
            load_processed_data(bad_file)

class TestCalculateGroupStats(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'alloy_type': ['A', 'A', 'B', 'B'],
            'yield_strength': [100.0, 110.0, 200.0, 210.0],
            'ductility': [10.0, 12.0, 5.0, 6.0]
        })
        self.target_cols = ['yield_strength', 'ductility']

    def test_stats_calculation(self):
        stats = calculate_group_stats(self.df, 'alloy_type', self.target_cols)
        
        # Check Group A
        self.assertIn('A', stats)
        self.assertEqual(stats['A']['count'], 2)
        self.assertAlmostEqual(stats['A']['properties']['yield_strength']['mean'], 105.0)
        self.assertAlmostEqual(stats['A']['properties']['yield_strength']['std'], 5.0)

        # Check Group B
        self.assertIn('B', stats)
        self.assertAlmostEqual(stats['B']['properties']['yield_strength']['mean'], 205.0)

    def test_missing_values_handling(self):
        df_with_nan = self.df.copy()
        df_with_nan.loc[0, 'yield_strength'] = np.nan
        stats = calculate_group_stats(df_with_nan, 'alloy_type', self.target_cols)
        
        # Mean should be calculated only on non-NaN values
        self.assertAlmostEqual(stats['A']['properties']['yield_strength']['mean'], 110.0)

class TestAssessVarianceHeterogeneity(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'alloy_type': ['A', 'A', 'A', 'B', 'B', 'B'],
            'yield_strength': [100.0, 105.0, 110.0, 200.0, 205.0, 210.0]
        })
        self.target_cols = ['yield_strength']

    @patch('models.stratified_analysis.scipy_stats')
    def test_levene_test_called(self, mock_scipy):
        mock_scipy.levene.return_value = (1.5, 0.25)
        
        result = assess_variance_heterogeneity(self.df, 'alloy_type', self.target_cols)
        
        self.assertIn('yield_strength', result)
        self.assertFalse(result['yield_strength']['significant'])
        self.assertEqual(result['yield_strength']['p_value'], 0.25)
        mock_scipy.levene.assert_called_once()

    def test_insufficient_groups(self):
        df_single = pd.DataFrame({
            'alloy_type': ['A', 'A'],
            'yield_strength': [100.0, 110.0]
        })
        result = assess_variance_heterogeneity(df_single, 'alloy_type', self.target_cols)
        self.assertEqual(result['status'], 'insufficient_groups')

class TestRunStratifiedAnalysisIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        # Create temp directories
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_dir = os.path.join(temp_dir, "processed")
            results_dir = os.path.join(temp_dir, "results")
            os.makedirs(processed_dir)
            os.makedirs(results_dir)
            
            # Create input file
            data = {
                'alloy_type': ['Al', 'Al', 'Ti', 'Ti', 'Steel', 'Steel'],
                'yield_strength': [250.0, 260.0, 800.0, 820.0, 500.0, 510.0],
                'ductility': [15.0, 14.0, 10.0, 11.0, 20.0, 19.0]
            }
            input_file = os.path.join(processed_dir, "processed_data.csv")
            pd.DataFrame(data).to_csv(input_file, index=False)
            
            # Mock config to use our temp dirs
            with patch('models.stratified_analysis.get_processed_data_dir', return_value=processed_dir), \
                 patch('models.stratified_analysis.get_results_dir', return_value=results_dir), \
                 patch('models.stratified_analysis.get_logs_dir', return_value=results_dir):
                
                    results = run_stratified_analysis(output_dir=results_dir)
                    
                    # Verify output file exists
                    output_file = os.path.join(results_dir, "stratified_analysis.json")
                    self.assertTrue(os.path.exists(output_file))
                    
                    # Verify content
                    self.assertEqual(results['total_samples'], 6)
                    self.assertIn('Al', results['groups_analyzed'])
                    self.assertIn('conclusion', results)