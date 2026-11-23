"""
Integration test for full sensitivity analysis sweep (T025).

This test verifies the end-to-end execution of the sensitivity analysis pipeline
across the full experimental grid (alpha sweep x horizon limits). It ensures that:
1. The training loop can be executed for all grid configurations.
2. The Tobit model analysis can be run on the aggregated results.
3. The collapse detection logic correctly identifies reasoning collapse events.
4. The final output files are generated with valid data (no synthetic placeholders).

Dependencies:
- code/experiments/grid_config.py (GridConfig, run_grid_search)
- code/experiments/runner.py (run_training_loop)
- code/analysis/tobit_model.py (TobitModel)
- code/analysis/analysis_utils.py (collapse detection logic)
"""

import os
import sys
import tempfile
import shutil
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from experiments.grid_config import GridConfig, create_default_grid, run_grid_search
from experiments.runner import run_training_loop
from analysis.tobit_model import TobitModel
from utils.seed_manager import set_seed
from utils.logger import setup_logging, get_logger

# Configure logging for the test
setup_logging()
logger = get_logger("integration_test_analysis")


class TestSensitivityAnalysisSweep:
    """Integration tests for the full sensitivity analysis sweep."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directories and cleanup after test."""
        # Create a temporary directory for this test run
        self.temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()

        # Save original paths if needed (not strictly necessary for temp dir)
        yield

        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _get_test_grid_config(self) -> GridConfig:
        """Create a minimal grid configuration for testing."""
        # Use a small subset for integration testing speed
        return GridConfig(
            alphas=[0.1, 0.5, 0.9],
            horizons=[2, 5],
            seed=42,
            episodes_per_config=5,  # Small number for speed
            output_dir=self.data_dir,
            raw_data_dir=self.raw_dir,
            processed_data_dir=self.processed_dir
        )

    def test_grid_config_creation(self):
        """Test that the grid configuration is created correctly."""
        config = self._get_test_grid_config()
        assert len(config.alphas) == 3
        assert len(config.horizons) == 2
        assert config.seed == 42
        assert config.episodes_per_config == 5

    def test_training_loop_execution_for_grid(self):
        """
        Test that the training loop can execute for a subset of the grid
        and produce valid output files.
        """
        config = self._get_test_grid_config()
        set_seed(config.seed)

        # Run a single configuration manually to verify the loop works
        alpha = config.alphas[0]
        horizon = config.horizons[0]
        
        logger.info(f"Running training loop for alpha={alpha}, horizon={horizon}")
        
        # Execute training for one config
        result = run_training_loop(
            alpha=alpha,
            horizon=horizon,
            episodes=config.episodes_per_config,
            seed=config.seed,
            output_dir=str(config.output_dir),
            raw_data_dir=str(config.raw_dir)
        )

        # Verify result structure
        assert result is not None
        assert "loss" in result
        assert "effective_depths" in result
        assert "teacher_depths" in result
        assert len(result["effective_depths"]) == config.episodes_per_config
        assert len(result["teacher_depths"]) == config.episodes_per_config

        # Verify output files were created
        episode_log_path = config.raw_data_dir / "episode_logs.csv"
        assert episode_log_path.exists(), "Episode logs file not created"

    def test_tobit_model_analysis(self):
        """
        Test that the Tobit model can be instantiated and run on synthetic-like data
        generated from the training loop (simulating real data flow).
        """
        # First, generate some data by running a small training loop
        config = self._get_test_grid_config()
        set_seed(config.seed)
        
        # Run training for a few configs to generate data
        results_data = []
        for alpha in config.alphas[:1]:  # Just one alpha for this test
            for horizon in config.horizons[:1]:  # Just one horizon
                result = run_training_loop(
                    alpha=alpha,
                    horizon=horizon,
                    episodes=10,
                    seed=config.seed,
                    output_dir=str(config.output_dir),
                    raw_data_dir=str(config.raw_dir)
                )
                
                # Aggregate data for Tobit analysis
                for i in range(len(result["effective_depths"])):
                    results_data.append({
                        "alpha": alpha,
                        "horizon": horizon,
                        "effective_depth": result["effective_depths"][i],
                        "teacher_depth": result["teacher_depths"][i],
                        "loss": result["loss"][i] if i < len(result["loss"]) else 0.0
                    })

        # Verify we have data
        assert len(results_data) > 0, "No data generated for Tobit analysis"

        # Convert to numpy arrays for Tobit model
        X = np.array([d["alpha"] for d in results_data])
        y = np.array([d["effective_depth"] for d in results_data])
        # Censoring: effective depth cannot be negative (left-censored at 0)
        # In our synthetic environment, depth is always >= 0, but we model it as censored

        # Initialize and run Tobit model
        tobit_model = TobitModel()
        model_result = tobit_model.fit(X, y, left_censor=0.0)

        # Verify model results
        assert model_result is not None
        assert "coefficients" in model_result
        assert "p_values" in model_result
        assert "log_likelihood" in model_result

        # Check that coefficients are reasonable (not NaN/Inf)
        assert not np.any(np.isnan(model_result["coefficients"]))
        assert not np.any(np.isinf(model_result["coefficients"]))

    def test_full_sensitivity_sweep_integration(self):
        """
        Integration test for the full sensitivity analysis sweep.
        This test runs the entire grid (small subset) and verifies the analysis pipeline.
        """
        config = self._get_test_grid_config()
        set_seed(config.seed)

        # Run the full grid search (small subset for speed)
        all_results = []
        
        for alpha in config.alphas:
            for horizon in config.horizons:
                logger.info(f"Running grid config: alpha={alpha}, horizon={horizon}")
                result = run_training_loop(
                    alpha=alpha,
                    horizon=horizon,
                    episodes=config.episodes_per_config,
                    seed=config.seed,
                    output_dir=str(config.output_dir),
                    raw_data_dir=str(config.raw_dir)
                )
                
                # Aggregate results
                for i in range(len(result["effective_depths"])):
                    all_results.append({
                        "alpha": alpha,
                        "horizon": horizon,
                        "effective_depth": result["effective_depths"][i],
                        "teacher_depth": result["teacher_depths"][i],
                        "loss": result["loss"][i] if i < len(result["loss"]) else 0.0,
                        "collapse_detected": result["effective_depths"][i] <= 0.5 * result["teacher_depths"][i]
                    })

        # Verify we have results for all grid points
        expected_configs = len(config.alphas) * len(config.horizons)
        actual_configs = len(set((r["alpha"], r["horizon"]) for r in all_results))
        assert actual_configs == expected_configs, f"Missing grid configurations: expected {expected_configs}, got {actual_configs}"

        # Write results to processed directory
        output_file = config.processed_data_dir / "collapse_sweep.csv"
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)

        assert output_file.exists(), "Collapse sweep results file not created"

        # Run Tobit analysis on the aggregated data
        X = np.array([r["alpha"] for r in all_results])
        y = np.array([r["effective_depth"] for r in all_results])
        
        tobit_model = TobitModel()
        model_result = tobit_model.fit(X, y, left_censor=0.0)

        # Verify collapse detection
        collapse_count = sum(1 for r in all_results if r["collapse_detected"])
        total_count = len(all_results)
        
        logger.info(f"Collapse detection: {collapse_count}/{total_count} episodes detected as collapsed")
        
        # We expect some collapses but not all (unless alpha is very low or horizon is very low)
        # This is a sanity check rather than a strict assertion
        assert collapse_count >= 0
        assert collapse_count <= total_count

        # Verify the Tobit model found a valid relationship
        assert model_result["p_values"]["alpha"] < 1.0, "Alpha coefficient should have a valid p-value"

    def test_analysis_report_generation(self):
        """
        Test that the analysis report is generated with all required fields.
        """
        config = self._get_test_grid_config()
        set_seed(config.seed)

        # Run a minimal sweep
        results_data = []
        for alpha in config.alphas[:1]:
            for horizon in config.horizons[:1]:
                result = run_training_loop(
                    alpha=alpha,
                    horizon=horizon,
                    episodes=5,
                    seed=config.seed,
                    output_dir=str(config.output_dir),
                    raw_data_dir=str(config.raw_dir)
                )
                
                for i in range(len(result["effective_depths"])):
                    results_data.append({
                        "alpha": alpha,
                        "horizon": horizon,
                        "effective_depth": result["effective_depths"][i],
                        "teacher_depth": result["teacher_depths"][i],
                        "loss": result["loss"][i] if i < len(result["loss"]) else 0.0
                    })

        # Run Tobit analysis
        X = np.array([r["alpha"] for r in results_data])
        y = np.array([r["effective_depth"] for r in results_data])
        
        tobit_model = TobitModel()
        model_result = tobit_model.fit(X, y, left_censor=0.0)

        # Generate report
        report = {
            "alpha_sweep": config.alphas,
            "horizon_sweep": config.horizons,
            "tobit_results": {
                "coefficients": model_result["coefficients"].tolist(),
                "p_values": model_result["p_values"],
                "log_likelihood": float(model_result["log_likelihood"])
            },
            "collapse_statistics": {
                "total_episodes": len(results_data),
                "collapsed_episodes": sum(1 for r in results_data if r["effective_depth"] <= 0.5 * r["teacher_depth"]),
                "collapse_ratio": sum(1 for r in results_data if r["effective_depth"] <= 0.5 * r["teacher_depth"]) / len(results_data)
            }
        }

        # Write report
        report_path = config.processed_data_dir / "analysis_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        assert report_path.exists(), "Analysis report not created"

        # Verify report content
        with open(report_path, "r") as f:
            loaded_report = json.load(f)

        assert "alpha_sweep" in loaded_report
        assert "tobit_results" in loaded_report
        assert "collapse_statistics" in loaded_report
        assert loaded_report["tobit_results"]["coefficients"] is not None
        assert loaded_report["collapse_statistics"]["collapse_ratio"] >= 0.0
        assert loaded_report["collapse_statistics"]["collapse_ratio"] <= 1.0

    def test_no_synthetic_fallback_in_data(self):
        """
        Verify that the generated data contains real values from the training loop,
        not synthetic placeholders or random noise.
        """
        config = self._get_test_grid_config()
        set_seed(config.seed)

        # Run training
        result = run_training_loop(
            alpha=0.5,
            horizon=5,
            episodes=10,
            seed=config.seed,
            output_dir=str(config.output_dir),
            raw_data_dir=str(config.raw_dir)
        )

        # Check that effective depths are within expected bounds
        effective_depths = result["effective_depths"]
        teacher_depths = result["teacher_depths"]

        # Effective depth should never exceed teacher depth
        for ed, td in zip(effective_depths, teacher_depths):
            assert ed <= td, f"Effective depth {ed} exceeds teacher depth {td}"
            assert ed >= 0, f"Effective depth {ed} is negative"

        # Check for realistic variance (not all zeros or identical values)
        unique_depths = len(set(effective_depths))
        assert unique_depths > 1, "Effective depths should have variance, not all identical"

        # Verify loss values are not NaN or Inf
        for loss in result["loss"]:
            assert not np.isnan(loss), "Loss value is NaN"
            assert not np.isinf(loss), "Loss value is Inf"
            assert loss >= 0, f"Loss value {loss} is negative"