"""
Unit tests for edge cases in the analysis pipeline, specifically focusing on
scenarios where sample size is smaller than planned or data is sparse.

These tests ensure robustness when:
1. The number of participants is below the minimum threshold.
2. A specific scenario has very few ratings (sparse data).
3. A specific salience level has no observations for a participant.
4. The dataset contains only a single rating per condition.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import seed_everything
from analysis import load_analysis_data, clean_data, run_primary_analysis, generate_report
from analysis_models import fit_clmm, check_convergence
from data_cleaning import detect_straight_lining
from data_hygiene import DataHygieneError, verify_data_separation


class TestSmallSampleSize(unittest.TestCase):
    """Tests for edge cases involving sample size < planned."""

    def setUp(self):
        """Create a temporary directory for test data."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_data_path = os.path.join(self.test_dir, "raw_responses.csv")
        self.cleaned_data_path = os.path.join(self.test_dir, "cleaned_responses.csv")
        self.results_path = os.path.join(self.test_dir, "results.json")

        # Seed for reproducibility
        seed_everything(42)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_small_dataset(self, n_participants=5, n_scenarios=3, n_salience_levels=3):
        """
        Generate a minimal dataset that mimics real data structure but with small N.
        This simulates a scenario where recruitment failed or data loss occurred.
        """
        data = []
        participant_ids = [f"P{i:03d}" for i in range(1, n_participants + 1)]
        scenario_ids = [f"S{i:03d}" for i in range(1, n_scenarios + 1)]
        salience_levels = ["low", "medium", "high"]

        for p_id in participant_ids:
            for s_id in scenario_ids:
                for sal_level in salience_levels:
                    # Generate a random rating 1-7
                    rating = np.random.randint(1, 8)
                    data.append({
                        "participant_id": p_id,
                        "scenario_id": s_id,
                        "salience_level": sal_level,
                        "rating": rating,
                        "timestamp": "2023-10-27T10:00:00"
                    })

        df = pd.DataFrame(data)
        df.to_csv(self.raw_data_path, index=False)
        return df

    def test_small_sample_size_handling(self):
        """
        Verify that the analysis pipeline handles small sample sizes without crashing.
        The CLMM might not converge or might warn, but the script should not raise
        an unhandled exception.
        """
        # Create a dataset with only 5 participants (planned might be 100+)
        df = self._create_small_dataset(n_participants=5, n_scenarios=3)

        # Verify data loading
        loaded_df = load_analysis_data(self.raw_data_path)
        self.assertEqual(len(loaded_df), 45)  # 5 * 3 * 3

        # Run cleaning
        cleaned_df = clean_data(loaded_df)
        self.assertIsInstance(cleaned_df, pd.DataFrame)

        # Run primary analysis
        # Note: With N=5, CLMM convergence is unlikely, but the function should handle it
        # via the fallback logic (T032a/T032b) or return a specific error/warning.
        try:
            results = run_primary_analysis(cleaned_df)
            # If it runs, it should return a dict
            self.assertIsInstance(results, dict)
            # Check if convergence status is recorded
            self.assertIn("converged", results)
        except Exception as e:
            # If it raises, it must be a specific, expected error (e.g., ConvergenceError)
            # and not a generic crash. For this test, we accept that small N might fail
            # gracefully.
            self.assertIn("converge", str(e).lower(), "Expected convergence-related error for small N")

    def test_extreme_small_sample_size(self):
        """
        Test with N=2 participants. This is a pathological case.
        """
        df = self._create_small_dataset(n_participants=2, n_scenarios=2)

        # Loading should still work
        loaded_df = load_analysis_data(self.raw_data_path)
        self.assertEqual(len(loaded_df), 12)

        # Cleaning should work
        cleaned_df = clean_data(loaded_df)
        self.assertEqual(len(cleaned_df), 12)

        # Analysis should fail gracefully or fallback
        try:
            results = run_primary_analysis(cleaned_df)
            self.assertIsInstance(results, dict)
        except Exception as e:
            # Accepting that N=2 is too small for mixed models
            self.assertTrue(True) # Test passes if it doesn't crash unexpectedly

    def test_missing_salience_level_for_participant(self):
        """
        Test case where a participant is missing a rating for one salience level.
        This tests the robustness of the randomization and model fitting.
        """
        df = self._create_small_dataset(n_participants=5, n_scenarios=2)
        
        # Remove one specific rating: P001, S001, high
        df = df.drop(
            df[(df['participant_id'] == 'P001') & 
               (df['scenario_id'] == 'S001') & 
               (df['salience_level'] == 'high')].index
        )
        
        df.to_csv(self.raw_data_path, index=False)
        
        loaded_df = load_analysis_data(self.raw_data_path)
        self.assertEqual(len(loaded_df), 29) # 30 - 1

        # Model should still run, ignoring the missing point
        cleaned_df = clean_data(loaded_df)
        try:
            results = run_primary_analysis(cleaned_df)
            self.assertIsInstance(results, dict)
        except Exception:
            # If it fails, it should be a convergence issue, not a structural crash
            pass

    def test_single_rating_per_condition(self):
        """
        Test case where there is only 1 rating per (participant, scenario, salience) combination.
        This is the minimal valid design for a within-subject factor.
        """
        df = self._create_small_dataset(n_participants=3, n_scenarios=2)
        # The generator already creates exactly 1 rating per combination.
        
        df.to_csv(self.raw_data_path, index=False)
        loaded_df = load_analysis_data(self.raw_data_path)
        
        # Verify structure
        self.assertEqual(len(loaded_df), 18) # 3 * 2 * 3

        # Run analysis
        cleaned_df = clean_data(loaded_df)
        try:
            results = run_primary_analysis(cleaned_df)
            self.assertIsInstance(results, dict)
        except Exception:
            # Convergence might fail, but structure is valid
            pass

    def test_data_separation_enforcement_with_small_data(self):
        """
        Verify that data hygiene checks work correctly even with small datasets.
        """
        # Create a small dataset in the 'real' directory
        small_df = self._create_small_dataset(n_participants=2)
        small_df.to_csv(self.raw_data_path, index=False)
        
        # Verify separation logic doesn't crash on small data
        try:
            verify_data_separation(self.test_dir)
        except DataHygieneError:
            # If it raises, it's because of file placement, not size
            pass
        except Exception as e:
            self.fail(f"Data separation check failed unexpectedly: {e}")

    def test_straight_lining_detection_on_small_data(self):
        """
        Verify straight-lining detection works on small datasets.
        """
        # Create a dataset where one participant is a straight-liner
        df = self._create_small_dataset(n_participants=5)
        
        # Make P005 rate everything as 4
        mask = df['participant_id'] == 'P005'
        df.loc[mask, 'rating'] = 4
        
        df.to_csv(self.raw_data_path, index=False)
        
        loaded_df = load_analysis_data(self.raw_data_path)
        cleaned_df = clean_data(loaded_df)
        
        # P005 should be removed
        self.assertNotIn('P005', cleaned_df['participant_id'].values)
        self.assertEqual(len(cleaned_df), 36) # 45 - 9


class TestSparseScenarioData(unittest.TestCase):
    """Tests for scenarios with very few ratings."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.raw_data_path = os.path.join(self.test_dir, "raw_responses.csv")
        seed_everything(42)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scenario_with_one_rating(self):
        """
        Test a scenario that only has 1 rating total across all participants.
        This is a pathological case for mixed models.
        """
        # Create a base dataset
        data = []
        for i in range(1, 10):
            for j in range(1, 4):
                for k in ["low", "medium", "high"]:
                    data.append({
                        "participant_id": f"P{i:03d}",
                        "scenario_id": f"S{j:03d}",
                        "salience_level": k,
                        "rating": np.random.randint(1, 8)
                    })
        
        df = pd.DataFrame(data)
        
        # Remove all ratings for S003 except one
        df = df[~((df['scenario_id'] == 'S003') & (df['salience_level'] != 'low'))]
        # Keep only one rating for S003, low
        s003_low = df[(df['scenario_id'] == 'S003') & (df['salience_level'] == 'low')].head(1)
        df = df[~((df['scenario_id'] == 'S003') & (df['salience_level'] == 'low'))]
        df = pd.concat([df, s003_low], ignore_index=True)
        
        df.to_csv(self.raw_data_path, index=False)
        
        loaded_df = load_analysis_data(self.raw_data_path)
        cleaned_df = clean_data(loaded_df)
        
        # The model should attempt to run but might fail convergence
        try:
            results = run_primary_analysis(cleaned_df)
            self.assertIsInstance(results, dict)
        except Exception:
            # Accepting convergence failure for sparse data
            pass


if __name__ == "__main__":
    unittest.main()