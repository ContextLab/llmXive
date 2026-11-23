"""
Unit tests for model training logic in code/models/training.py.
Verifies CV switch (5-fold vs LOOCV) and covariate logic (source_study exclusion).
"""
import os
import sys
import tempfile
import shutil
import unittest
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent to path to allow imports if run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.training import (
    determine_cv_strategy,
    check_study_covariate_condition,
    save_cv_strategy,
    load_processed_data
)


class TestModelsT027(unittest.TestCase):
    """Tests for User Story 2 Model Training Logic (T027)."""

    def setUp(self):
        """Set up temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.test_dir, "test_data.csv")
        self.strategy_path = os.path.join(self.test_dir, "cv_strategy.json")
        self.covariate_path = os.path.join(self.test_dir, "covariate_config.json")

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_df(self, n_rows, include_study=False):
        """Helper to create a deterministic DataFrame."""
        np.random.seed(42)
        data = {
            'population_id': [f'POP_{i:03d}' for i in range(n_rows)],
            'diversity_metric': np.random.rand(n_rows),
            'env_temp': np.random.rand(n_rows) * 10,
            'compound_conc': np.random.rand(n_rows) * 100
        }
        if include_study:
            # Create a scenario where unique_studies == n_rows (every row is a unique study)
            # This triggers the condition unique_studies >= N-1
            data['source_study'] = [f'STUDY_{i:03d}' for i in range(n_rows)]
        return pd.DataFrame(data)

    # --- T021: CV Strategy Logic ---

    def test_cv_strategy_large_n_uses_5_fold(self):
        """Verify 5-fold CV is selected when N >= 30."""
        df = self._create_test_df(n_rows=50)
        strategy = determine_cv_strategy(df)

        self.assertEqual(strategy['cv_type'], 'k_fold')
        self.assertEqual(strategy['n'], 50)
        self.assertTrue(strategy['k'] == 5)

    def test_cv_strategy_small_n_uses_loocv(self):
        """Verify LOOCV is selected when N < 30."""
        df = self._create_test_df(n_rows=10)
        strategy = determine_cv_strategy(df)

        self.assertEqual(strategy['cv_type'], 'leave_one_out')
        self.assertEqual(strategy['n'], 10)

    def test_cv_strategy_boundary_n_30(self):
        """Verify 5-fold is selected exactly at N=30."""
        df = self._create_test_df(n_rows=30)
        strategy = determine_cv_strategy(df)

        self.assertEqual(strategy['cv_type'], 'k_fold')
        self.assertEqual(strategy['k'], 5)

    def test_save_cv_strategy_writes_json(self):
        """Verify save_cv_strategy writes a valid JSON file."""
        df = self._create_test_df(n_rows=40)
        strategy = determine_cv_strategy(df)
        save_cv_strategy(strategy, self.strategy_path)

        self.assertTrue(os.path.exists(self.strategy_path))
        with open(self.strategy_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['cv_type'], 'k_fold')
        self.assertEqual(loaded['n'], 40)

    # --- T022: Covariate Logic ---

    def test_covariate_logic_unique_studies_less_than_n_minus_1(self):
        """
        Verify use_source_study=True when unique_studies < N-1.
        Scenario: 50 rows, but only 5 unique studies.
        """
        df = self._create_test_df(n_rows=50, include_study=True)
        # Manually override to have fewer unique studies
        df['source_study'] = [f'STUDY_{i % 5:03d}' for i in range(50)]

        config = check_study_covariate_condition(df)

        self.assertEqual(config['use_source_study'], True)
        self.assertEqual(config['normalization_type'], 'study_specific')

    def test_covariate_logic_unique_studies_greater_equal_n_minus_1(self):
        """
        Verify use_source_study=False when unique_studies >= N-1.
        Scenario: 50 rows, 50 unique studies.
        """
        df = self._create_test_df(n_rows=50, include_study=True)
        # Already set to unique studies per row in helper

        config = check_study_covariate_condition(df)

        self.assertEqual(config['use_source_study'], False)
        self.assertEqual(config['normalization_type'], 'global')

    def test_covariate_logic_missing_source_study_column(self):
        """
        Verify use_source_study=False when column is missing (treat as global).
        """
        df = self._create_test_df(n_rows=50, include_study=False)

        config = check_study_covariate_condition(df)

        self.assertEqual(config['use_source_study'], False)
        self.assertEqual(config['normalization_type'], 'global')

    def test_covariate_config_writes_json(self):
        """Verify check_study_covariate_condition output can be saved to JSON."""
        df = self._create_test_df(n_rows=50, include_study=True)
        config = check_study_covariate_condition(df)
        
        # Save manually to verify serializability
        with open(self.covariate_path, 'w') as f:
            json.dump(config, f)

        self.assertTrue(os.path.exists(self.covariate_path))
        with open(self.covariate_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertFalse(loaded['use_source_study'])


if __name__ == '__main__':
    unittest.main()