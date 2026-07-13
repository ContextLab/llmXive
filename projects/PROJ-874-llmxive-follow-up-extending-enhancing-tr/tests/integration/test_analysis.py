"""
Integration test for statistical analysis (T025).

This test validates the statistical analysis pipeline defined in code/analyze.py.
It verifies:
1. Power analysis correctly calculates power and flags underpowered studies.
2. Normality testing (Shapiro-Wilk) correctly identifies distribution type.
3. Adaptive statistical testing (Wilcoxon vs T-test) selects the correct test.
4. Failure case identification logic correctly flags degraded videos.
5. CSV report generation includes all required columns and data types.

Prerequisites:
- code/analyze.py must be implemented with functions:
  calculate_power, shapiro_wilk_test, adaptive_statistical_test,
  identify_failure_cases, generate_report
- Pilot study results must exist at data/pilot_variance.json (from T017)
- Naive baseline and corrected video metrics must be available for analysis
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_dataset_paths, get_results_dir, get_processed_dir
from analyze import (
    calculate_power,
    shapiro_wilk_test,
    adaptive_statistical_test,
    identify_failure_cases,
    generate_report
)


class TestStatisticalAnalysis:
    """Integration tests for the statistical analysis pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.test_dir) / "results"
        self.results_dir.mkdir(parents=True)

        # Mock pilot variance data
        self.mock_pilot_data = {
            "mean": 0.75,
            "std": 0.15,
            "n_samples": 5,
            "metric_name": "object_permanence"
        }

        # Save mock pilot data
        self.pilot_file = Path(self.test_dir) / "pilot_variance.json"
        with open(self.pilot_file, 'w') as f:
            json.dump(self.mock_pilot_data, f)

        # Create mock metric data for analysis
        self.mock_metrics = []
        for i in range(50):
            self.mock_metrics.append({
                "video_id": f"video_{i:03d}",
                "condition": "naive",
                "vbench_score": np.random.uniform(0.6, 0.9),
                "fvd": np.random.uniform(100, 300),
                "object_permanence": np.random.uniform(0.6, 0.95)
            })
            self.mock_metrics.append({
                "video_id": f"video_{i:03d}",
                "condition": "corrected",
                "vbench_score": np.random.uniform(0.65, 0.95),
                "fvd": np.random.uniform(80, 250),
                "object_permanence": np.random.uniform(0.65, 0.98)
            })

        self.metrics_df = pd.DataFrame(self.mock_metrics)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_power_analysis_sufficient(self):
        """Test that power analysis correctly identifies sufficient power."""
        # Create data with large effect size (should yield high power)
        n = 50
        mean_diff = 0.3
        std_dev = 0.15

        power = calculate_power(
            mean_diff=mean_diff,
            std_dev=std_dev,
            n_samples=n,
            alpha=0.05
        )

        assert power >= 0.8, f"Expected power >= 0.8 for large effect, got {power}"

    def test_power_analysis_insufficient(self):
        """Test that power analysis correctly identifies insufficient power."""
        # Create data with small effect size (should yield low power)
        n = 5
        mean_diff = 0.05
        std_dev = 0.15

        power = calculate_power(
            mean_diff=mean_diff,
            std_dev=std_dev,
            n_samples=n,
            alpha=0.05
        )

        assert power < 0.8, f"Expected power < 0.8 for small effect, got {power}"

    def test_shapiro_wilk_normal(self):
        """Test Shapiro-Wilk test correctly identifies normal distribution."""
        # Generate normal data
        normal_data = np.random.normal(loc=0.5, scale=0.1, size=100)

        stat, p_value = shapiro_wilk_test(normal_data)

        # For normal data, p-value should be > 0.05 (fail to reject null)
        assert p_value > 0.05, f"Expected p > 0.05 for normal data, got {p_value}"

    def test_shapiro_wilk_non_normal(self):
        """Test Shapiro-Wilk test correctly identifies non-normal distribution."""
        # Generate exponential data (non-normal)
        non_normal_data = np.random.exponential(scale=0.5, size=100)

        stat, p_value = shapiro_wilk_test(non_normal_data)

        # For non-normal data, p-value should be < 0.05 (reject null)
        assert p_value < 0.05, f"Expected p < 0.05 for non-normal data, got {p_value}"

    def test_adaptive_test_normal(self):
        """Test adaptive testing selects t-test for normal data."""
        # Generate paired normal data
        group1 = np.random.normal(loc=0.5, scale=0.1, size=50)
        group2 = np.random.normal(loc=0.55, scale=0.1, size=50)

        test_type, p_value = adaptive_statistical_test(group1, group2)

        assert test_type == "t-test", f"Expected t-test for normal data, got {test_type}"
        assert 0.0 <= p_value <= 1.0, f"Invalid p-value: {p_value}"

    def test_adaptive_test_non_normal(self):
        """Test adaptive testing selects Wilcoxon for non-normal data."""
        # Generate paired non-normal data (exponential)
        group1 = np.random.exponential(scale=0.5, size=50)
        group2 = np.random.exponential(scale=0.55, size=50)

        test_type, p_value = adaptive_statistical_test(group1, group2)

        assert test_type == "Wilcoxon", f"Expected Wilcoxon for non-normal data, got {test_type}"
        assert 0.0 <= p_value <= 1.0, f"Invalid p-value: {p_value}"

    def test_failure_case_identification(self):
        """Test failure case identification logic."""
        # Create metrics with some failure cases
        metrics = [
            {"video_id": "v1", "condition": "naive", "vbench_score": 0.8, "object_permanence": 0.9},
            {"video_id": "v1", "condition": "corrected", "vbench_score": 0.7, "object_permanence": 0.85},  # Drop < 5%
            {"video_id": "v2", "condition": "naive", "vbench_score": 0.8, "object_permanence": 0.9},
            {"video_id": "v2", "condition": "corrected", "vbench_score": 0.6, "object_permanence": 0.8},  # Drop >= 5%
        ]

        df = pd.DataFrame(metrics)
        failure_cases = identify_failure_cases(df)

        # v2 should be flagged (object_permanence drop >= 5%)
        assert len(failure_cases) >= 1, "Expected at least one failure case"
        assert "v2" in failure_cases["video_id"].values, "v2 should be flagged as failure case"

    def test_report_generation(self):
        """Test CSV report generation with all required columns."""
        output_file = self.results_dir / "analysis_report.csv"

        generate_report(
            metrics_df=self.metrics_df,
            output_path=str(output_file),
            pilot_file=str(self.pilot_file)
        )

        assert output_file.exists(), "Report file should be created"

        df = pd.read_csv(output_file)

        # Check required columns
        required_columns = [
            'video_id', 'condition', 'vbench_score', 'fvd',
            'object_permanence', 'p_value', 'test_type', 'power_sufficient'
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"

        # Check data types
        assert df['power_sufficient'].dtype == bool, "power_sufficient should be boolean"
        assert df['p_value'].dtype in [float, 'float64', 'float32'], "p_value should be numeric"

    def test_end_to_end_pipeline(self):
        """Test complete statistical analysis pipeline."""
        # Run power analysis
        pilot_data = self.mock_pilot_data
        power = calculate_power(
            mean_diff=0.2,
            std_dev=pilot_data['std'],
            n_samples=50,
            alpha=0.05
        )

        # Generate full report
        output_file = self.results_dir / "full_report.csv"
        generate_report(
            metrics_df=self.metrics_df,
            output_path=str(output_file),
            pilot_file=str(self.pilot_file)
        )

        assert output_file.exists(), "Full report should be generated"

        # Verify report content
        df = pd.read_csv(output_file)
        assert len(df) > 0, "Report should contain data"
        assert all(col in df.columns for col in ['p_value', 'test_type', 'power_sufficient']), \
            "Report missing statistical columns"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])