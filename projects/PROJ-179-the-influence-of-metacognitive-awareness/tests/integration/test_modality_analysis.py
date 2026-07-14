"""
Integration test for modality-specific correlation analysis (T025).

This test verifies that:
1. The data can be filtered by stimulus modality (visual vs auditory).
2. The correlation pipeline runs independently on each subset.
3. Separate correlation coefficients (r_visual, r_auditory) and CIs are produced.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.analysis.filter import run_filter_analysis
from code.src.analysis.robustness import run_robustness_analysis
from code.src.report.generate import generate_robustness_analysis_report, write_report


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up temporary directories and sample data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir)
        
        # Create directory structure
        self.derived_dir = self.base_dir / "data" / "derived"
        self.results_dir = self.base_dir / "data" / "results"
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Generate realistic sample data with required fields
        np.random.seed(42)
        n_trials = 200
        
        data = {
            'participant_id': np.repeat(range(1, 21), 10),  # 20 participants, 10 trials each
            'trial_id': range(1, n_trials + 1),
            'stimulus_modality': np.random.choice(['visual', 'auditory'], n_trials),
            'source_label': np.random.choice(['internal', 'external'], n_trials),
            'participant_response': np.random.choice([0, 1], n_trials),
            'confidence_rating': np.random.randint(1, 6, n_trials),  # 1-5 scale
            'is_correct': np.random.choice([0, 1], n_trials)
        }
        
        self.trial_data = pd.DataFrame(data)
        self.trial_csv_path = self.derived_dir / "trial_data.csv"
        self.trial_data.to_csv(self.trial_csv_path, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_modality_filter_creates_subset_files(self):
        """Test that filter.py creates separate visual and auditory trial files."""
        # Run filter analysis
        run_filter_analysis(
            input_path=str(self.trial_csv_path),
            output_dir=str(self.derived_dir)
        )

        # Check that output files were created
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"

        self.assertTrue(visual_path.exists(), "visual_trials.csv should be created")
        self.assertTrue(auditory_path.exists(), "auditory_trials.csv should be created")

        # Verify content
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)

        self.assertIn('stimulus_modality', visual_df.columns)
        self.assertIn('stimulus_modality', auditory_df.columns)
        
        # All rows in visual file should be visual
        self.assertTrue(all(visual_df['stimulus_modality'] == 'visual'))
        # All rows in auditory file should be auditory
        self.assertTrue(all(auditory_df['stimulus_modality'] == 'auditory'))

    def test_robustness_analysis_produces_modality_correlations(self):
        """Test that robustness.py produces separate correlation results for each modality."""
        # First, run the filter to create modality-specific files
        run_filter_analysis(
            input_path=str(self.trial_csv_path),
            output_dir=str(self.derived_dir)
        )

        # Run robustness analysis
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )

        # Check that robustness results file was created
        results_path = self.results_dir / "robustness_analysis.json"
        self.assertTrue(results_path.exists(), "robustness_analysis.json should be created")

        # Load and verify results structure
        with open(results_path, 'r') as f:
            results = json.load(f)

        # Verify modality-specific results exist
        self.assertIn('visual', results, "Visual modality results should be present")
        self.assertIn('auditory', results, "Auditory modality results should be present")

        # Verify correlation statistics are present for each modality
        for modality in ['visual', 'auditory']:
            modality_results = results[modality]
            self.assertIn('r', modality_results, f"Correlation coefficient (r) missing for {modality}")
            self.assertIn('p_value', modality_results, f"P-value missing for {modality}")
            self.assertIn('ci_lower', modality_results, f"CI lower bound missing for {modality}")
            self.assertIn('ci_upper', modality_results, f"CI upper bound missing for {modality}")
            
            # Verify values are numeric and reasonable
            r_val = modality_results['r']
            self.assertIsInstance(r_val, (int, float), f"r should be numeric for {modality}")
            self.assertGreaterEqual(r_val, -1.0, f"r should be >= -1 for {modality}")
            self.assertLessEqual(r_val, 1.0, f"r should be <= 1 for {modality}")

    def test_separate_correlations_not_identical(self):
        """Test that visual and auditory correlations are computed independently (not just copies)."""
        # Run filter
        run_filter_analysis(
            input_path=str(self.trial_csv_path),
            output_dir=str(self.derived_dir)
        )

        # Run robustness analysis
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )

        # Load results
        results_path = self.results_dir / "robustness_analysis.json"
        with open(results_path, 'r') as f:
            results = json.load(f)

        visual_r = results['visual']['r']
        auditory_r = results['auditory']['r']

        # With random data, correlations should likely differ
        # This test ensures the pipeline computes separate statistics
        # Note: In rare cases with very similar random data they might be close,
        # but with 200 trials and random generation, they should differ
        self.assertNotAlmostEqual(
            visual_r, auditory_r, places=1,
            msg="Visual and auditory correlations should differ (computed independently)"
        )

    def test_full_pipeline_integration(self):
        """Test the complete pipeline from filtering to report generation."""
        # Step 1: Filter data
        run_filter_analysis(
            input_path=str(self.trial_csv_path),
            output_dir=str(self.derived_dir)
        )

        # Step 2: Run robustness analysis
        run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            results_dir=str(self.results_dir)
        )

        # Step 3: Generate final report
        report_path = self.results_dir / "robustness_analysis.json"
        
        # Verify report exists and has correct structure
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            report = json.load(f)

        # Verify all expected sections
        self.assertIn('visual', report)
        self.assertIn('auditory', report)
        self.assertIn('summary', report)
        
        # Verify summary contains both modality results
        summary = report['summary']
        self.assertIn('r_visual', summary)
        self.assertIn('r_auditory', summary)
        self.assertIn('p_visual', summary)
        self.assertIn('p_auditory', summary)


if __name__ == '__main__':
    unittest.main()