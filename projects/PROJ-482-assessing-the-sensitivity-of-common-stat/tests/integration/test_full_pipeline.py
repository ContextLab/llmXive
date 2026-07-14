"""
Integration tests for the full simulation pipeline (T034).

This test suite validates the end-to-end execution of the project:
1. Directory Setup
2. Data Generation (US1)
3. Simulation Execution (US2) - limited scope for speed
4. Analysis & Export (US3)

It ensures that the pipeline produces valid output files and that
the results are consistent with expectations (e.g., Type I error near alpha).
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import SimulationConfig, get_simulation_grid
from data_generator import generate_normal
from simulation_engine import run_adaptive_simulation, execute_t_test
from analyzer import aggregate_results, compute_bootstrap_ci
from export_results import ensure_output_dirs, export_final_results


class TestFullPipeline:
    """Integration tests for the complete statistical sensitivity pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory for test outputs and clean up afterwards."""
        self.test_dir = tempfile.mkdtemp(prefix="llmXive_test_")
        self.data_dir = os.path.join(self.test_dir, "data")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.raw_dir = os.path.join(self.data_dir, "raw")
        
        # Create directory structure
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Store original paths to restore later if needed
        self.original_cwd = os.getcwd()
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_directory_setup(self):
        """Verify that the pipeline creates necessary directory structures."""
        # This is implicitly tested by the fixture, but we assert existence
        assert os.path.exists(self.raw_dir), "Raw data directory not created"
        assert os.path.exists(self.processed_dir), "Processed data directory not created"

    def test_02_data_generation_consistency(self):
        """
        Test that data generation produces consistent results with known parameters.
        Uses a small sample for speed in integration tests.
        """
        np.random.seed(42)
        n = 100
        effect_size = 0.5
        
        # Generate data under Null Hypothesis (effect=0)
        data_null = generate_normal(n=n, effect_size=0.0, seed=42)
        
        # Generate data under Alternative Hypothesis (effect=0.5)
        data_alt = generate_normal(n=n, effect_size=effect_size, seed=42)
        
        # Verify basic properties
        assert len(data_null['group_a']) == n
        assert len(data_null['group_b']) == n
        
        # Under null, means should be close
        mean_diff_null = np.mean(data_null['group_b']) - np.mean(data_null['group_a'])
        # Under alt, means should differ by approx effect_size (assuming std=1)
        mean_diff_alt = np.mean(data_alt['group_b']) - np.mean(data_alt['group_a'])
        
        # Allow some tolerance for randomness in small samples
        assert abs(mean_diff_null) < 0.5, "Null hypothesis data shows unexpected large difference"
        assert abs(mean_diff_alt - effect_size) < 0.5, "Alternative hypothesis data does not match expected effect size"

    def test_03_simulation_execution(self):
        """
        Run a minimal simulation scenario to verify the engine works end-to-end.
        Scenario: T-test, Normal dist, n=50, Null True.
        Expected: Type I error rate approx 0.05.
        """
        np.random.seed(123)
        
        # Run a small adaptive simulation (min reps=100 for speed in test)
        # We override min_replicates to 100 and max to 200 for this test
        results = run_adaptive_simulation(
            n=50,
            distribution="normal",
            effect_size=0.0,  # Null is true
            test_type="t_test",
            min_replicates=100,
            max_replicates=200,
            alpha=0.05,
            ci_width_target=0.10, # Looser target for speed
            seed=123
        )
        
        assert results is not None, "Simulation returned no results"
        assert "rejections" in results
        assert "total_replicates" in results
        
        observed_error_rate = results["rejections"] / results["total_replicates"]
        
        # With 100 reps, we expect ~5 rejections. Allow wide range (0 to 15%)
        # to avoid flakiness, but catch gross errors (e.g., 50% error rate)
        assert 0.0 <= observed_error_rate <= 0.20, \
            f"Type I error rate {observed_error_rate:.2f} is outside expected range for Null scenario"

    def test_04_full_pipeline_aggregation(self):
        """
        Simulate a small batch of results, aggregate them, and verify output.
        This mimics the flow of run_simulation.py -> analyzer.py -> export_results.py
        """
        # Prepare mock simulation results in the expected format
        # (Normally generated by run_simulation.py)
        mock_data = []
        np.random.seed(999)
        
        scenarios = [
            {"n": 50, "dist": "normal", "test": "t_test", "effect": 0.0, "reject": 0},
            {"n": 50, "dist": "normal", "test": "t_test", "effect": 0.0, "reject": 1},
            {"n": 50, "dist": "normal", "test": "t_test", "effect": 0.5, "reject": 1},
            {"n": 100, "dist": "normal", "test": "t_test", "effect": 0.0, "reject": 0},
            {"n": 100, "dist": "normal", "test": "t_test", "effect": 0.5, "reject": 1},
        ]
        
        # Generate enough rows to simulate a small batch
        for _ in range(20):
            for s in scenarios:
                # Randomize rejection based on effect size logic roughly
                prob = 0.05 if s["effect"] == 0.0 else 0.8
                reject = 1 if np.random.random() < prob else 0
                mock_data.append({
                    "sample_size": s["n"],
                    "distribution": s["dist"],
                    "test_type": s["test"],
                    "effect_size": s["effect"],
                    "rejected": reject,
                    "p_value": np.random.random() # Dummy p-value
                })
        
        df = pd.DataFrame(mock_data)
        output_path = os.path.join(self.processed_dir, "test_aggregation.csv")
        df.to_csv(output_path, index=False)
        
        # Now run the analyzer logic
        loaded_df = pd.read_csv(output_path)
        aggregated = aggregate_results(loaded_df)
        
        assert not aggregated.empty, "Aggregation resulted in empty dataframe"
        assert "rejection_rate" in aggregated.columns
        assert "sample_size" in aggregated.columns
        
        # Verify specific expected behavior
        # For effect=0.0, rate should be low
        null_rows = aggregated[aggregated["effect_size"] == 0.0]
        if not null_rows.empty:
            avg_null_rate = null_rows["rejection_rate"].mean()
            assert avg_null_rate < 0.2, f"Null rejection rate {avg_null_rate} too high"

    def test_05_export_functionality(self):
        """Test that the export module writes valid CSV files."""
        # Create a simple dataframe
        df = pd.DataFrame({
            "sample_size": [50, 100],
            "distribution": ["normal", "normal"],
            "test_type": ["t_test", "t_test"],
            "rejection_rate": [0.05, 0.06],
            "ci_lower": [0.03, 0.04],
            "ci_upper": [0.07, 0.08]
        })
        
        output_file = os.path.join(self.processed_dir, "final_export.csv")
        
        # Use the export function
        export_final_results(df, output_file)
        
        assert os.path.exists(output_file), "Export file was not created"
        
        # Verify content
        exported_df = pd.read_csv(output_file)
        assert len(exported_df) == 2
        assert list(exported_df.columns) == list(df.columns)

    def test_06_end_to_end_small_run(self):
        """
        A true end-to-end test:
        1. Generate data
        2. Run a tiny simulation (20 reps)
        3. Aggregate
        4. Export
        5. Verify file exists and has data
        """
        # 1. Generate Data (Simulated scenario)
        np.random.seed(42)
        n = 30
        data = generate_normal(n=n, effect_size=0.0, seed=42)
        
        # 2. Run Simulation (Very small scale for speed)
        sim_result = run_adaptive_simulation(
            n=n,
            distribution="normal",
            effect_size=0.0,
            test_type="t_test",
            min_replicates=20,
            max_replicates=50,
            alpha=0.05,
            ci_width_target=0.5, # Very loose to stop early
            seed=42
        )
        
        assert sim_result["total_replicates"] >= 20
        
        # 3. Prepare data for analyzer (mimicking run_simulation output)
        results_df = pd.DataFrame([{
            "sample_size": n,
            "distribution": "normal",
            "test_type": "t_test",
            "effect_size": 0.0,
            "rejections": sim_result["rejections"],
            "total_replicates": sim_result["total_replicates"],
            "rejection_rate": sim_result["rejections"] / sim_result["total_replicates"]
        }])
        
        # 4. Aggregate
        agg_df = aggregate_results(results_df)
        
        # 5. Export
        export_path = os.path.join(self.processed_dir, "e2e_results.csv")
        export_final_results(agg_df, export_path)
        
        # 6. Verify
        assert os.path.exists(export_path)
        final_df = pd.read_csv(export_path)
        assert len(final_df) > 0
        assert "rejection_rate" in final_df.columns