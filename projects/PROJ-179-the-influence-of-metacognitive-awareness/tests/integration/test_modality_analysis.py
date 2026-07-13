"""
Integration test for modality-specific correlation analysis (T025).

This test verifies that the robustness analysis pipeline correctly:
1. Loads filtered data for visual and auditory modalities.
2. Computes hold-out metrics (Type-2 AUC on train, d' on test) for each modality.
3. Runs bootstrap resampling to generate 95% CIs.
4. Produces the expected output structure in data/results/robustness_analysis.json.

Prerequisites:
- T026 (filter.py) must have run to produce data/derived/visual_trials.csv and data/derived/auditory_trials.csv.
- T014 (correlation.py) logic must be available in src/analysis/robustness.py.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.robustness import (
    load_filtered_data,
    compute_hold_out_metrics_for_modality,
    run_bootstrap_correlation,
    write_results,
    run_robustness_analysis
)
from src.analysis.filter import run_filter_analysis
from src.utils.stats import compute_type2_auc, compute_sdt_metrics
from config.env_config import load_config


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up temporary directories and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.derived_dir = self.data_dir / "derived"
        self.results_dir = self.data_dir / "results"
        
        self.data_dir.mkdir(parents=True)
        self.derived_dir.mkdir(parents=True)
        self.results_dir.mkdir(parents=True)

        # Create a mock trial dataset with both modalities
        np.random.seed(42)
        n_trials = 200
        n_participants = 10

        # Generate mock data
        data = {
            'participant_id': np.repeat([f"sub-{i:03d}" for i in range(n_participants)], n_trials // n_participants),
            'trial_id': range(n_trials),
            'stimulus_modality': np.random.choice(['visual', 'auditory'], n_trials),
            'source_label': np.random.choice(['real', 'fake'], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.randint(1, 6, n_trials),
            'is_correct': np.random.choice([0, 1], n_trials)
        }
        
        self.mock_df = pd.DataFrame(data)
        self.input_csv_path = self.data_dir / "raw_trials.csv"
        self.mock_df.to_csv(self.input_csv_path, index=False)

        # Mock config for the test
        self.config = {
            "paths": {
                "base": self.temp_dir,
                "derived_data": str(self.derived_dir),
                "results": str(self.results_dir)
            },
            "analysis": {
                "random_seed": 42,
                "bootstrap_count": 10  # Small number for fast testing
            }
        }

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filter_analysis_creates_modality_files(self):
        """Test that T026 filter analysis creates separate modality CSV files."""
        # Run the filter analysis
        run_filter_analysis(self.config)

        # Check that the expected files were created
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"

        self.assertTrue(visual_path.exists(), "Visual trials file not created")
        self.assertTrue(auditory_path.exists(), "Auditory trials file not created")

        # Verify content
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)

        self.assertEqual(visual_df['stimulus_modality'].unique()[0], 'visual')
        self.assertEqual(auditory_df['stimulus_modality'].unique()[0], 'auditory')

    def test_compute_hold_out_metrics_for_modality(self):
        """Test that hold-out metrics are computed correctly for a single modality."""
        # First, ensure filtered data exists
        run_filter_analysis(self.config)
        
        visual_path = self.derived_dir / "visual_trials.csv"
        df = load_filtered_data(str(visual_path))

        # Run the hold-out computation
        result = compute_hold_out_metrics_for_modality(df, seed=42)

        # Verify structure
        self.assertIn('r', result, "Correlation coefficient 'r' missing")
        self.assertIn('p', result, "P-value 'p' missing")
        self.assertIn('ci_lower', result, "CI lower bound missing")
        self.assertIn('ci_upper', result, "CI upper bound missing")
        self.assertIn('n_train', result, "Training set size missing")
        self.assertIn('n_test', result, "Test set size missing")

        # Verify types and ranges
        self.assertIsInstance(result['r'], (int, float))
        self.assertIsInstance(result['p'], (int, float))
        self.assertGreaterEqual(result['r'], -1.0)
        self.assertLessEqual(result['r'], 1.0)
        self.assertGreaterEqual(result['p'], 0.0)
        self.assertLessEqual(result['p'], 1.0)

    def test_run_bootstrap_correlation(self):
        """Test that bootstrap correlation runs and returns valid results."""
        run_filter_analysis(self.config)
        visual_path = self.derived_dir / "visual_trials.csv"
        df = load_filtered_data(str(visual_path))

        # Run bootstrap with a small count for speed
        result = run_bootstrap_correlation(df, n_resamples=5, seed=42)

        self.assertIn('r', result)
        self.assertIn('p', result)
        self.assertIn('ci_lower', result)
        self.assertIn('ci_upper', result)
        self.assertIn('n_resamples', result)
        self.assertEqual(result['n_resamples'], 5)

    def test_run_robustness_analysis_integration(self):
        """
        Full integration test: run the entire robustness analysis pipeline
        and verify the output file is created with correct structure.
        """
        # Run the full robustness analysis
        run_robustness_analysis(self.config)

        # Check output file
        output_path = self.results_dir / "robustness_analysis.json"
        self.assertTrue(output_path.exists(), "robustness_analysis.json not created")

        # Load and verify content
        with open(output_path, 'r') as f:
            results = json.load(f)

        # Verify top-level keys
        self.assertIn('visual', results, "Visual modality results missing")
        self.assertIn('auditory', results, "Auditory modality results missing")

        # Verify structure for each modality
        for modality in ['visual', 'auditory']:
            mod_results = results[modality]
            self.assertIn('r', mod_results, f"Correlation 'r' missing for {modality}")
            self.assertIn('p', mod_results, f"P-value 'p' missing for {modality}")
            self.assertIn('ci_95_lower', mod_results, f"CI lower missing for {modality}")
            self.assertIn('ci_95_upper', mod_results, f"CI upper missing for {modality}")
            self.assertIn('n_trials', mod_results, f"Trial count missing for {modality}")
            self.assertIn('bootstrap_count', mod_results, f"Bootstrap count missing for {modality}")

        # Verify that results are different (or at least computed) for each modality
        # Note: With random data they might be similar, but the structure must be correct.
        self.assertIsInstance(results['visual']['r'], (int, float))
        self.assertIsInstance(results['auditory']['r'], (int, float))

    def test_empty_modality_handling(self):
        """Test that the pipeline handles a modality with zero trials gracefully."""
        # Create a dataset with only one modality
        np.random.seed(42)
        n_trials = 100
        data = {
            'participant_id': [f"sub-001"] * n_trials,
            'trial_id': range(n_trials),
            'stimulus_modality': ['visual'] * n_trials,  # Only visual
            'source_label': np.random.choice(['real', 'fake'], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.randint(1, 6, n_trials),
            'is_correct': np.random.choice([0, 1], n_trials)
        }
        
        mock_df = pd.DataFrame(data)
        input_csv = self.data_dir / "only_visual.csv"
        mock_df.to_csv(input_csv, index=False)

        # Manually create filtered files to simulate T026 output
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"
        mock_df.to_csv(visual_path, index=False)
        # Create empty auditory file with headers
        pd.DataFrame(columns=mock_df.columns).to_csv(auditory_path, index=False)

        # Run robustness analysis
        try:
            run_robustness_analysis(self.config)
            
            output_path = self.results_dir / "robustness_analysis.json"
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            # Visual should have data
            self.assertIn('r', results['visual'])
            
            # Auditory should have NaN or be handled gracefully
            # The implementation should not crash
            self.assertIn('r', results['auditory'])
            
        except Exception as e:
            # If it crashes, that's a failure of the implementation
            self.fail(f"Robustness analysis crashed on empty modality: {e}")


if __name__ == '__main__':
    unittest.main()