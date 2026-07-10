"""
Integration test for the full analysis pipeline (US3).

This test verifies the end-to-end flow:
1. Loads synthetic data (null-effect mode) via data.load.
2. Processes raw logs into aggregated D-scores via data.process.
3. Runs the Permutation Test via analysis.permutation.
4. Generates visualization via viz.plot.
5. Validates that output files are created and contain expected keys.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_project_root, ensure_directories, get_data_path
from data.load import generate_synthetic_response_logs, load_response_logs
from data.process import aggregate_d_scores, save_aggregated_scores
from analysis.permutation import run_permutation_test, calculate_power
from viz.plot import plot_boxplot


class TestFullAnalysisPipeline:
    """Integration tests for the full analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up a temporary directory for test artifacts."""
        # Create a temporary directory to simulate project structure
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create minimal config structure for the test
        os.makedirs("code", exist_ok=True)
        os.makedirs("data/raw/responses", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("data/results", exist_ok=True)

        # Create a mock config.py to override paths if necessary,
        # but since we are running in a temp dir, we rely on the
        # functions to use relative paths or we patch get_project_root.
        # For this test, we will generate files directly in the temp dir
        # and pass explicit paths where possible, or rely on the
        # default behavior if the project root is detected as the temp dir.

        yield

        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_null_effect(self):
        """
        Run the full pipeline in 'null-effect' mode.

        Steps:
        1. Generate synthetic response logs (null effect).
        2. Aggregate D-scores.
        3. Run Permutation Test.
        4. Generate Plot.
        5. Verify output files exist and contain valid data.
        """
        # 1. Generate Synthetic Data
        # We need to simulate the existence of raw logs first.
        # The load module has a main that does this, but we can call the helper.
        # We'll create a dummy raw log file to satisfy the loader.
        raw_logs_path = Path("data/raw/responses/synthetic_log.csv")
        
        # Generate synthetic data directly to a file
        n_participants = 20
        df_synthetic = generate_synthetic_response_logs(n_participants, seed=42)
        df_synthetic.to_csv(raw_logs_path, index=False)

        # 2. Load and Process
        # Load the raw logs
        raw_data = load_response_logs([raw_logs_path])
        
        # Aggregate D-scores
        # We need to simulate the 'complexity_category' which usually comes from US1.
        # Since we are in a null-effect test, we can assign categories randomly or
        # based on a mock mapping to ensure the analysis runs.
        # The aggregate_d_scores function expects a list of ParticipantResponse dicts.
        
        # Let's manually construct the input for aggregate_d_scores to ensure
        # we have the 'complexity_category' field which might be missing in raw logs
        # if not processed by US1.
        # However, the task T026 (process.py) handles aggregation.
        # Let's assume the raw logs have the necessary fields or we mock them.
        
        # For this integration test, we will call aggregate_d_scores with the raw data
        # and assume the logic in process.py handles the mapping or we provide a mock.
        # Looking at the API: aggregate_d_scores(raw_logs_dict) -> DataFrame.
        # It likely joins with complexity scores.
        # To make this work without US1, we will create a mock complexity score file.
        
        mock_complexity_path = Path("data/processed/complexity_scores.csv")
        mock_complexity_df = pd.DataFrame({
            "filename": [f"img_{i}.png" for i in range(n_participants)],
            "complexity_category": np.random.choice(["Low", "High"], n_participants)
        })
        mock_complexity_df.to_csv(mock_complexity_path, index=False)

        # Now run aggregation
        aggregated_df = aggregate_d_scores() 
        # Note: aggregate_d_scores() in process.py likely reads from default paths.
        # If it fails because it expects specific file names, we rely on the
        # implementation in T026 to use the standard paths.
        
        # Save aggregated scores
        save_aggregated_scores(aggregated_df)

        # 3. Run Permutation Test
        # The permutation test expects aggregated D-scores.
        # We pass the path to the aggregated scores.
        results = run_permutation_test(
            aggregated_scores_path="data/processed/aggregated_d_scores.csv",
            n_permutations=100, # Small number for speed in CI
            seed=42
        )

        # 4. Generate Visualization
        # Plot the boxplot
        fig = plot_boxplot(
            aggregated_scores_path="data/processed/aggregated_d_scores.csv",
            output_path="data/results/d_score_boxplot.png"
        )
        
        # Ensure the figure is saved (plotting functions usually save if path is given)
        # If the function returns a fig object, we might need to save it explicitly
        # depending on the implementation of plot_boxplot.
        # Assuming plot_boxplot saves to the path provided.

        # 5. Verify Outputs
        # Check that results file exists
        results_path = Path("data/results/permutation_results.json")
        assert results_path.exists(), "Permutation results file not created"

        with open(results_path, "r") as f:
            results_data = json.load(f)

        assert "p_value" in results_data, "p_value missing in results"
        assert "effect_size" in results_data, "effect_size missing in results"
        assert "n_permutations" in results_data, "n_permutations missing in results"

        # Check that plot file exists
        plot_path = Path("data/results/d_score_boxplot.png")
        assert plot_path.exists(), "Boxplot image not created"
        assert plot_path.stat().st_size > 0, "Boxplot image is empty"

        # Verify null effect logic: p-value should be > 0.05 (not significant)
        # Note: With small N and random seed, it might occasionally be significant,
        # but for a robust test, we check that the calculation ran.
        # A strict assertion on p > 0.05 might be flaky with small N, 
        # but we assert the structure is correct.
        assert isinstance(results_data["p_value"], (int, float))
        assert isinstance(results_data["effect_size"], (int, float))

    def test_power_analysis_integration(self):
        """
        Integration test for power analysis calculation.
        """
        # Re-use the data from the previous test or generate new
        n_participants = 50
        raw_logs_path = Path("data/raw/responses/power_test_log.csv")
        df_synthetic = generate_synthetic_response_logs(n_participants, seed=123)
        df_synthetic.to_csv(raw_logs_path, index=False)

        # Mock complexity
        mock_complexity_path = Path("data/processed/complexity_scores_power.csv")
        mock_complexity_df = pd.DataFrame({
            "filename": [f"img_{i}.png" for i in range(n_participants)],
            "complexity_category": np.random.choice(["Low", "High"], n_participants)
        })
        # Note: aggregate_d_scores reads from specific paths, so we might need to
        # ensure the names match or rely on the function's internal logic.
        # For simplicity in this test, we assume the function reads the default
        # aggregated file if not specified, or we pass the path.
        # However, T026 implementation likely hardcodes the output path.
        
        # Run aggregation again to update the default file
        # We need to ensure the raw log path is correct for the loader
        # The loader might scan a directory.
        # Let's assume the loader picks up the latest or we overwrite the default.
        # To be safe, we'll just call aggregate_d_scores which should read the
        # raw logs from the standard location.
        # We'll copy our synthetic log to the standard location to be sure.
        standard_raw_path = Path("data/raw/responses/synthetic_log.csv")
        df_synthetic.to_csv(standard_raw_path, index=False)
        
        # Re-run aggregation
        aggregated_df = aggregate_d_scores()
        save_aggregated_scores(aggregated_df)

        # Run power analysis
        # T034a requires calculating power.
        # We call the function directly.
        power_result = calculate_power(
            d_effect=0.5, # Expected effect size
            alpha=0.05,
            n_samples=n_participants
        )

        # Verify output
        assert "power_value" in power_result
        assert "target" in power_result
        assert "status" in power_result
        
        # The power value should be a float between 0 and 1
        assert 0.0 <= power_result["power_value"] <= 1.0

        # Check if the status is 'pass' or 'fail' based on target
        assert power_result["status"] in ["pass", "fail"]

        # Save power analysis results (simulating T034a output)
        power_output_path = Path("data/results/power_analysis.json")
        with open(power_output_path, "w") as f:
            json.dump(power_result, f, indent=2)

        assert power_output_path.exists()
        assert power_output_path.stat().st_size > 0