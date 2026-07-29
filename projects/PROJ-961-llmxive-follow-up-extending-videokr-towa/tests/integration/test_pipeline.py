"""
Integration tests for the VideoKR threshold detection pipeline.

This module tests the end-to-end flow of the threshold detection logic
(T018) by running `detect_threshold.py` on the annotated data produced by T013.

Prerequisites:
- T013 must have completed successfully, producing `data/processed/annotated_videokr.csv`.
- T020a must have completed successfully, producing `data/processed/bin_config.json`.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.detect_threshold import (
    load_raw_annotated_data,
    load_binned_accuracy_data,
    calculate_effect_size,
    permutation_test,
    bonferroni_correction,
    grid_search_change_point,
    detect_threshold,
    save_results,
    main
)
from utils.config import get_project_root, get_path, ensure_dir


class TestThresholdDetectionIntegration(unittest.TestCase):
    """
    Integration tests for the threshold detection pipeline (T018).
    
    These tests verify that the `detect_threshold.py` script correctly:
    1. Loads the annotated data from T013.
    2. Reads the bin configuration from T020a.
    3. Executes the permutation test and grid search.
    4. Produces a valid results JSON file.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures if real data exists."""
        cls.project_root = get_project_root()
        cls.annotated_data_path = get_path("data/processed/annotated_videokr.csv")
        cls.bin_config_path = get_path("data/processed/bin_config.json")
        cls.output_results_path = get_path("data/processed/threshold_results.json")
        
        # Check if prerequisites exist
        cls.has_annotated_data = cls.annotated_data_path.exists()
        cls.has_bin_config = cls.bin_config_path.exists()

    def test_load_raw_annotated_data(self):
        """Test that the data loader correctly reads the annotated CSV."""
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        df = load_raw_annotated_data(str(self.annotated_data_path))
        
        self.assertIn("chain_length", df.columns, "Missing chain_length column")
        self.assertIn("correctness", df.columns, "Missing correctness column")
        self.assertGreater(len(df), 0, "Dataset is empty")
        
        # Verify data types
        self.assertEqual(df["chain_length"].dtype, "int64", "chain_length should be integer")
        self.assertIn(df["correctness"].dtype, ["int64", "float64"], "correctness should be numeric")

    def test_load_binned_accuracy_data(self):
        """Test that the binned data loader works correctly."""
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        # This function typically aggregates raw data into bins
        # We test that it runs without error on the real data
        df = load_binned_accuracy_data(str(self.annotated_data_path))
        
        self.assertIn("chain_bin", df.columns, "Missing chain_bin column")
        self.assertIn("accuracy", df.columns, "Missing accuracy column")
        self.assertGreater(len(df), 0, "Binned dataset is empty")

    def test_calculate_effect_size(self):
        """Test the effect size calculation logic."""
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        df = load_raw_annotated_data(str(self.annotated_data_path))
        
        # Mock a simple scenario: split by a hypothetical threshold
        # For integration, we just verify the function returns a float
        # In a real scenario, we'd pass specific groups
        group1 = df[df["chain_length"] <= 2]["correctness"]
        group2 = df[df["chain_length"] > 2]["correctness"]
        
        if len(group1) > 0 and len(group2) > 0:
            effect_size = calculate_effect_size(group1, group2)
            self.assertIsInstance(effect_size, float, "Effect size must be a float")
            # Effect size (Cohen's d) is typically between -3 and 3 in practice
            self.assertLessEqual(effect_size, 3.0, "Effect size seems unreasonably large")
            self.assertGreaterEqual(effect_size, -3.0, "Effect size seems unreasonably small")

    def test_permutation_test_basic(self):
        """Test the permutation test engine."""
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        df = load_raw_annotated_data(str(self.annotated_data_path))
        
        # Prepare two groups for testing
        group1 = df[df["chain_length"] == 1]["correctness"].values
        group2 = df[df["chain_length"] == 2]["correctness"].values
        
        if len(group1) < 5 or len(group2) < 5:
            self.skipTest("Insufficient data for permutation test (need >= 5 per group)")
        
        # Run permutation test with a small number of permutations for speed
        p_value = permutation_test(group1, group2, n_permutations=100)
        
        self.assertIsInstance(p_value, float, "P-value must be a float")
        self.assertGreaterEqual(p_value, 0.0, "P-value cannot be negative")
        self.assertLessEqual(p_value, 1.0, "P-value cannot exceed 1.0")

    def test_bonferroni_correction(self):
        """Test the Bonferroni correction logic."""
        raw_p_values = [0.01, 0.05, 0.10]
        corrected = bonferroni_correction(raw_p_values, alpha=0.05)
        
        self.assertEqual(len(corrected), len(raw_p_values), "Length mismatch")
        # Check that corrected values are >= raw values
        for raw, corr in zip(raw_p_values, corrected):
            self.assertGreaterEqual(corr, raw, "Corrected p-value should be >= raw")
        
        # Check specific calculation
        expected = [min(1.0, p * 3) for p in raw_p_values]
        for c, e in zip(corrected, expected):
            self.assertAlmostEqual(c, e, places=5, msg="Bonferroni calculation incorrect")

    def test_grid_search_change_point(self):
        """Test the grid search for optimal change point."""
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        df = load_raw_annotated_data(str(self.annotated_data_path))
        
        # Filter to ensure we have enough data points
        # We need at least some data for each hop count 1, 2, 3
        valid_hops = [1, 2, 3]
        filtered_df = df[df["chain_length"].isin(valid_hops)]
        
        if len(filtered_df) < 20:
            self.skipTest("Insufficient data for grid search (need >= 20 rows)")
        
        # Run grid search with minimal permutations for speed
        best_knot, best_p_value = grid_search_change_point(
            filtered_df["chain_length"].values,
            filtered_df["correctness"].values,
            n_permutations=50  # Reduced for CI speed
        )
        
        self.assertIn(best_knot, [1, 2, 3], "Optimal knot must be a valid hop count")
        self.assertIsInstance(best_p_value, float, "Best p-value must be a float")

    def test_detect_threshold_end_to_end(self):
        """
        Full integration test: Run detect_threshold on real data.
        
        This verifies the complete pipeline:
        1. Load data
        2. Load bin config
        3. Run grid search + permutation
        4. Save results
        """
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        if not self.has_bin_config:
            self.skipTest("bin_config.json not found. Run T020a first.")
        
        # Create a temporary output path to avoid overwriting real results during test
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_output_path = Path(tmp_dir) / "threshold_results_test.json"
            
            # Run the detection logic
            results = detect_threshold(
                str(self.annotated_data_path),
                str(self.bin_config_path),
                str(tmp_output_path),
                n_permutations=100, # Reduced for CI speed
                alpha=0.05
            )
            
            # Verify results structure
            self.assertIn("optimal_knot", results, "Missing optimal_knot")
            self.assertIn("p_value", results, "Missing p_value")
            self.assertIn("p_corrected", results, "Missing p_corrected")
            self.assertIn("is_significant", results, "Missing is_significant")
            self.assertIn("conclusion", results, "Missing conclusion")
            
            # Verify types
            self.assertIsInstance(results["optimal_knot"], int, "optimal_knot must be int")
            self.assertIsInstance(results["p_value"], float, "p_value must be float")
            self.assertIsInstance(results["is_significant"], bool, "is_significant must be bool")
            
            # Verify file was written
            self.assertTrue(tmp_output_path.exists(), "Output file was not written")
            
            # Verify JSON validity
            with open(tmp_output_path, "r") as f:
                loaded_results = json.load(f)
            self.assertEqual(loaded_results, results, "Loaded results mismatch")

    def test_main_function_execution(self):
        """
        Test the main entry point function.
        
        This simulates running the script as `python detect_threshold.py`
        and verifies it exits cleanly and produces output.
        """
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        if not self.has_bin_config:
            self.skipTest("bin_config.json not found. Run T020a first.")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_output_path = Path(tmp_dir) / "main_test_results.json"
            
            # Mock sys.argv to simulate command line execution
            test_args = [
                "detect_threshold.py",
                "--input", str(self.annotated_data_path),
                "--bin_config", str(self.bin_config_path),
                "--output", str(tmp_output_path),
                "--n_permutations", "50"
            ]
            
            with patch("sys.argv", test_args):
                # Capture stdout to ensure no errors
                try:
                    main()
                except SystemExit as e:
                    # main() often calls sys.exit(0)
                    if e.code != 0:
                        self.fail(f"main() exited with code {e.code}")
            
            # Verify output exists
            self.assertTrue(tmp_output_path.exists(), "main() did not produce output file")

    def test_disconnected_graph_handling(self):
        """
        Test that the pipeline handles cases where no significant threshold is found.
        
        This verifies the 'deferred' or 'no_threshold' logic in detect_threshold.
        """
        if not self.has_annotated_data:
            self.skipTest("annotated_videokr.csv not found. Run T013 first.")
        
        # Create a synthetic dataset with NO correlation (random correctness)
        # This should result in a high p-value and a 'no_threshold' conclusion
        df = load_raw_annotated_data(str(self.annotated_data_path))
        
        # Randomize correctness to break any real signal
        df_random = df.copy()
        df_random["correctness"] = np.random.permutation(df["correctness"].values)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_random.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_output_path = Path(tmp_dir) / "random_results.json"
                
                results = detect_threshold(
                    temp_path,
                    str(self.bin_config_path),
                    str(tmp_output_path),
                    n_permutations=50
                )
                
                # With random data, we expect non-significance
                self.assertFalse(
                    results.get("is_significant", False),
                    "Random data should not yield a significant threshold"
                )
                self.assertIn("conclusion", results)
                self.assertIn("no_threshold", results["conclusion"].lower() or "not significant", results["conclusion"].lower())
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    # Import numpy here to avoid dependency issues if not installed
    import numpy as np
    unittest.main()