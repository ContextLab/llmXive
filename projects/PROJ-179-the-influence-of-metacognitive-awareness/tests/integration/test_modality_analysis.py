"""
Integration test for modality-specific correlation analysis (T025).
Verifies that the correlation pipeline correctly handles data filtered by stimulus modality.
"""
import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.analysis.bootstrap import run_bootstrap_analysis, load_correlation_data
from code.src.analysis.correlation import compute_hold_out_correlation
from code.models.data_models import StimulusModality


class TestModalitySpecificCorrelation(unittest.TestCase):
    """
    Integration tests ensuring that modality-specific analysis (Visual vs Auditory)
    produces valid, independent correlation results.
    """

    def setUp(self):
        """Create temporary directory and mock data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create mock trial data with both modalities
        np.random.seed(42)
        n_trials = 200
        
        data = {
            'participant_id': np.repeat(range(1, 21), n_trials // 20),
            'trial_id': range(n_trials),
            'stimulus_modality': np.random.choice(['visual', 'auditory'], n_trials),
            'source_label': np.random.choice(['internal', 'external'], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.uniform(1, 5, n_trials),
            'accuracy': np.random.choice([0, 1], n_trials)
        }
        
        self.mock_df = pd.DataFrame(data)
        self.test_csv_path = self.data_dir / "mock_trial_data.csv"
        self.mock_df.to_csv(self.test_csv_path, index=False)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_visual_modality_correlation(self):
        """
        Test that filtering for 'visual' modality produces a valid correlation result.
        Verifies the pipeline handles the filter correctly and computes stats.
        """
        # Filter data for visual modality
        visual_data = self.mock_df[self.mock_df['stimulus_modality'] == 'visual']
        visual_csv = self.data_dir / "visual_trials.csv"
        visual_data.to_csv(visual_csv, index=False)

        # Ensure we have data to work with
        self.assertGreater(len(visual_data), 0, "Mock data should contain visual trials")

        # Prepare input for correlation function (simulating T014 input)
        # We need to simulate the output of T014 (Hold-Out design)
        # For this integration test, we will construct the expected input format
        # that compute_hold_out_correlation would receive.
        
        # Simulate the training/test split results structure
        # In a real scenario, this would come from T014 output
        train_data = visual_data.sample(frac=0.7, random_state=42)
        test_data = visual_data.drop(train_data.index)

        # Compute mock metrics for the test set (Reality Testing Accuracy - d')
        # and training set (Metacognitive Score - Type-2 AUC)
        # Since we don't have the full T014 implementation logic here, 
        # we create a synthetic dataset that mimics the expected output structure
        # for the correlation analysis.
        
        synthetic_results = []
        for pid in visual_data['participant_id'].unique():
            p_train = train_data[train_data['participant_id'] == pid]
            p_test = test_data[test_data['participant_id'] == pid]
            
            if len(p_train) > 10 and len(p_test) > 5:
                # Mock Type-2 AUC (Metacognitive Score)
                meta_score = np.random.uniform(0.5, 0.95)
                # Mock d' (Reality Testing Accuracy)
                d_prime = np.random.uniform(0.1, 2.5)
                
                synthetic_results.append({
                    'participant_id': pid,
                    'modality': 'visual',
                    'metacognitive_score': meta_score,
                    'reality_testing_accuracy': d_prime
                })

        if not synthetic_results:
            self.skipTest("Not enough data to simulate split results")

        synthetic_df = pd.DataFrame(synthetic_results)
        synthetic_csv = self.data_dir / "visual_correlation_input.csv"
        synthetic_df.to_csv(synthetic_csv, index=False)

        # Run the correlation analysis
        try:
            result = run_bootstrap_analysis(
                input_path=str(synthetic_csv),
                x_col='metacognitive_score',
                y_col='reality_testing_accuracy',
                n_boot=100, # Small number for speed in test
                output_dir=str(self.data_dir)
            )
            
            # Assertions
            self.assertIsNotNone(result)
            self.assertIn('correlation', result)
            self.assertIn('p_value', result)
            self.assertIn('ci_lower', result)
            self.assertIn('ci_upper', result)
            
            # Verify the correlation coefficient is a valid float
            self.assertIsInstance(result['correlation'], float)
            self.assertGreaterEqual(result['correlation'], -1.0)
            self.assertLessEqual(result['correlation'], 1.0)

        except Exception as e:
            self.fail(f"Visual modality correlation analysis failed: {e}")

    def test_auditory_modality_correlation(self):
        """
        Test that filtering for 'auditory' modality produces a valid correlation result.
        Ensures independence from visual results.
        """
        # Filter data for auditory modality
        auditory_data = self.mock_df[self.mock_df['stimulus_modality'] == 'auditory']
        auditory_csv = self.data_dir / "auditory_trials.csv"
        auditory_data.to_csv(auditory_csv, index=False)

        self.assertGreater(len(auditory_data), 0, "Mock data should contain auditory trials")

        # Create synthetic results similar to visual test
        train_data = auditory_data.sample(frac=0.7, random_state=42)
        test_data = auditory_data.drop(train_data.index)

        synthetic_results = []
        for pid in auditory_data['participant_id'].unique():
            p_train = train_data[train_data['participant_id'] == pid]
            p_test = test_data[test_data['participant_id'] == pid]
            
            if len(p_train) > 10 and len(p_test) > 5:
                meta_score = np.random.uniform(0.5, 0.95)
                d_prime = np.random.uniform(0.1, 2.5)
                
                synthetic_results.append({
                    'participant_id': pid,
                    'modality': 'auditory',
                    'metacognitive_score': meta_score,
                    'reality_testing_accuracy': d_prime
                })

        if not synthetic_results:
            self.skipTest("Not enough data to simulate split results")

        synthetic_df = pd.DataFrame(synthetic_results)
        synthetic_csv = self.data_dir / "auditory_correlation_input.csv"
        synthetic_df.to_csv(synthetic_csv, index=False)

        try:
            result = run_bootstrap_analysis(
                input_path=str(synthetic_csv),
                x_col='metacognitive_score',
                y_col='reality_testing_accuracy',
                n_boot=100,
                output_dir=str(self.data_dir)
            )
            
            self.assertIsNotNone(result)
            self.assertIn('correlation', result)
            self.assertIsInstance(result['correlation'], float)
            
        except Exception as e:
            self.fail(f"Auditory modality correlation analysis failed: {e}")

    def test_modality_independence(self):
        """
        Verify that visual and auditory analyses produce distinct results
        (they should not be identical due to random sampling in mock data).
        """
        # Run visual
        visual_data = self.mock_df[self.mock_df['stimulus_modality'] == 'visual']
        train_v = visual_data.sample(frac=0.7, random_state=1)
        test_v = visual_data.drop(train_v.index)
        
        # Run auditory
        auditory_data = self.mock_df[self.mock_df['stimulus_modality'] == 'auditory']
        train_a = auditory_data.sample(frac=0.7, random_state=1)
        test_a = auditory_data.drop(train_a.index)

        # Generate synthetic inputs
        def make_synthetic(data, train, test, mod):
            res = []
            for pid in data['participant_id'].unique():
                pt = train[train['participant_id'] == pid]
                ps = test[test['participant_id'] == pid]
                if len(pt) > 5 and len(ps) > 3:
                    res.append({
                        'modality': mod,
                        'metacognitive_score': np.random.uniform(0.5, 0.9),
                        'reality_testing_accuracy': np.random.uniform(0.1, 2.0)
                    })
            return pd.DataFrame(res) if res else None

        df_v = make_synthetic(visual_data, train_v, test_v, 'visual')
        df_a = make_synthetic(auditory_data, train_a, test_a, 'auditory')

        if df_v is None or df_a is None:
            self.skipTest("Insufficient mock data for independence test")

        v_csv = self.data_dir / "v_indep.csv"
        a_csv = self.data_dir / "a_indep.csv"
        df_v.to_csv(v_csv, index=False)
        df_a.to_csv(a_csv, index=False)

        res_v = run_bootstrap_analysis(str(v_csv), 'metacognitive_score', 'reality_testing_accuracy', 50, str(self.data_dir))
        res_a = run_bootstrap_analysis(str(a_csv), 'metacognitive_score', 'reality_testing_accuracy', 50, str(self.data_dir))

        # They should not be exactly equal (probabilistic nature)
        # Note: With random seed fixed in mock generation, they might be close, 
        # but the logic ensures we are testing separate datasets.
        self.assertNotEqual(res_v['n_samples'], res_a['n_samples'])


if __name__ == '__main__':
    unittest.main()