"""
Unit tests for entanglement_scores.py
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import entropy, skew, kurtosis

# Import the module functions
import sys
sys.path.insert(0, 'code')
from entanglement_scores import (
    extract_teacher_scores_matrix,
    compute_per_sample_stats,
    compute_mahalanobis_distance,
    integrate_features,
    save_features
)

class TestEntanglementScores(unittest.TestCase):

    def setUp(self):
        # Create a mock dataframe with teacher scores
        self.df = pd.DataFrame({
            'sample_id': [1, 2, 3],
            'teacher_dim_0': [1.0, 2.0, 3.0],
            'teacher_dim_1': [4.0, 5.0, 6.0],
            'teacher_dim_2': [7.0, 8.0, 9.0],
            'teacher_dim_3': [10.0, 11.0, 12.0],
            'fidelity_loss': [0.1, 0.2, 0.3]
        })

    def test_extract_teacher_scores_matrix(self):
        matrix = extract_teacher_scores_matrix(self.df)
        expected_shape = (3, 4)
        self.assertEqual(matrix.shape, expected_shape)
        self.assertTrue(np.allclose(matrix[0], [1.0, 4.0, 7.0, 10.0]))

    def test_compute_per_sample_stats(self):
        matrix = extract_teacher_scores_matrix(self.df)
        stats = compute_per_sample_stats(matrix)
        
        self.assertIn('variance', stats)
        self.assertIn('entropy', stats)
        self.assertIn('skewness', stats)
        self.assertIn('kurtosis', stats)
        
        self.assertEqual(len(stats['variance']), 3)
        self.assertEqual(len(stats['entropy']), 3)
        self.assertEqual(len(stats['skewness']), 3)
        self.assertEqual(len(stats['kurtosis']), 3)

    def test_compute_mahalanobis_distance(self):
        matrix = extract_teacher_scores_matrix(self.df)
        cov_matrix = np.eye(4) # Identity matrix for simplicity
        mean_vec = np.mean(matrix, axis=0)
        
        distances = compute_mahalanobis_distance(matrix, cov_matrix, mean_vec)
        self.assertEqual(len(distances), 3)
        self.assertTrue(all(d >= 0 for d in distances))

    def test_integrate_features(self):
        matrix = extract_teacher_scores_matrix(self.df)
        stats = compute_per_sample_stats(matrix)
        cov_matrix = np.eye(4)
        mean_vec = np.mean(matrix, axis=0)
        mahalanobis = compute_mahalanobis_distance(matrix, cov_matrix, mean_vec)
        eigenvalue = 1.5

        df_enriched = integrate_features(self.df, stats, mahalanobis, eigenvalue)

        self.assertIn('variance', df_enriched.columns)
        self.assertIn('entropy', df_enriched.columns)
        self.assertIn('skewness', df_enriched.columns)
        self.assertIn('kurtosis', df_enriched.columns)
        self.assertIn('mahalanobis_distance', df_enriched.columns)
        self.assertIn('global_eigenvalue', df_enriched.columns)

    def test_save_features(self):
        matrix = extract_teacher_scores_matrix(self.df)
        stats = compute_per_sample_stats(matrix)
        cov_matrix = np.eye(4)
        mean_vec = np.mean(matrix, axis=0)
        mahalanobis = compute_mahalanobis_distance(matrix, cov_matrix, mean_vec)
        eigenvalue = 1.5

        df_enriched = integrate_features(self.df, stats, mahalanobis, eigenvalue)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            save_features(df_enriched, temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 3)
            self.assertIn('variance', data[0])
            self.assertIn('entropy', data[0])
            self.assertIn('skewness', data[0])
            self.assertIn('kurtosis', data[0])
            self.assertIn('mahalanobis_distance', data[0])
            self.assertIn('global_eigenvalue', data[0])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()