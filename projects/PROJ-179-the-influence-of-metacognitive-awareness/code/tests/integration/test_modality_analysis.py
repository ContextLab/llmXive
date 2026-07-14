"""
Integration test for modality-specific correlation analysis (User Story 3).
This test verifies that the pipeline correctly splits data by modality,
runs the correlation analysis on each subset, and produces valid results.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.filter import run_filter_analysis
from code.src.analysis.robustness import run_robustness_analysis
from code.src.report.generate import generate_robustness_analysis_report, write_report
from code.config.env_config import load_config, AppConfig


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for the modality-specific correlation pipeline."""

    def setUp(self):
        """Set up temporary directories and mock data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        
        # Create necessary subdirectories
        self.derived_dir = self.base_dir / "data" / "derived"
        self.results_dir = self.base_dir / "data" / "results"
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Create a mock trial_data.csv with both visual and auditory modalities
        self.trial_data_path = self.derived_dir / "trial_data.csv"
        self._create_mock_trial_data()

        # Create a mock config for the test
        self.config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir),
                "results": str(self.results_dir)
            },
            "analysis": {
                "bootstrap_count": 100,  # Reduced for faster testing
                "train_split": 0.7
            }
        }
        
        # Write config to a temporary file
        self.config_path = self.base_dir / "config"
        self.config_path.mkdir(parents=True, exist_ok=True)
        with open(self.config_path / "test_config.json", "w") as f:
            json.dump(self.config, f)

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir.cleanup()

    def _create_mock_trial_data(self):
        """Create a realistic mock trial dataset for testing."""
        import pandas as pd
        import numpy as np

        # Set seed for reproducibility
        np.random.seed(42)
        
        n_participants = 20
        n_trials_per_participant = 100
        
        data = []
        trial_id = 0
        
        for participant_id in range(1, n_participants + 1):
            # Vary parameters per participant to create realistic variance
            base_d_prime = np.random.uniform(0.5, 2.5)
            base_meta_auc = np.random.uniform(0.55, 0.85)
            
            for _ in range(n_trials_per_participant):
                # Randomly assign modality (50/50 split)
                modality = np.random.choice(["visual", "auditory"])
                
                # Generate realistic behavioral data
                # Source label: 1 = correct source, 0 = incorrect source
                source_label = np.random.choice([0, 1], p=[0.3, 0.7])
                
                # Participant response based on source and some noise
                if source_label == 1:
                    # High probability of correct response when source is correct
                    participant_response = 1 if np.random.random() > 0.2 else 0
                else:
                    # Lower probability when source is incorrect
                    participant_response = 1 if np.random.random() > 0.6 else 0
                
                # Confidence rating (1-4 scale) correlated with accuracy
                accuracy = 1 if participant_response == source_label else 0
                if accuracy:
                    confidence = np.random.choice([3, 4], p=[0.3, 0.7])
                else:
                    confidence = np.random.choice([1, 2], p=[0.6, 0.4])
                
                data.append({
                    "participant_id": participant_id,
                    "trial_id": trial_id,
                    "stimulus_modality": modality,
                    "source_label": source_label,
                    "participant_response": participant_response,
                    "confidence_rating": confidence
                })
                trial_id += 1
        
        df = pd.DataFrame(data)
        df.to_csv(self.trial_data_path, index=False)

    def test_filter_analysis_creates_modality_files(self):
        """Test that filter analysis correctly splits data by modality."""
        # Run the filter analysis
        run_filter_analysis(
            trial_data_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Check that both modality-specific files were created
        visual_path = self.derived_dir / "visual_trials.csv"
        auditory_path = self.derived_dir / "auditory_trials.csv"
        
        self.assertTrue(visual_path.exists(), "Visual trials file not created")
        self.assertTrue(auditory_path.exists(), "Auditory trials file not created")
        
        # Verify content
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)
        
        self.assertEqual(len(visual_df[visual_df["stimulus_modality"] == "visual"]), len(visual_df))
        self.assertEqual(len(auditory_df[auditory_df["stimulus_modality"] == "auditory"]), len(auditory_df))
        
        # Check that total rows match original
        original_df = pd.read_csv(self.trial_data_path)
        self.assertEqual(len(original_df), len(visual_df) + len(auditory_df))

    def test_robustness_analysis_produces_results(self):
        """Test that robustness analysis runs and produces valid results."""
        # First run filter to create modality files
        run_filter_analysis(
            trial_data_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Run robustness analysis
        robustness_results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            bootstrap_count=50,  # Small count for testing
            train_split=0.7
        )
        
        # Check that results are valid
        self.assertIsNotNone(robustness_results)
        self.assertIn("visual", robustness_results)
        self.assertIn("auditory", robustness_results)
        
        # Check structure of results
        for modality, results in robustness_results.items():
            self.assertIn("r", results)
            self.assertIn("p", results)
            self.assertIn("ci_lower", results)
            self.assertIn("ci_upper", results)
            self.assertIn("n_trials", results)
            
            # Check that values are reasonable
            self.assertIsInstance(results["r"], float)
            self.assertIsInstance(results["p"], float)
            self.assertGreaterEqual(results["ci_lower"], -1.0)
            self.assertLessEqual(results["ci_upper"], 1.0)
            self.assertGreater(results["n_trials"], 0)

    def test_report_generation_with_correction(self):
        """Test that the report generation includes multiple comparison correction."""
        # Run the full pipeline
        run_filter_analysis(
            trial_data_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        robustness_results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            bootstrap_count=50,
            train_split=0.7
        )
        
        # Generate report
        report = generate_robustness_analysis_report(
            robustness_results=robustness_results,
            correction_method="bonferroni"
        )
        
        # Verify report structure
        self.assertIn("modality_results", report)
        self.assertIn("correction_method", report)
        self.assertIn("corrected_p_values", report)
        
        # Check that both modalities are in the report
        self.assertIn("visual", report["modality_results"])
        self.assertIn("auditory", report["modality_results"])
        
        # Verify corrected p-values are present
        self.assertIn("visual", report["corrected_p_values"])
        self.assertIn("auditory", report["corrected_p_values"])
        
        # Write report to file
        report_path = self.results_dir / "robustness_analysis.json"
        write_report(report, str(report_path))
        
        # Verify file was written and can be loaded
        self.assertTrue(report_path.exists())
        with open(report_path, "r") as f:
            loaded_report = json.load(f)
        
        self.assertEqual(report, loaded_report)

    def test_end_to_end_pipeline(self):
        """Test the complete end-to-end pipeline for modality analysis."""
        # Step 1: Filter data
        run_filter_analysis(
            trial_data_path=str(self.trial_data_path),
            derived_dir=str(self.derived_dir)
        )
        
        # Step 2: Run robustness analysis
        robustness_results = run_robustness_analysis(
            derived_dir=str(self.derived_dir),
            bootstrap_count=50,
            train_split=0.7
        )
        
        # Step 3: Generate report
        report = generate_robustness_analysis_report(
            robustness_results=robustness_results,
            correction_method="bonferroni"
        )
        
        # Step 4: Write report
        report_path = self.results_dir / "robustness_analysis.json"
        write_report(report, str(report_path))
        
        # Verify all expected files exist
        expected_files = [
            self.derived_dir / "visual_trials.csv",
            self.derived_dir / "auditory_trials.csv",
            report_path
        ]
        
        for file_path in expected_files:
            self.assertTrue(file_path.exists(), f"Expected file not created: {file_path}")
        
        # Verify report content
        with open(report_path, "r") as f:
            final_report = json.load(f)
        
        # Check that the report contains all required information
        self.assertIn("modality_results", final_report)
        self.assertIn("correction_method", final_report)
        self.assertIn("corrected_p_values", final_report)
        self.assertIn("summary", final_report)
        
        # Verify summary contains both modalities
        self.assertIn("visual", final_report["summary"])
        self.assertIn("auditory", final_report["summary"])


if __name__ == "__main__":
    unittest.main()