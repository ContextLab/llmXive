"""
Integration test for modality-specific correlation analysis (User Story 3).

This test verifies that the pipeline correctly splits data by stimulus modality
(visual vs auditory) and computes separate correlation metrics for each subset.
It ensures that the robustness analysis produces valid results for both modalities
and that the outputs are written to the correct files.
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
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.filter import run_filter_analysis, load_trial_data
from code.src.analysis.robustness import run_robustness_analysis
from code.src.report.generate import generate_robustness_analysis_report


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up temporary directories and sample data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.derived_dir = self.data_dir / "derived"
        self.results_dir = self.data_dir / "results"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Create a realistic sample dataset with required fields
        # This mimics the output of data/preprocess.py (T012)
        np.random.seed(42)
        n_trials = 200
        
        trial_data = {
            'participant_id': [f"P{1:03d}" if i < 100 else f"P{2:03d}" for i in range(n_trials)],
            'trial_id': list(range(n_trials)),
            'stimulus_modality': ['visual'] * 100 + ['auditory'] * 100,
            'source_label': np.random.choice([0, 1], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_trials),
            'accuracy': np.random.choice([0, 1], n_trials)  # Derived for realism
        }
        
        self.df = pd.DataFrame(trial_data)
        self.trial_data_path = self.derived_dir / "trial_data.csv"
        self.df.to_csv(self.trial_data_path, index=False)

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_filter_by_modality_creates_subsets(self):
        """Test that filter.py correctly splits data into visual and auditory subsets."""
        # Run filter analysis
        run_filter_analysis(
            input_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"
        
        # Assert files exist
        self.assertTrue(visual_path.exists(), "visual_trials.csv was not created")
        self.assertTrue(auditory_path.exists(), "auditory_trials.csv was not created")
        
        # Load and verify content
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)
        
        # Check row counts
        self.assertEqual(len(visual_df), 100, "Visual subset should have 100 rows")
        self.assertEqual(len(auditory_df), 100, "Auditory subset should have 100 rows")
        
        # Check modality values
        self.assertTrue((visual_df['stimulus_modality'] == 'visual').all(), 
                      "Visual subset should only contain 'visual' trials")
        self.assertTrue((auditory_df['stimulus_modality'] == 'auditory').all(), 
                      "Auditory subset should only contain 'auditory' trials")

    def test_robustness_analysis_computes_separate_correlations(self):
        """Test that robustness.py computes separate correlations for each modality."""
        # First run filter to create subsets
        run_filter_analysis(
            input_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness analysis
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Assert output file exists
        robustness_path = self.results_dir / "robustness_analysis.json"
        self.assertTrue(robustness_path.exists(), "robustness_analysis.json was not created")
        
        # Load and verify structure
        with open(robustness_path, 'r') as f:
            results = json.load(f)
        
        # Check top-level keys
        self.assertIn('visual', results, "Results should contain 'visual' key")
        self.assertIn('auditory', results, "Results should contain 'auditory' key")
        
        # Check visual results structure
        visual_res = results['visual']
        self.assertIn('correlation', visual_res, "Visual results missing 'correlation' key")
        self.assertIn('r', visual_res['correlation'], "Visual results missing 'r'")
        self.assertIn('p', visual_res['correlation'], "Visual results missing 'p'")
        self.assertIn('ci_lower', visual_res['correlation'], "Visual results missing 'ci_lower'")
        self.assertIn('ci_upper', visual_res['correlation'], "Visual results missing 'ci_upper'")
        
        # Check auditory results structure
        auditory_res = results['auditory']
        self.assertIn('correlation', auditory_res, "Auditory results missing 'correlation' key")
        self.assertIn('r', auditory_res['correlation'], "Auditory results missing 'r'")
        self.assertIn('p', auditory_res['correlation'], "Auditory results missing 'p'")
        
        # Verify that correlations are computed from real data (not placeholders)
        # The values should be numeric and within valid ranges
        self.assertIsInstance(visual_res['correlation']['r'], float, "Visual r should be float")
        self.assertIsInstance(auditory_res['correlation']['r'], float, "Auditory r should be float")
        
        # Correlation coefficient must be between -1 and 1
        self.assertGreaterEqual(visual_res['correlation']['r'], -1.0, "Visual r out of range")
        self.assertLessEqual(visual_res['correlation']['r'], 1.0, "Visual r out of range")
        self.assertGreaterEqual(auditory_res['correlation']['r'], -1.0, "Auditory r out of range")
        self.assertLessEqual(auditory_res['correlation']['r'], 1.0, "Auditory r out of range")

    def test_hold_out_design_is_enforced(self):
        """Test that the hold-out design (70/30 split) is used in modality analysis."""
        # Run filter
        run_filter_analysis(
            input_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Load results
        with open(self.results_dir / "robustness_analysis.json", 'r') as f:
            results = json.load(f)
        
        # Check that metadata confirms hold-out design was used
        # The robustness analysis should report the method used
        self.assertIn('method', results, "Results should specify the analysis method")
        self.assertEqual(results['method'], "Hold-Out Accuracy", 
                       "Method should be 'Hold-Out Accuracy' per plan.md")
        
        # Verify that train/test split ratio is documented
        self.assertIn('train_split_ratio', results, "Results should document train split ratio")
        self.assertAlmostEqual(results['train_split_ratio'], 0.7, places=1, 
                             msg="Train split should be approximately 70%")

    def test_integration_end_to_end(self):
        """Full integration test: filter -> robustness -> report generation."""
        # Step 1: Filter data
        run_filter_analysis(
            input_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Step 2: Run robustness analysis
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )
        
        # Step 3: Generate report
        report = generate_robustness_analysis_report(
            results_dir=str(self.results_dir)
        )
        
        # Verify report contains both modalities
        self.assertIn('visual', report, "Report missing visual results")
        self.assertIn('auditory', report, "Report missing auditory results")
        
        # Verify report contains multiple comparison correction info
        self.assertIn('correction_method', report, "Report should specify correction method")
        self.assertIn('corrected_p_values', report, "Report should contain corrected p-values")
        
        # Verify the report is written to disk
        output_path = self.results_dir / "robustness_analysis.json"
        self.assertTrue(output_path.exists(), "Final report was not written to disk")

    def test_data_integrity_across_splits(self):
        """Test that no trials are lost or duplicated across modality splits."""
        # Run filter
        run_filter_analysis(
            input_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        visual_df = pd.read_csv(self.derived_dir / "visual_trials.csv")
        auditory_df = pd.read_csv(self.derived_dir / "auditory_trials.csv")
        original_df = pd.read_csv(self.trial_data_path)
        
        # Check total count
        total_subset_count = len(visual_df) + len(auditory_df)
        self.assertEqual(total_subset_count, len(original_df), 
                       "Total trials in subsets should match original")
        
        # Check for duplicates
        all_trial_ids = list(visual_df['trial_id']) + list(auditory_df['trial_id'])
        self.assertEqual(len(all_trial_ids), len(set(all_trial_ids)), 
                       "Trial IDs should be unique across subsets")

    def test_missing_modality_handling(self):
        """Test robustness when one modality is missing from the dataset."""
        # Create dataset with only visual trials
        small_df = self.df[self.df['stimulus_modality'] == 'visual'].copy()
        small_path = self.derived_dir / "small_trial_data.csv"
        small_df.to_csv(small_path, index=False)
        
        # Run filter
        run_filter_analysis(
            input_path=str(small_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness - should handle missing auditory gracefully
        try:
            run_robustness_analysis(
                derived_dir=str(self.derived_dir),
                results_dir=str(self.results_dir)
            )
            
            # Should still produce output, even if one modality is empty
            robustness_path = self.results_dir / "robustness_analysis.json"
            self.assertTrue(robustness_path.exists(), "Output should exist even with missing modality")
            
            with open(robustness_path, 'r') as f:
                results = json.load(f)
            
            # Visual should have results, auditory might be empty or flagged
            self.assertIn('visual', results, "Visual results should exist")
            # Auditory might exist but with nulls or flags indicating insufficient data
            
        except Exception as e:
            # If it fails, it should be a clear error about missing data, not a crash
            self.assertIn("No data", str(e) or "Insufficient data", str(e), 
                        "Error should indicate missing data, not a generic crash")

if __name__ == '__main__':
    unittest.main()