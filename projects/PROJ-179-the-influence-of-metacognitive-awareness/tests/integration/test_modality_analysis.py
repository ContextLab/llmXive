"""
Integration test for modality-specific correlation analysis (T025).
This test verifies that the robustness analysis pipeline correctly:
1. Filters data by stimulus modality (visual vs auditory).
2. Computes hold-out correlation metrics for each modality.
3. Performs bootstrap resampling for confidence intervals.
4. Generates the robustness_analysis.json report.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.filter import run_filter_analysis
from code.src.analysis.robustness import run_robustness_analysis
from code.src.report.generate import generate_robustness_analysis_report


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up temporary directories and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.derived_dir = self.data_dir / "derived"
        self.results_dir = self.data_dir / "results"
        
        self.derived_dir.mkdir(parents=True)
        self.results_dir.mkdir(parents=True)
        
        # Create a mock trial_data.csv with required columns
        self.trial_data_path = self.derived_dir / "trial_data.csv"
        self._create_mock_trial_data()

    def _create_mock_trial_data(self):
        """Create a mock trial_data.csv with realistic structure."""
        import pandas as pd
        import numpy as np

        np.random.seed(42)
        n_trials = 200

        data = {
            'participant_id': ['P001'] * n_trials,
            'trial_id': range(n_trials),
            'stimulus_modality': np.random.choice(['visual', 'auditory'], n_trials),
            'source_label': np.random.choice(['true', 'false'], n_trials),
            'participant_response': np.random.choice(['true', 'false'], n_trials),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_trials),
            'accuracy': (np.random.random(n_trials) > 0.5).astype(int)
        }

        df = pd.DataFrame(data)
        df.to_csv(self.trial_data_path, index=False)

    def _load_results(self, filename):
        """Load JSON results file."""
        filepath = self.results_dir / filename
        with open(filepath, 'r') as f:
            return json.load(f)

    def test_filter_analysis_creates_modality_files(self):
        """Test that filter analysis creates visual and auditory trial files."""
        # Run filter analysis
        run_filter_analysis(
            trial_data_path=self.trial_data_path,
            output_dir=self.derived_dir
        )

        # Verify output files exist
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"

        self.assertTrue(visual_path.exists(), "visual_trials.csv should be created")
        self.assertTrue(auditory_path.exists(), "auditory_trials.csv should be created")

        # Verify file contents
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)

        self.assertTrue(all(visual_df['stimulus_modality'] == 'visual'))
        self.assertTrue(all(auditory_df['stimulus_modality'] == 'auditory'))

    def test_robustness_analysis_computes_metrics(self):
        """Test that robustness analysis computes correlation metrics for each modality."""
        # First run filter to create modality-specific files
        run_filter_analysis(
            trial_data_path=self.trial_data_path,
            output_dir=self.derived_dir
        )

        # Run robustness analysis
        run_robustness_analysis(
            derived_dir=self.derived_dir,
            results_dir=self.results_dir,
            bootstrap_count=50,  # Small count for testing speed
            seed=42
        )

        # Verify robustness results file exists
        robustness_file = self.results_dir / "robustness_analysis.json"
        self.assertTrue(robustness_file.exists(), "robustness_analysis.json should be created")

        # Load and verify structure
        results = self._load_results("robustness_analysis.json")

        self.assertIn("visual", results)
        self.assertIn("auditory", results)

        # Check visual results structure
        visual_results = results["visual"]
        self.assertIn("r", visual_results)
        self.assertIn("p_value", visual_results)
        self.assertIn("ci_lower", visual_results)
        self.assertIn("ci_upper", visual_results)
        self.assertIn("n_trials", visual_results)

        # Check auditory results structure
        auditory_results = results["auditory"]
        self.assertIn("r", auditory_results)
        self.assertIn("p_value", auditory_results)
        self.assertIn("ci_lower", auditory_results)
        self.assertIn("ci_upper", auditory_results)
        self.assertIn("n_trials", auditory_results)

    def test_robustness_report_generation(self):
        """Test that the robustness report is generated with corrected p-values."""
        # Run full pipeline
        run_filter_analysis(
            trial_data_path=self.trial_data_path,
            output_dir=self.derived_dir
        )

        run_robustness_analysis(
            derived_dir=self.derived_dir,
            results_dir=self.results_dir,
            bootstrap_count=50,
            seed=42
        )

        # Generate report
        generate_robustness_analysis_report(
            results_dir=self.results_dir,
            output_path=self.results_dir / "robustness_analysis_report.json"
        )

        # Verify report exists and has correct structure
        report_path = self.results_dir / "robustness_analysis_report.json"
        self.assertTrue(report_path.exists())

        report = self._load_results("robustness_analysis_report.json")

        self.assertIn("visual", report)
        self.assertIn("auditory", report)
        self.assertIn("multiple_comparison_correction", report)

        # Verify correction method is present
        self.assertIn("method", report["multiple_comparison_correction"])
        self.assertIn("corrected_p_values", report["multiple_comparison_correction"])

    def test_disjoint_trial_validation(self):
        """Test that visual and auditory trials are disjoint."""
        run_filter_analysis(
            trial_data_path=self.trial_data_path,
            output_dir=self.derived_dir
        )

        visual_df = pd.read_csv(self.derived_dir / "visual_trials.csv")
        auditory_df = pd.read_csv(self.derived_dir / "auditory_trials.csv")

        visual_trials = set(visual_df['trial_id'])
        auditory_trials = set(auditory_df['trial_id'])

        # Intersection should be empty
        self.assertEqual(len(visual_trials & auditory_trials), 0)

        # Union should equal original
        original_df = pd.read_csv(self.trial_data_path)
        original_trials = set(original_df['trial_id'])

        self.assertEqual(visual_trials | auditory_trials, original_trials)

    def test_robustness_with_empty_modality(self):
        """Test handling when one modality has no trials."""
        # Create data with only visual trials
        import pandas as pd
        import numpy as np

        np.random.seed(42)
        n_trials = 50

        data = {
            'participant_id': ['P001'] * n_trials,
            'trial_id': range(n_trials),
            'stimulus_modality': ['visual'] * n_trials,
            'source_label': np.random.choice(['true', 'false'], n_trials),
            'participant_response': np.random.choice(['true', 'false'], n_trials),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_trials),
            'accuracy': (np.random.random(n_trials) > 0.5).astype(int)
        }

        df = pd.DataFrame(data)
        df.to_csv(self.trial_data_path, index=False)

        run_filter_analysis(
            trial_data_path=self.trial_data_path,
            output_dir=self.derived_dir
        )

        # Robustness analysis should handle empty auditory data gracefully
        run_robustness_analysis(
            derived_dir=self.derived_dir,
            results_dir=self.results_dir,
            bootstrap_count=10,
            seed=42
        )

        results = self._load_results("robustness_analysis.json")

        # Visual should have results
        self.assertIn("r", results["visual"])
        
        # Auditory should indicate no data
        self.assertTrue(results["auditory"].get("no_data", False))

if __name__ == '__main__':
    unittest.main()