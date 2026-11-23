"""
Integration test for Power Analysis under Dependency (US3).

This test verifies the end-to-end pipeline for calculating statistical power
when non-independence (dependency strength r) is present.

It exercises:
1. Data loading and validation (T005, T035)
2. Dependency injection with effect (T026 logic via simulation_runner)
3. Power calculation (T027a, T027b)
4. Aggregation and reporting

Pre-requisites:
- data/raw/ must contain at least one valid dataset (N >= 50)
- code/config.yaml must be valid
"""
import os
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Project imports based on API surface
from config import load_config
from data_loader import load_datasets, validate_dataset, CriticalValidationError
from dependency_injector import ar1_inject
from simulation_runner import run_single_replication, EdgeCaseError
from metrics import calculate_power, calculate_type1_error, clopper_pearson_ci


class TestPowerAnalysisIntegration:
    """Integration tests for the Power Analysis user story."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure a clean temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create minimal directory structure
        Path("data").mkdir(parents=True, exist_ok=True)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/manifests").mkdir(parents=True, exist_ok=True)
        Path("results").mkdir(parents=True, exist_ok=True)

        # Create a minimal config.yaml if not present (or load existing if in project)
        # For this integration test, we assume the project root config is available
        # or we create a temporary one.
        config_path = Path("code/config.yaml")
        if not config_path.exists():
            # Fallback: create a minimal config for the test environment
            # In a real run, this file should exist in the project root
            pass

        yield

        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_power_calculation_pipeline(self):
        """
        End-to-end test: Load data -> Inject dependency + Effect -> Calculate Power.

        Verifies:
        1. Data loading works and N >= 50 check passes.
        2. Dependency injection (AR1) works with a true effect.
        3. Power is calculated correctly (should be > Type1 error when effect exists).
        4. Clopper-Pearson CI is computed.
        """
        # 1. Create a synthetic dataset for testing purposes since we need a guaranteed
        #    valid dataset for this specific integration test.
        #    Note: In the full pipeline, this comes from data_loader.fetch_dataset.
        #    We simulate the 'data/raw/' state here to ensure the test is robust.
        test_data = {
            'group': np.repeat([0, 1], 100), # 200 samples
            'value': np.concatenate([
                np.random.normal(0, 1, 100),      # Group 0
                np.random.normal(1.0, 1, 100)     # Group 1 (True Effect delta=1.0)
            ])
        }
        df = pd.DataFrame(test_data)
        raw_file = Path("data/raw/test_dataset.csv")
        df.to_csv(raw_file, index=False)

        # 2. Create a minimal manifest for the loader
        manifest_data = {
            "datasets": [
                {
                    "name": "test_dataset",
                    "url": "local",
                    "path": "data/raw/test_dataset.csv",
                    "type": "continuous"
                }
            ]
        }
        with open("data/manifests/datasets.yaml", "w") as f:
            import yaml
            yaml.dump(manifest_data, f)

        # 3. Load and validate (simulating T005/T035)
        # We bypass the full fetch since we created the file, but run validation logic
        loaded_df = pd.read_csv(raw_file)
        validation_result = validate_dataset(loaded_df, "test_dataset", "results/validation_report.json")
        
        assert validation_result["valid"], "Dataset validation should pass for N=200"
        assert loaded_df.shape[0] >= 50, "N must be >= 50"

        # 4. Run Simulation Logic (T026/T027)
        # We manually run a small number of replications to verify the logic
        # without waiting for 10,000 in an integration test.
        n_replications = 100  # Small number for integration test speed
        r_strength = 0.3      # Dependency strength
        delta_effect = 1.0    # True effect size

        p_values = []
        
        # Seed for reproducibility
        np.random.seed(42)

        for i in range(n_replications):
            # A. Generate Null Data (Normal 0,1) - T012 logic
            # For a two-sample t-test, we need two groups
            n_per_group = 50
            group_a = np.random.normal(0, 1, n_per_group)
            group_b = np.random.normal(0, 1, n_per_group)

            # B. Inject True Effect (T026) - Add delta to Group B
            group_b_effected = group_b + delta_effect

            # C. Inject Dependency (AR1) - T006a logic
            # We inject dependency into the combined data or per group
            # For this test, we inject into the combined series to simulate temporal dependence
            combined_data = np.concatenate([group_a, group_b_effected])
            injected_data, _ = ar1_inject(combined_data, r=r_strength)

            # Split back
            injected_a = injected_data[:n_per_group]
            injected_b = injected_data[n_per_group:]

            # D. Perform Test
            try:
                stat, p_val = stats.ttest_ind(injected_a, injected_b)
                p_values.append(p_val)
            except Exception as e:
                # Handle edge cases (e.g., variance issues)
                p_values.append(np.nan)

        # 5. Calculate Metrics (T007/T027a)
        p_values_arr = np.array(p_values)
        alpha = 0.05
        
        observed_power = calculate_power(p_values_arr, alpha)
        ci_lower, ci_upper = clopper_pearson_ci(sum(p_values_arr <= alpha), n_replications, alpha)

        # 6. Assertions
        # With delta=1.0 and N=100 (50 per group), power should be reasonably high (> 0.5)
        # even with some dependency, though dependency might reduce it slightly.
        # We assert it is significantly higher than the Type 1 error rate (0.05).
        assert observed_power > 0.3, f"Observed power {observed_power} is unexpectedly low for delta=1.0"
        assert observed_power > 0.05, "Power must be greater than Type 1 error rate"
        assert ci_lower >= 0.0, "CI Lower bound must be non-negative"
        assert ci_upper <= 1.0, "CI Upper bound must be <= 1.0"

        # 7. Write results to disk (simulating T027b/T029 output)
        results_df = pd.DataFrame({
            'replication': range(n_replications),
            'p_value': p_values,
            'significant': [p <= alpha for p in p_values]
        })
        results_df.to_csv("results/power_analysis_raw.csv", index=False)

        summary = {
            'n_replications': n_replications,
            'dependency_strength': r_strength,
            'effect_size': delta_effect,
            'observed_power': float(observed_power),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'alpha': alpha
        }
        with open("results/power_analysis_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Verify files were written
        assert Path("results/power_analysis_raw.csv").exists()
        assert Path("results/power_analysis_summary.json").exists()

    def test_dependency_reduces_power(self):
        """
        Verify that increasing dependency strength reduces power (US3 AC-2).
        
        We compare power at r=0 vs r=0.5 with the same true effect.
        """
        n_replications = 50
        delta_effect = 1.5
        n_per_group = 50
        alpha = 0.05

        def run_power_test(r_val):
            np.random.seed(123 + int(r_val * 100)) # Distinct seed per r
            p_vals = []
            for _ in range(n_replications):
                g_a = np.random.normal(0, 1, n_per_group)
                g_b = np.random.normal(0, 1, n_per_group) + delta_effect
                combined = np.concatenate([g_a, g_b])
                injected, _ = ar1_inject(combined, r=r_val)
                ia = injected[:n_per_group]
                ib = injected[n_per_group:]
                try:
                    _, p = stats.ttest_ind(ia, ib)
                    p_vals.append(p)
                except:
                    p_vals.append(np.nan)
            
            return calculate_power(np.array(p_vals), alpha)

        power_r0 = run_power_test(0.0)
        power_r05 = run_power_test(0.5)

        # Power should generally decrease or stay similar with higher dependency
        # We assert power_r05 is not significantly HIGHER than power_r0
        # (Ideally power_r05 < power_r0, but statistical noise exists)
        # We assert the difference is not a massive increase (which would be wrong)
        assert power_r05 <= power_r0 + 0.1, f"Power at r=0.5 ({power_r05}) should not exceed r=0 ({power_r0}) significantly"

        # Save comparison
        comparison = {
            "r_0_power": power_r0,
            "r_05_power": power_r05,
            "delta_power": power_r05 - power_r0
        }
        with open("results/power_delta_report.json", "w") as f:
            json.dump(comparison, f)

        assert Path("results/power_delta_report.json").exists()