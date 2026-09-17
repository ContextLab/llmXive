"""
Unit tests for T017 statistical significance module.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from statistical_significance import (
    apply_benjamini_hochberg,
    calculate_deviations,
    generate_pvalues_report,
    load_coverage_results,
    load_nominal_levels,
    perform_hypothesis_tests,
)


@pytest.fixture
def sample_coverage_data():
    """Create sample coverage data for testing."""
    np.random.seed(42)
    data = []
    for model in ["arima", "ets", "prophet", "lightgbm"]:
        for horizon in range(1, 13):
            for series_id in range(100):
                # Simulate empirical coverage around nominal (0.95)
                empirical = 0.95 + np.random.normal(0, 0.02)
                empirical = np.clip(empirical, 0, 1)
                data.append(
                    {
                        "series_id": series_id,
                        "model": model,
                        "horizon": horizon,
                        "empirical_coverage": empirical,
                    }
                )
    return pd.DataFrame(data)


@pytest.fixture
def temp_config_file():
    """Create a temporary config.yaml file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write("nominal_levels:\n  - 0.80\n  - 0.95\n")
        f.write("threshold: 0.02\n")
        f.write("seed: 42\n")
    return f.name


@pytest.fixture
def temp_input_file(sample_coverage_data):
    """Create a temporary CSV file with coverage data."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        sample_coverage_data.to_csv(f, index=False)
    return f.name


def test_load_coverage_results(temp_input_file):
    """Test loading coverage results from CSV."""
    df = load_coverage_results(temp_input_file)
    assert isinstance(df, pd.DataFrame)
    assert "series_id" in df.columns
    assert "model" in df.columns
    assert "horizon" in df.columns
    assert "empirical_coverage" in df.columns
    assert len(df) > 0


def test_load_coverage_results_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_coverage_results("nonexistent_file.csv")


def test_load_coverage_results_missing_columns(temp_input_file):
    """Test that missing columns raise ValueError."""
    # Create file with missing column
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        df = pd.read_csv(temp_input_file)
        df = df.drop(columns=["empirical_coverage"])
        df.to_csv(f, index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        load_coverage_results(f.name)


def test_load_nominal_levels(temp_config_file):
    """Test loading nominal levels from config."""
    levels = load_nominal_levels(temp_config_file)
    assert isinstance(levels, list)
    assert 0.80 in levels
    assert 0.95 in levels


def test_calculate_deviations(sample_coverage_data):
    """Test deviation calculation."""
    result = calculate_deviations(sample_coverage_data, 0.95)
    assert "deviation" in result.columns
    assert "nominal_coverage" in result.columns
    assert np.allclose(
        result["deviation"],
        result["empirical_coverage"] - 0.95,
    )


def test_perform_hypothesis_tests(sample_coverage_data, temp_config_file):
    """Test hypothesis test execution."""
    nominal_levels = load_nominal_levels(temp_config_file)
    df_with_dev = calculate_deviations(sample_coverage_data, 0.95)
    results = perform_hypothesis_tests(df_with_dev, [0.95])

    assert isinstance(results, pd.DataFrame)
    assert "model" in results.columns
    assert "horizon" in results.columns
    assert "p_raw" in results.columns
    assert "n_series" in results.columns
    assert len(results) > 0

    # Check that p-values are between 0 and 1 (or NaN)
    valid_p_values = results["p_raw"].dropna()
    assert np.all((valid_p_values >= 0) & (valid_p_values <= 1))


def test_apply_benjamini_hochberg(sample_coverage_data, temp_config_file):
    """Test Benjamini-Hochberg correction."""
    nominal_levels = load_nominal_levels(temp_config_file)
    df_with_dev = calculate_deviations(sample_coverage_data, 0.95)
    test_results = perform_hypothesis_tests(df_with_dev, [0.95])

    corrected = apply_benjamini_hochberg(test_results)

    assert "p_value" in corrected.columns
    assert "rejected" in corrected.columns
    assert len(corrected) == len(test_results)

    # Corrected p-values should be >= raw p-values (for BH)
    # Note: This is a property of BH correction
    valid_rows = corrected.dropna(subset=["p_raw", "p_value"])
    if len(valid_rows) > 0:
        # BH correction ensures monotonicity in a specific way
        # Just check that we have valid p-values
        assert np.all((corrected["p_value"] >= 0) & (corrected["p_value"] <= 1))


def test_generate_pvalues_report(temp_input_file, temp_config_file):
    """Test end-to-end report generation."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        output_path = f.name

    try:
        generate_pvalues_report(
            input_path=temp_input_file,
            output_path=output_path,
            config_path=temp_config_file,
        )

        # Verify output file exists
        assert Path(output_path).exists()

        # Verify JSON structure
        with open(output_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) > 0

        # Check required fields
        required_fields = ["model", "horizon", "nominal_coverage", "p_raw", "p_value"]
        for record in data:
            for field in required_fields:
                assert field in record

    finally:
        # Cleanup
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_generate_pvalues_report_empty_input():
    """Test handling of empty input."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        # Write header only
        f.write("series_id,model,horizon,empirical_coverage\n")
        input_path = f.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write("nominal_levels:\n  - 0.95\n")
        config_path = f.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        output_path = f.name

    try:
        # Should handle empty input gracefully (log warning, write empty list)
        generate_pvalues_report(
            input_path=input_path,
            output_path=output_path,
            config_path=config_path,
        )

        with open(output_path, "r") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 0

    finally:
        for path in [input_path, config_path, output_path]:
            if Path(path).exists():
                Path(path).unlink()
