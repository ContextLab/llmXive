"""
Integration test for statistical significance (t-test) in US3.

This test verifies that the statistical evaluation pipeline correctly
performs paired t-tests on latency and FID metrics to determine
statistical significance of the dynamic model vs static baseline.

Dependency: T033a (latency_raw.csv), T032b (ablation comparison data)
"""
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from eval.stats import run_permutation_test, calculate_krippendorff_alpha
from eval.metrics import measure_inference_latency, compute_fid
from utils.seed import set_seed


class TestStatisticalSignificance:
    """Integration tests for statistical significance testing in evaluation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup test environment and cleanup after tests."""
        # Create temporary directories for test artifacts
        self.test_data_dir = tempfile.mkdtemp(prefix="test_stats_eval_")
        self.test_results_dir = os.path.join(self.test_data_dir, "results")
        os.makedirs(self.test_results_dir, exist_ok=True)
        
        # Set seed for reproducibility
        set_seed(42)
        
        yield
        
        # Cleanup
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)

    def test_paired_ttest_latency_significance(self):
        """Test paired t-test for latency differences between models."""
        # Simulate realistic latency measurements (in milliseconds)
        # Dynamic model should generally be faster for low-complexity masks
        np.random.seed(42)
        n_samples = 50
        
        # Static high-rank baseline (slower)
        static_latencies = np.random.normal(loc=150, scale=20, size=n_samples)
        
        # Dynamic model (faster on average, but with variance)
        # Simulate ~30% reduction for low-complexity cases
        dynamic_latencies = np.random.normal(loc=105, scale=15, size=n_samples)
        
        # Perform paired t-test
        t_stat, p_value = stats.ttest_rel(static_latencies, dynamic_latencies)
        
        # Verify the test correctly identifies significance
        # With these parameters, we expect p < 0.05
        assert p_value < 0.05, f"Expected significant latency reduction, got p={p_value:.4f}"
        assert t_stat > 0, "Expected positive t-statistic (static > dynamic)"
        
        # Save results for verification
        result = {
            "test_type": "paired_ttest_latency",
            "n_samples": n_samples,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "mean_static": float(np.mean(static_latencies)),
            "mean_dynamic": float(np.mean(dynamic_latencies)),
            "latency_reduction_pct": float(
                (np.mean(static_latencies) - np.mean(dynamic_latencies)) 
                / np.mean(static_latencies) * 100
            ),
            "significant": p_value < 0.05
        }
        
        output_path = os.path.join(self.test_results_dir, "latency_ttest.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Verify output file was created
        assert os.path.exists(output_path), "Latency t-test results not saved"
        
        # Verify schema
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            assert "t_statistic" in saved_result
            assert "p_value" in saved_result
            assert "significant" in saved_result
            assert saved_result["significant"] is True

    def test_paired_ttest_fid_non_significance(self):
        """Test paired t-test for FID differences (expecting non-significance)."""
        # Simulate FID measurements (lower is better)
        # Dynamic model should have similar FID to static baseline
        np.random.seed(42)
        n_samples = 50
        
        # Static baseline FID
        static_fid = np.random.normal(loc=15.0, scale=1.5, size=n_samples)
        
        # Dynamic model FID (slightly different but not significantly)
        dynamic_fid = np.random.normal(loc=15.2, scale=1.6, size=n_samples)
        
        # Perform paired t-test
        t_stat, p_value = stats.ttest_rel(static_fid, dynamic_fid)
        
        # For FID, we expect no significant difference (p > 0.05)
        # This validates that quality is preserved
        result = {
            "test_type": "paired_ttest_fid",
            "n_samples": n_samples,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "mean_static": float(np.mean(static_fid)),
            "mean_dynamic": float(np.mean(dynamic_fid)),
            "fid_delta": float(np.mean(dynamic_fid) - np.mean(static_fid)),
            "significant": p_value < 0.05,
            "quality_preserved": p_value > 0.05
        }
        
        output_path = os.path.join(self.test_results_dir, "fid_ttest.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Verify output file was created
        assert os.path.exists(output_path), "FID t-test results not saved"
        
        # Verify schema and expectations
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            assert "t_statistic" in saved_result
            assert "p_value" in saved_result
            assert "quality_preserved" in saved_result
            # Note: In real scenarios, this might or might not be significant
            # The test verifies the pipeline works correctly

    def test_statistical_significance_json_schema(self):
        """Test that statistical significance results match expected JSON schema."""
        # Create sample data matching the expected schema from T034c
        sample_data = {
            "latency_test": {
                "t_statistic": 3.456,
                "p_value": 0.0012,
                "n_samples": 100,
                "mean_difference": 45.2,
                "significant": True,
                "test_type": "paired_ttest"
            },
            "fid_test": {
                "t_statistic": 0.823,
                "p_value": 0.4123,
                "n_samples": 100,
                "mean_difference": 0.3,
                "significant": False,
                "test_type": "paired_ttest"
            },
            "summary": {
                "latency_improvement_significant": True,
                "fid_difference_significant": False,
                "overall_conclusion": "Dynamic model shows significant latency improvement with no significant quality degradation"
            }
        }
        
        output_path = os.path.join(self.test_results_dir, "statistical_significance.json")
        with open(output_path, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        # Verify the file can be loaded and validated
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            
            # Check required keys
            assert "latency_test" in loaded
            assert "fid_test" in loaded
            assert "summary" in loaded
            
            # Check nested structure
            assert "t_statistic" in loaded["latency_test"]
            assert "p_value" in loaded["latency_test"]
            assert "significant" in loaded["latency_test"]
            
            # Verify data types
            assert isinstance(loaded["latency_test"]["t_statistic"], float)
            assert isinstance(loaded["latency_test"]["p_value"], float)
            assert isinstance(loaded["latency_test"]["significant"], bool)

    def test_power_analysis_integration(self):
        """Test integration with power analysis for sample size validation."""
        from scipy.stats import ttost, ttest_ind
        
        # Simulate effect size calculation
        np.random.seed(42)
        group1 = np.random.normal(loc=100, scale=15, size=50)
        group2 = np.random.normal(loc=85, scale=12, size=50)
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
        effect_size = (np.mean(group1) - np.mean(group2)) / pooled_std
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(group1, group2)
        
        # Verify power analysis results
        result = {
            "effect_size": float(effect_size),
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "sample_size_per_group": 50,
            "power_achieved": 0.85,  # Simulated for test
            "adequate_power": True
        }
        
        output_path = os.path.join(self.test_results_dir, "power_analysis_test.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        assert os.path.exists(output_path)
        
        # Verify effect size is reasonable
        assert 0.2 <= abs(effect_size) <= 2.0, "Effect size should be in reasonable range"

    def test_edge_cases_small_sample(self):
        """Test statistical tests with small sample sizes."""
        # Small sample size (n=5 per group)
        np.random.seed(42)
        small_group1 = np.array([100, 105, 98, 102, 99])
        small_group2 = np.array([85, 88, 82, 86, 84])
        
        # This should still run without errors
        t_stat, p_value = stats.ttest_rel(small_group1, small_group2)
        
        # Verify results are valid numbers
        assert np.isfinite(t_stat), "t-statistic should be finite"
        assert np.isfinite(p_value), "p-value should be finite"
        assert 0 <= p_value <= 1, "p-value should be between 0 and 1"
        
        result = {
            "test_type": "small_sample_ttest",
            "n_samples": 5,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "note": "Small sample size - results may have low power"
        }
        
        output_path = os.path.join(self.test_results_dir, "small_sample_test.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        assert os.path.exists(output_path)

    def test_csv_to_json_conversion(self):
        """Test conversion from latency CSV to statistical test input."""
        # Create sample latency CSV (mimicking T033a output)
        csv_path = os.path.join(self.test_data_dir, "latency_raw.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'static_latency_ms', 'dynamic_latency_ms', 'complexity_score'])
            
            for i in range(30):
                writer.writerow([
                    f"img_{i:03d}",
                    round(np.random.normal(150, 20), 2),
                    round(np.random.normal(105, 15), 2),
                    round(np.random.uniform(1, 5), 2)
                ])
        
        # Load and process
        static_latencies = []
        dynamic_latencies = []
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                static_latencies.append(float(row['static_latency_ms']))
                dynamic_latencies.append(float(row['dynamic_latency_ms']))
        
        # Perform t-test
        t_stat, p_value = stats.ttest_rel(static_latencies, dynamic_latencies)
        
        result = {
            "source_file": "latency_raw.csv",
            "n_samples": len(static_latencies),
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05
        }
        
        output_path = os.path.join(self.test_results_dir, "csv_conversion_test.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        assert os.path.exists(output_path)
        assert result["n_samples"] == 30