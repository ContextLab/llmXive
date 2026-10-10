"""
Unit tests for the aggregation helper added for T007.
These tests exercise the ``generate_aggregated_metrics`` function
on a tiny synthetic dataset to ensure the output CSV conforms to the
contract and that the statistical calculations run without error.
"""
import csv
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np

from analysis.stats import generate_aggregated_metrics

def test_aggregation_produces_expected_columns():
    # Create a minimal synthetic estimation results CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_csv = tmpdir_path / "estimation_results.csv"
        output_csv = tmpdir_path / "aggregated_metrics.csv"

        df = pd.DataFrame({
            "tau_squared": [0.0, 0.0, 0.1, 0.1, 0.1],
            "bias": [0.01, -0.02, 0.05, -0.03, 0.00],
            "coverage_flag": [True, True, False, True, False],
        })
        df.to_csv(input_csv, index=False)

        # Run aggregation
        generate_aggregated_metrics(input_csv, output_csv)

        # Verify CSV exists and has required columns
        assert output_csv.exists()
        with output_csv.open(newline="") as f:
            reader = csv.DictReader(f)
            expected_fields = {
                "tau2_level",
                "coverage_rate",
                "mean_bias",
                "p_value_binomial",
                "p_value_normality_test",
                "test_type_bias_comparison",
            }
            assert set(reader.fieldnames) == expected_fields

            rows = list(reader)
            # Should have two rows (tau=0.0 and tau=0.1)
            assert len(rows) == 2

            # Basic sanity checks on numeric fields
            for row in rows:
                assert float(row["coverage_rate"]) >= 0.0
                assert float(row["coverage_rate"]) <= 1.0
                assert float(row["mean_bias"]) != 0.0 or float(row["p_value_binomial"]) != 0.0
                assert row["test_type_bias_comparison"] in {"ANOVA", "Kruskal-Wallis"}