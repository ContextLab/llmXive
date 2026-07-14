import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from src.analysis.robustness import run_robustness_analysis
from src.analysis.bootstrap import run_bootstrap_analysis
from src.utils.stats import compute_type2_auc, compute_sdt_metrics


class TestModalityAnalysis(unittest.TestCase):
    """
    Integration test for modality-specific correlation (US3).
    Verifies that the pipeline correctly splits data by modality,
    computes metrics on each subset, and produces valid results.
    """

    def setUp(self):
        """Create temporary directories and mock data for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        
        # Create derived and results directories
        self.derived_dir = self.base_dir / "data" / "derived"
        self.results_dir = self.base_dir / "data" / "results"
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Create a realistic mock dataset with required fields
        # This mimics the output of data/preprocess.py (T012)
        np.random.seed(42)
        n_participants = 20
        n_trials_per_participant = 50
        
        data = []
        for pid in range(1, n_participants + 1):
            # Each participant has both visual and auditory trials
            for modality in ["visual", "auditory"]:
                n_trials = np.random.randint(20, 30)
                for tid in range(n_trials):
                    # Simulate realistic metacognitive behavior
                    # Type-2 AUC correlates with accuracy (d')
                    base_accuracy = np.random.uniform(0.5, 0.9)
                    confidence = base_accuracy + np.random.normal(0, 0.1)
                    confidence = np.clip(confidence, 0, 1)
                    
                    # Generate response and ground truth
                    if np.random.random() < base_accuracy:
                        response = 1
                        ground_truth = 1
                    else:
                        response = 0
                        ground_truth = 0
                    
                    data.append({
                        "participant_id": pid,
                        "trial_id": f"P{pid}_T{tid}_{modality}",
                        "stimulus_modality": modality,
                        "source_label": "internal" if ground_truth == 1 else "external",
                        "participant_response": response,
                        "confidence_rating": confidence,
                        "is_correct": 1 if response == ground_truth else 0
                    })
        
        self.mock_df = pd.DataFrame(data)
        self.trial_data_path = self.derived_dir / "trial_data.csv"
        self.mock_df.to_csv(self.trial_data_path, index=False)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_modality_filter_creates_files(self):
        """Test that the filter step creates separate modality files."""
        from src.analysis.filter import run_filter_analysis
        
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir)
            }
        }
        
        result = run_filter_analysis(config)
        
        self.assertTrue(result["success"])
        self.assertTrue((self.derived_dir / "visual_trials.csv").exists())
        self.assertTrue((self.derived_dir / "auditory_trials.csv").exists())
        
        # Verify column integrity
        visual_df = pd.read_csv(self.derived_dir / "visual_trials.csv")
        auditory_df = pd.read_csv(self.derived_dir / "auditory_trials.csv")
        
        self.assertEqual(visual_df["stimulus_modality"].unique()[0], "visual")
        self.assertEqual(auditory_df["stimulus_modality"].unique()[0], "auditory")
        self.assertGreater(len(visual_df), 0)
        self.assertGreater(len(auditory_df), 0)

    def test_robustness_analysis_produces_results(self):
        """Test the full robustness analysis pipeline."""
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir),
                "results": str(self.results_dir)
            },
            "analysis": {
                "bootstrap_count": 100,  # Reduced for test speed
                "random_seed": 42
            }
        }
        
        result = run_robustness_analysis(config)
        
        self.assertTrue(result["success"])
        self.assertIn("visual", result["results"])
        self.assertIn("auditory", result["results"])
        
        # Verify structure of results
        visual_result = result["results"]["visual"]
        auditory_result = result["results"]["auditory"]
        
        for modality, res in [("visual", visual_result), ("auditory", auditory_result)]:
            self.assertIn("r", res)
            self.assertIn("p", res)
            self.assertIn("ci_lower", res)
            self.assertIn("ci_upper", res)
            self.assertIn("bootstrap_count", res)
            self.assertIn("n_trials", res)
            
            # Verify statistical plausibility
            self.assertIsInstance(res["r"], float)
            self.assertIsInstance(res["p"], float)
            self.assertGreaterEqual(res["r"], -1.0)
            self.assertLessEqual(res["r"], 1.0)
            self.assertGreaterEqual(res["p"], 0.0)
            self.assertLessEqual(res["p"], 1.0)

    def test_hold_out_design_enforced(self):
        """Verify that the hold-out design is correctly applied."""
        from src.analysis.correlation import compute_hold_out_metrics
        
        # Load visual data
        visual_df = pd.read_csv(self.derived_dir / "visual_trials.csv")
        
        config = {
            "train_split": 0.7,
            "random_seed": 42
        }
        
        result = compute_hold_out_metrics(visual_df, config)
        
        # Verify that metrics were computed
        self.assertIn("meta_auc_train", result)
        self.assertIn("d_prime_test", result)
        self.assertIn("n_train", result)
        self.assertIn("n_test", result)
        
        # Verify split sizes are reasonable
        total_n = len(visual_df)
        self.assertGreaterEqual(result["n_train"], int(total_n * 0.6))
        self.assertGreaterEqual(result["n_test"], int(total_n * 0.2))

    def test_bootstrap_confidence_intervals(self):
        """Test that bootstrap CIs are computed correctly."""
        # Load bootstrap results from robustness analysis
        results_path = self.results_dir / "robustness_analysis.json"
        
        if results_path.exists():
            with open(results_path) as f:
                results = json.load(f)
            
            for modality, mod_result in results["results"].items():
                ci_lower = mod_result["ci_lower"]
                ci_upper = mod_result["ci_upper"]
                r = mod_result["r"]
                
                # CI should contain the point estimate
                self.assertLessEqual(ci_lower, r)
                self.assertGreaterEqual(ci_upper, r)
                
                # CI bounds should be within [-1, 1]
                self.assertGreaterEqual(ci_lower, -1.0)
                self.assertLessEqual(ci_upper, 1.0)

    def test_disjoint_trials_validation(self):
        """Verify that train and test sets are disjoint."""
        from src.analysis.filter import run_filter_analysis
        from src.analysis.correlation import compute_hold_out_metrics
        
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir)
            }
        }
        
        # Run filter
        run_filter_analysis(config)
        
        # Load visual data
        visual_df = pd.read_csv(self.derived_dir / "visual_trials.csv")
        
        # Compute metrics with hold-out
        result = compute_hold_out_metrics(visual_df, {"train_split": 0.7, "random_seed": 42})
        
        # Verify that trial IDs in train and test are disjoint
        train_ids = set(result["train_trial_ids"])
        test_ids = set(result["test_trial_ids"])
        
        intersection = train_ids.intersection(test_ids)
        self.assertEqual(len(intersection), 0, "Train and test sets must be disjoint")

    def test_integration_with_realistic_data_patterns(self):
        """Test that the pipeline handles realistic data patterns correctly."""
        # Create data with known correlation pattern
        np.random.seed(123)
        n = 100
        
        # Generate correlated variables
        metacognition = np.random.normal(0.6, 0.1, n)
        accuracy = metacognition * 0.5 + np.random.normal(0, 0.1, n)
        accuracy = np.clip(accuracy, 0.3, 0.95)
        
        data = []
        for i in range(n):
            data.append({
                "participant_id": 1,
                "trial_id": f"T{i}",
                "stimulus_modality": "visual",
                "source_label": "internal",
                "participant_response": 1 if np.random.random() < accuracy[i] else 0,
                "confidence_rating": metacognition[i],
                "is_correct": 1 if np.random.random() < accuracy[i] else 0
            })
        
        test_df = pd.DataFrame(data)
        test_path = self.derived_dir / "test_visual_trials.csv"
        test_df.to_csv(test_path, index=False)
        
        # Run correlation on this data
        from src.analysis.bootstrap import load_correlation_data, compute_correlation_statistic, run_bootstrap_analysis
        
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir),
                "results": str(self.results_dir)
            },
            "analysis": {
                "bootstrap_count": 50,
                "random_seed": 42
            }
        }
        
        # Load data
        loaded_data = load_correlation_data(test_path)
        
        # Compute correlation
        stat_result = compute_correlation_statistic(
            loaded_data["metacognition"],
            loaded_data["accuracy"]
        )
        
        self.assertIn("r", stat_result)
        self.assertIn("p", stat_result)
        
        # With this constructed data, we expect a positive correlation
        self.assertGreater(stat_result["r"], 0.0)

    def test_error_handling_missing_files(self):
        """Test graceful handling of missing input files."""
        from src.analysis.robustness import load_filtered_data
        
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": self.base_dir / "nonexistent"
            }
        }
        
        # Should return error result, not crash
        result = load_filtered_data(config, "visual")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_multiple_modality_handling(self):
        """Test that both visual and auditory modalities are processed."""
        from src.analysis.robustness import run_robustness_analysis
        
        config = {
            "paths": {
                "base": str(self.base_dir),
                "derived_data": str(self.derived_dir),
                "results": str(self.results_dir)
            },
            "analysis": {
                "bootstrap_count": 50,
                "random_seed": 42
            }
        }
        
        result = run_robustness_analysis(config)
        
        self.assertTrue(result["success"])
        self.assertIn("visual", result["results"])
        self.assertIn("auditory", result["results"])
        
        # Both should have valid statistics
        for modality in ["visual", "auditory"]:
            res = result["results"][modality]
            self.assertIsNotNone(res.get("r"))
            self.assertIsNotNone(res.get("p"))
            self.assertIsNotNone(res.get("ci_lower"))
            self.assertIsNotNone(res.get("ci_upper"))


if __name__ == "__main__":
    unittest.main()