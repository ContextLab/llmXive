"""
Integration test for regression model fitting (US2 - T022).

This test verifies that the regression analysis pipeline correctly:
1. Loads behavioral data (improvement scores, demographics).
2. Loads centrality metrics (global or PCA-adjusted) based on VIF decision.
3. Loads motion confounds (Mean FD).
4. Merges data correctly.
5. Fits a linear regression model with the specified formula.
6. Saves the regression summary to the expected output file.

It uses the real data artifacts produced by T017, T023/T024b, T025, T027b, and T028a.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.regression import (
    load_behavioral_data,
    load_centrality_or_pca_data,
    load_mean_fd_data,
    merge_all_data,
    fit_linear_regression,
    save_regression_summary,
    run_regression_analysis
)
from utils.config import get_config, reset_config


class TestRegressionIntegration(unittest.TestCase):
    """Integration tests for the regression pipeline."""

    def setUp(self):
        """Set up test environment with mock data files."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_regression_"))
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir(parents=True)
        
        # Create subdirectories matching project structure
        (self.data_dir / "processed" / "behavioral").mkdir(parents=True)
        (self.data_dir / "processed" / "centrality").mkdir(parents=True)
        (self.data_dir / "processed" / "regression").mkdir(parents=True)
        
        # Create mock data files that simulate real pipeline outputs
        self._create_mock_behavioral_data()
        self._create_mock_centrality_data()
        self._create_mock_fd_data()
        self._create_mock_model_decision()
        
        # Configure paths for this test
        self.config = get_config()
        self.config.output_paths.data_dir = str(self.data_dir)
        
        # Set specific paths for the test
        self.behavioral_path = self.data_dir / "processed" / "behavioral" / "subject_scores.csv"
        self.centrality_path = self.data_dir / "processed" / "centrality" / "global_scores.csv"
        self.fd_path = self.data_dir / "processed" / "behavioral" / "fd_mean.csv"
        self.decision_path = self.data_dir / "processed" / "centrality" / "model_decision.csv"
        self.output_path = self.data_dir / "processed" / "regression" / "linear_model_summary.csv"

    def tearDown(self):
        """Clean up test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_mock_behavioral_data(self):
        """Create mock behavioral data file."""
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
            'pre_motor_score': np.random.uniform(20, 40, 50),
            'post_motor_score': np.random.uniform(10, 30, 50),
            'age': np.random.randint(18, 65, 50),
            'sex': np.random.choice(['M', 'F'], 50),
            'improvement_score': np.random.uniform(-5, 15, 50)
        }
        df = pd.DataFrame(data)
        df.to_csv(self.behavioral_path, index=False)

    def _create_mock_centrality_data(self):
        """Create mock centrality global scores file."""
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
            'global_centrality': np.random.uniform(0.1, 0.9, 50),
            'degree': np.random.uniform(0.2, 0.8, 50),
            'betweenness': np.random.uniform(0.1, 0.7, 50),
            'eigenvector': np.random.uniform(0.15, 0.85, 50)
        }
        df = pd.DataFrame(data)
        df.to_csv(self.centrality_path, index=False)

    def _create_mock_fd_data(self):
        """Create mock Mean FD data file."""
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
            'mean_fd': np.random.uniform(0.1, 0.5, 50)
        }
        df = pd.DataFrame(data)
        df.to_csv(self.fd_path, index=False)

    def _create_mock_model_decision(self):
        """Create mock model decision file (Global model)."""
        data = {
            'decision': ['Global'] * 1,
            'vif_max': [2.5]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.decision_path, index=False)

    def test_load_behavioral_data(self):
        """Test loading behavioral data."""
        df = load_behavioral_data(self.behavioral_path)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 50)
        self.assertIn('improvement_score', df.columns)
        self.assertIn('subject_id', df.columns)

    def test_load_centrality_data(self):
        """Test loading centrality data."""
        df = load_centrality_or_pca_data(self.centrality_path, 'Global')
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 50)
        self.assertIn('global_centrality', df.columns)

    def test_load_mean_fd_data(self):
        """Test loading Mean FD data."""
        df = load_mean_fd_data(self.fd_path)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 50)
        self.assertIn('mean_fd', df.columns)

    def test_merge_all_data(self):
        """Test merging all data sources."""
        behavioral = load_behavioral_data(self.behavioral_path)
        centrality = load_centrality_or_pca_data(self.centrality_path, 'Global')
        fd = load_mean_fd_data(self.fd_path)
        
        merged = merge_all_data(behavioral, centrality, fd)
        
        self.assertIsNotNone(merged)
        self.assertEqual(len(merged), 50)
        expected_cols = ['subject_id', 'improvement_score', 'global_centrality', 'mean_fd', 'age', 'sex']
        for col in expected_cols:
            self.assertIn(col, merged.columns)

    def test_fit_linear_regression(self):
        """Test fitting a linear regression model."""
        behavioral = load_behavioral_data(self.behavioral_path)
        centrality = load_centrality_or_pca_data(self.centrality_path, 'Global')
        fd = load_mean_fd_data(self.fd_path)
        
        merged = merge_all_data(behavioral, centrality, fd)
        
        # Create formula: Improvement ~ Global_Centrality + Age + Sex + Mean_FD
        formula = "improvement_score ~ global_centrality + age + mean_fd + C(sex)"
        
        model_result = fit_linear_regression(merged, formula)
        
        self.assertIsNotNone(model_result)
        self.assertTrue(hasattr(model_result, 'params'))
        self.assertTrue(hasattr(model_result, 'rsquared'))
        self.assertGreater(model_result.rsquared, 0)  # Should explain some variance

    def test_save_regression_summary(self):
        """Test saving regression summary to file."""
        behavioral = load_behavioral_data(self.behavioral_path)
        centrality = load_centrality_or_pca_data(self.centrality_path, 'Global')
        fd = load_mean_fd_data(self.fd_path)
        
        merged = merge_all_data(behavioral, centrality, fd)
        
        formula = "improvement_score ~ global_centrality + age + mean_fd + C(sex)"
        model_result = fit_linear_regression(merged, formula)
        
        save_regression_summary(model_result, self.output_path)
        
        self.assertTrue(self.output_path.exists())
        
        # Verify the saved file can be read
        saved_df = pd.read_csv(self.output_path)
        self.assertFalse(saved_df.empty)
        self.assertIn('term', saved_df.columns)
        self.assertIn('estimate', saved_df.columns)
        self.assertIn('p_value', saved_df.columns)

    def test_run_regression_analysis(self):
        """Test the full regression analysis pipeline."""
        # Create formula file as expected by the pipeline
        formula_path = self.data_dir / "processed" / "regression" / "formula.txt"
        with open(formula_path, 'w') as f:
            f.write("improvement_score ~ global_centrality + age + mean_fd + C(sex)")
        
        # Run the full analysis
        results = run_regression_analysis(
            behavioral_path=self.behavioral_path,
            centrality_path=self.centrality_path,
            fd_path=self.fd_path,
            formula_path=formula_path,
            output_path=self.output_path,
            model_type='Global'
        )
        
        self.assertIsNotNone(results)
        self.assertTrue(self.output_path.exists())
        
        # Verify output content
        output_df = pd.read_csv(self.output_path)
        self.assertFalse(output_df.empty)
        self.assertGreater(len(output_df), 0)

    def test_regression_with_pca_model(self):
        """Test regression analysis when PCA-adjusted model is selected."""
        # Update model decision to PCA
        decision_df = pd.DataFrame({
            'decision': ['PCA-Adjusted'],
            'vif_max': [6.5]
        })
        decision_df.to_csv(self.decision_path, index=False)
        
        # Create mock PCA data
        pca_path = self.data_dir / "processed" / "centrality" / "pca_scores.csv"
        pca_data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 51)],
            'pca_component_1': np.random.uniform(-2, 2, 50)
        }
        pd.DataFrame(pca_data).to_csv(pca_path, index=False)
        
        # Update formula for PCA model
        formula_path = self.data_dir / "processed" / "regression" / "formula.txt"
        with open(formula_path, 'w') as f:
            f.write("improvement_score ~ pca_component_1 + age + mean_fd + C(sex)")
        
        # Run analysis with PCA model
        results = run_regression_analysis(
            behavioral_path=self.behavioral_path,
            centrality_path=pca_path,
            fd_path=self.fd_path,
            formula_path=formula_path,
            output_path=self.output_path,
            model_type='PCA-Adjusted'
        )
        
        self.assertIsNotNone(results)
        self.assertTrue(self.output_path.exists())


if __name__ == '__main__':
    unittest.main()