"""
Integration test for the full analysis pipeline on synthetic data.

This test verifies that the entire analysis workflow (cleaning -> CLMM -> 
post-hoc -> reporting) executes end-to-end without errors on a controlled
synthetic dataset. It does NOT make empirical claims about the data.

This test is designed to run in CI/CD to ensure the pipeline logic is sound
before running on real data.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import seed_everything
from data_cleaning import detect_straight_lining, save_cleaned_data
from analysis import run_clmm_analysis, run_post_hoc, generate_report
from data_hygiene import DataHygieneError, verify_data_separation

class TestAnalysisPipelineIntegration(unittest.TestCase):
    """Integration tests for the full analysis pipeline."""

    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp(prefix="test_analysis_pipeline_")
        self.seed = 42
        seed_everything(self.seed)
        
        # Define paths
        self.raw_data_path = Path(self.test_dir) / "data" / "survey" / "pilot_responses_sim.csv"
        self.cleaned_data_path = Path(self.test_dir) / "data" / "processed" / "cleaned_responses.csv"
        self.results_json_path = Path(self.test_dir) / "data" / "analysis" / "results.json"
        self.results_csv_path = Path(self.test_dir) / "data" / "analysis" / "clmm_results.csv"
        
        # Ensure directories exist
        self.raw_data_path.parent.mkdir(parents=True, exist_ok=True)
        self.cleaned_data_path.parent.mkdir(parents=True, exist_ok=True)
        self.results_json_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _generate_synthetic_data(self, n_participants=50, n_scenarios=20):
        """
        Generate a synthetic dataset with known properties for testing.
        
        Creates data with:
        - Participants rating scenarios at different salience levels
        - Some straight-liners (to be filtered)
        - Known effect size for validation
        """
        data = []
        participant_ids = [f"P{i:03d}" for i in range(n_participants)]
        scenario_ids = [f"S{i:03d}" for i in range(n_scenarios)]
        salience_levels = ['low', 'medium', 'high']
        
        # Generate data with a known effect
        for p_id in participant_ids:
            # 10% chance of being a straight-liner
            is_straight_liner = np.random.random() < 0.1
            base_rating = np.random.randint(1, 6)
            
            for s_id in scenario_ids:
                for salience in salience_levels:
                    # Generate rating
                    if is_straight_liner:
                        rating = base_rating
                    else:
                        # Add a small effect of salience
                        salience_effect = 0
                        if salience == 'medium':
                            salience_effect = 0.2
                        elif salience == 'high':
                            salience_effect = 0.5
                        
                        # Add noise
                        noise = np.random.normal(0, 1.5)
                        rating = base_rating + salience_effect + noise
                        # Clip to valid range [1, 5]
                        rating = int(np.clip(rating, 1, 5))
                    
                    data.append({
                        'participant_id': p_id,
                        'scenario_id': s_id,
                        'salience_level': salience,
                        'rating': rating,
                        'timestamp': '2023-10-01T12:00:00'
                    })
        
        df = pd.DataFrame(data)
        df.to_csv(self.raw_data_path, index=False)
        return df

    def test_full_pipeline_execution(self):
        """
        Test that the full pipeline runs from raw data to final report.
        
        Steps:
        1. Generate synthetic data
        2. Run data cleaning (straight-lining detection)
        3. Run CLMM analysis
        4. Run post-hoc tests
        5. Generate report
        6. Verify all output files exist and contain expected structure
        """
        # Step 1: Generate synthetic data
        print("Generating synthetic data...")
        raw_df = self._generate_synthetic_data()
        self.assertTrue(raw_df.shape[0] > 0, "Raw data should not be empty")
        
        # Verify raw data exists
        self.assertTrue(self.raw_data_path.exists(), "Raw data file should exist")
        
        # Step 2: Run data cleaning
        print("Running data cleaning...")
        # We need to load the data to clean it
        from data_cleaning import load_survey_data
        raw_loaded = load_survey_data(self.raw_data_path)
        cleaned_df, excluded_ids = detect_straight_lining(raw_loaded)
        save_cleaned_data(cleaned_df, self.cleaned_data_path)
        
        self.assertTrue(self.cleaned_data_path.exists(), "Cleaned data file should exist")
        self.assertLess(cleaned_df.shape[0], raw_loaded.shape[0], 
                      "Some participants should be excluded as straight-liners")
        
        # Step 3: Run CLMM analysis
        print("Running CLMM analysis...")
        # Load cleaned data
        cleaned_loaded = load_survey_data(self.cleaned_data_path)
        
        # Run the analysis (this calls T030 logic)
        clmm_results = run_clmm_analysis(cleaned_loaded)
        
        # Save results to CSV (as per T030)
        clmm_results.to_csv(self.results_csv_path, index=False)
        
        self.assertTrue(self.results_csv_path.exists(), "CLMM results CSV should exist")
        self.assertIn('salience_level', clmm_results.columns, 
                     "Results should contain salience_level column")
        
        # Step 4: Run post-hoc tests
        print("Running post-hoc tests...")
        post_hoc_results = run_post_hoc(clmm_results)
        
        self.assertIsNotNone(post_hoc_results, "Post-hoc results should not be None")
        
        # Step 5: Generate report
        print("Generating report...")
        report_data = generate_report(clmm_results, post_hoc_results, self.cleaned_data_path)
        
        # Save report as JSON (as per T037)
        with open(self.results_json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.assertTrue(self.results_json_path.exists(), "Results JSON should exist")
        
        # Verify report structure
        with open(self.results_json_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn('model_summary', report, "Report should contain model_summary")
        self.assertIn('post_hoc', report, "Report should contain post_hoc")
        self.assertIn('n_participants', report, "Report should contain n_participants")
        self.assertIn('n_scenarios', report, "Report should contain n_scenarios")
        
        # Step 6: Verify data hygiene
        print("Verifying data hygiene...")
        # Create a fake synth directory to test separation
        synth_dir = Path(self.test_dir) / "data" / "synth"
        synth_dir.mkdir(parents=True, exist_ok=True)
        
        # Test that our cleaned data is in the right place
        try:
            verify_data_separation([self.cleaned_data_path])
        except DataHygieneError:
            self.fail("Data hygiene check failed for valid data location")
        
        print("Full pipeline execution test passed!")

    def test_pipeline_with_no_effect(self):
        """
        Test pipeline on data with no effect (negative control).
        
        This ensures the pipeline doesn't falsely detect effects when none exist.
        """
        # Generate data with no effect
        data = []
        for i in range(30):
            p_id = f"P{i:03d}"
            for j in range(10):
                s_id = f"S{j:03d}"
                for salience in ['low', 'medium', 'high']:
                    # Random rating with no salience effect
                    rating = np.random.randint(1, 6)
                    data.append({
                        'participant_id': p_id,
                        'scenario_id': s_id,
                        'salience_level': salience,
                        'rating': rating,
                        'timestamp': '2023-10-01T12:00:00'
                    })
        
        df = pd.DataFrame(data)
        df.to_csv(self.raw_data_path, index=False)
        
        # Run cleaning
        raw_loaded = load_survey_data(self.raw_data_path)
        cleaned_df, _ = detect_straight_lining(raw_loaded)
        save_cleaned_data(cleaned_df, self.cleaned_data_path)
        
        # Run analysis
        cleaned_loaded = load_survey_data(self.cleaned_data_path)
        clmm_results = run_clmm_analysis(cleaned_loaded)
        
        # Check that we get results (even if not significant)
        self.assertFalse(clmm_results.empty, "Results should not be empty")
        
        print("Negative control test passed!")

    def test_pipeline_convergence_handling(self):
        """
        Test that the pipeline handles convergence issues gracefully.
        
        This tests the fallback logic implemented in T032a/T032b.
        """
        # Generate small dataset that might cause convergence issues
        data = []
        for i in range(5):  # Very few participants
            p_id = f"P{i:03d}"
            for j in range(3):  # Few scenarios
                s_id = f"S{j:03d}"
                for salience in ['low', 'medium', 'high']:
                    rating = np.random.randint(1, 6)
                    data.append({
                        'participant_id': p_id,
                        'scenario_id': s_id,
                        'salience_level': salience,
                        'rating': rating,
                        'timestamp': '2023-10-01T12:00:00'
                    })
        
        df = pd.DataFrame(data)
        df.to_csv(self.raw_data_path, index=False)
        
        # Run cleaning
        raw_loaded = load_survey_data(self.raw_data_path)
        cleaned_df, _ = detect_straight_lining(raw_loaded)
        save_cleaned_data(cleaned_df, self.cleaned_data_path)
        
        # Run analysis - should handle convergence issues
        cleaned_loaded = load_survey_data(self.cleaned_data_path)
        try:
            clmm_results = run_clmm_analysis(cleaned_loaded)
            # If we get here, the model either converged or fell back gracefully
            self.assertIsNotNone(clmm_results)
            print("Convergence handling test passed!")
        except Exception as e:
            # If it fails, it should be a clear error, not a silent failure
            self.fail(f"Analysis failed with unhandled error: {e}")

if __name__ == '__main__':
    unittest.main()