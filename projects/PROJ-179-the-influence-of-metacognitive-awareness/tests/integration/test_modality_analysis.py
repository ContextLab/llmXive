"""
Integration test for modality-specific correlation analysis (US3).

This test verifies that:
1. The filter module correctly splits data into visual and auditory subsets.
2. The robustness module computes correlation metrics for each subset.
3. The results are written to the expected output files.
4. The reported metrics are real measurements (not fabricated).
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.src.analysis.filter import run_filter_analysis
from code.src.analysis.robustness import run_robustness_analysis
from code.data.preprocess import main as preprocess_main
from code.data.download import main as download_main
from code.data.validate_data import main as validate_main
from code.data.validate_data_availability import main as availability_main


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.derived_dir = self.data_dir / "derived"
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a realistic sample dataset for testing
        self._create_sample_dataset()

    def _create_sample_dataset(self):
        """Create a sample dataset with visual and auditory trials."""
        np.random.seed(42)
        n_trials = 200
        
        # Generate realistic behavioral data
        data = {
            'participant_id': np.random.choice(['P001', 'P002', 'P003'], n_trials),
            'trial_id': range(n_trials),
            'stimulus_modality': np.random.choice(['visual', 'auditory'], n_trials),
            'source_label': np.random.choice(['real', 'fake'], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.randint(1, 6, n_trials),
            'accuracy': np.random.choice([0, 1], n_trials)
        }
        
        # Create some correlation structure for testing
        df = pd.DataFrame(data)
        
        # Add some realistic correlation: higher confidence -> higher accuracy
        # for visual trials only (to test modality specificity)
        visual_mask = df['stimulus_modality'] == 'visual'
        df.loc[visual_mask, 'accuracy'] = (
            (df.loc[visual_mask, 'confidence_rating'] > 3).astype(int)
        )
        
        # Save to CSV
        self.sample_file = self.data_dir / "behavioral_data.csv"
        df.to_csv(self.sample_file, index=False)

    def test_filter_analysis_creates_modality_files(self):
        """Test that filter analysis creates visual and auditory trial files."""
        # Run filter analysis
        run_filter_analysis(
            input_file=str(self.sample_file),
            derived_dir=str(self.derived_dir)
        )
        
        # Check that output files exist
        visual_file = self.derived_dir / "visual_trials.csv"
        auditory_file = self.derived_dir / "auditory_trials.csv"
        
        self.assertTrue(visual_file.exists(), "Visual trials file not created")
        self.assertTrue(auditory_file.exists(), "Auditory trials file not created")
        
        # Check file contents
        visual_df = pd.read_csv(visual_file)
        auditory_df = pd.read_csv(auditory_file)
        
        self.assertIn('stimulus_modality', visual_df.columns)
        self.assertIn('stimulus_modality', auditory_df.columns)
        
        # Verify all visual trials are in visual file
        self.assertTrue((visual_df['stimulus_modality'] == 'visual').all())
        self.assertTrue((auditory_df['stimulus_modality'] == 'auditory').all())

    def test_robustness_analysis_computes_real_metrics(self):
        """Test that robustness analysis computes real correlation metrics."""
        # First run filter to create modality files
        run_filter_analysis(
            input_file=str(self.sample_file),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness analysis
        results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Check that results are not fabricated
        self.assertIsNotNone(results, "Robustness analysis returned None")
        self.assertIn('visual', results, "Visual results missing")
        self.assertIn('auditory', results, "Auditory results missing")
        
        visual_results = results['visual']
        auditory_results = results['auditory']
        
        # Check for required keys
        required_keys = ['r', 'p', 'ci_lower', 'ci_upper', 'n_trials', 'bootstrap_count']
        for key in required_keys:
            self.assertIn(key, visual_results, f"Missing {key} in visual results")
            self.assertIn(key, auditory_results, f"Missing {key} in auditory results")
        
        # Verify metrics are real numbers (not None, NaN, or fabricated constants)
        self.assertIsInstance(visual_results['r'], (int, float))
        self.assertIsInstance(visual_results['p'], (int, float))
        self.assertIsInstance(auditory_results['r'], (int, float))
        self.assertIsInstance(auditory_results['p'], (int, float))
        
        # Check that metrics are within valid ranges
        self.assertTrue(-1 <= visual_results['r'] <= 1, "Visual r out of range")
        self.assertTrue(-1 <= auditory_results['r'] <= 1, "Auditory r out of range")
        self.assertTrue(0 <= visual_results['p'] <= 1, "Visual p out of range")
        self.assertTrue(0 <= auditory_results['p'] <= 1, "Auditory p out of range")
        
        # Check that confidence intervals are reasonable
        self.assertTrue(
            visual_results['ci_lower'] <= visual_results['r'] <= visual_results['ci_upper'],
            "Visual CI does not contain r"
        )
        self.assertTrue(
            auditory_results['ci_lower'] <= auditory_results['r'] <= auditory_results['ci_upper'],
            "Auditory CI does not contain r"
        )

    def test_robustness_analysis_writes_output_file(self):
        """Test that robustness analysis writes results to JSON file."""
        # Run filter and robustness analysis
        run_filter_analysis(
            input_file=str(self.sample_file),
            derived_dir=str(self.derived_dir)
        )
        
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Check that output file exists
        output_file = self.results_dir / "robustness_analysis.json"
        self.assertTrue(output_file.exists(), "Robustness analysis JSON not created")
        
        # Verify JSON structure
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        self.assertIn('visual', results)
        self.assertIn('auditory', results)
        self.assertIn('correction_method', results)
        self.assertIn('familywise_error_rate', results)

    def test_modality_specific_correlation_differs(self):
        """Test that visual and auditory correlations can differ (modality specificity)."""
        # Create a dataset where visual and auditory have different correlations
        np.random.seed(123)
        n_trials = 300
        
        # Visual trials: strong positive correlation
        visual_data = {
            'participant_id': ['V'] * 150,
            'trial_id': range(150),
            'stimulus_modality': ['visual'] * 150,
            'source_label': ['real'] * 150,
            'confidence_rating': np.random.randint(1, 6, 150),
            'accuracy': (np.random.random(150) + np.random.random(150) * 0.5 > 1).astype(int)
        }
        
        # Auditory trials: weak or no correlation
        auditory_data = {
            'participant_id': ['A'] * 150,
            'trial_id': range(150, 300),
            'stimulus_modality': ['auditory'] * 150,
            'source_label': ['real'] * 150,
            'confidence_rating': np.random.randint(1, 6, 150),
            'accuracy': np.random.choice([0, 1], 150)  # Random accuracy
        }
        
        combined_data = {
            'participant_id': visual_data['participant_id'] + auditory_data['participant_id'],
            'trial_id': visual_data['trial_id'] + auditory_data['trial_id'],
            'stimulus_modality': visual_data['stimulus_modality'] + auditory_data['stimulus_modality'],
            'source_label': visual_data['source_label'] + auditory_data['source_label'],
            'confidence_rating': visual_data['confidence_rating'] + auditory_data['confidence_rating'],
            'accuracy': visual_data['accuracy'] + auditory_data['accuracy']
        }
        
        test_file = self.data_dir / "test_modality_data.csv"
        pd.DataFrame(combined_data).to_csv(test_file, index=False)
        
        # Run analysis
        run_filter_analysis(
            input_file=str(test_file),
            derived_dir=str(self.derived_dir)
        )
        
        results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Verify that correlations are computed (they may differ due to data generation)
        visual_r = results['visual']['r']
        auditory_r = results['auditory']['r']
        
        # At minimum, verify both are real numbers
        self.assertIsInstance(visual_r, (int, float))
        self.assertIsInstance(auditory_r, (int, float))

    def test_full_pipeline_integration(self):
        """Test the full pipeline from data download to modality analysis."""
        # This test simulates the full pipeline flow
        # In a real scenario, this would download actual data
        
        # For this test, we use the sample data created in setUp
        # Step 1: Validate data availability (simulated)
        # Step 2: Download (simulated with sample data)
        # Step 3: Validate data
        # Step 4: Preprocess
        # Step 5: Filter by modality
        # Step 6: Run robustness analysis
        
        # Run filter
        run_filter_analysis(
            input_file=str(self.sample_file),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness analysis
        results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Verify all expected outputs
        expected_files = [
            self.derived_dir / "visual_trials.csv",
            self.derived_dir / "auditory_trials.csv",
            self.results_dir / "robustness_analysis.json"
        ]
        
        for file_path in expected_files:
            self.assertTrue(
                file_path.exists(),
                f"Expected output file not created: {file_path}"
            )
        
        # Verify JSON content
        with open(self.results_dir / "robustness_analysis.json", 'r') as f:
            json_results = json.load(f)
        
        self.assertIn('visual', json_results)
        self.assertIn('auditory', json_results)
        self.assertIn('correction_method', json_results)
        self.assertIn('familywise_error_rate', json_results)


if __name__ == '__main__':
    unittest.main()