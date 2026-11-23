"""
Integration test for the end-to-end power analysis pipeline (T011).

This test verifies the full pipeline execution from data download to power curve generation.
It follows TDD principles: written first, failing until T012-T017 are implemented.

Test Configuration:
  - Dataset: ds000030
  - Sample Size: N=10
  - Smoothing Kernel: 4mm
  - Paradigm: Motor

Expected Output:
  - data/aggregated/power_curves.json
    - Contains 'sample_sizes_tested' (list of ints)
    - Contains 'empirical_rates' (list of floats)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# Configuration for this specific integration test
TEST_DATASET = "ds000030"
TEST_SAMPLE_SIZE = 10
TEST_KERNEL = 4
TEST_PARADIGM = "Motor"
EXPECTED_OUTPUT_FILE = Path("data/aggregated/power_curves.json")


class TestEndToEndPipeline:
    """Integration tests for the full statistical power analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Ensure required directories exist before running tests."""
        # Create necessary directories if they don't exist
        data_agg_dir = Path("data/aggregated")
        data_agg_dir.mkdir(parents=True, exist_ok=True)

        # Ensure we start with a clean output file state for this test
        if EXPECTED_OUTPUT_FILE.exists():
            EXPECTED_OUTPUT_FILE.unlink()

        yield

        # Cleanup after test (optional, but good practice)
        # Note: In CI, we might want to keep artifacts for debugging
        if EXPECTED_OUTPUT_FILE.exists():
            pass  # Keep for inspection

    def test_pipeline_execution_creates_power_curves(self):
        """
        Run the full pipeline and assert output file creation and structure.

        This test executes the main pipeline script with specific parameters
        and verifies the expected output artifact is generated with correct structure.
        """
        # Construct the command to run the pipeline
        # Using the main.py entry point with specific configuration
        cmd = [
            sys.executable,
            "code/main.py",
            "--dataset", TEST_DATASET,
            "--sample-size", str(TEST_SAMPLE_SIZE),
            "--kernel", str(TEST_KERNEL),
            "--paradigm", TEST_PARADIGM,
            "--iterations", "2",  # Reduced for CI speed, but >1 to test bootstrap
            "--verbose"
        ]

        # Execute the pipeline
        try:
            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Assert the pipeline completed successfully
            assert result.returncode == 0, (
                f"Pipeline execution failed with code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution timed out (exceeded 300 seconds)")
        except Exception as e:
            pytest.fail(f"Pipeline execution raised an exception: {str(e)}")

        # Assert output file exists
        assert EXPECTED_OUTPUT_FILE.exists(), (
            f"Expected output file {EXPECTED_OUTPUT_FILE} was not created. "
            "Check that T012-T017 are implemented correctly."
        )

        # Load and validate the JSON structure
        try:
            with open(EXPECTED_OUTPUT_FILE, "r", encoding="utf-8") as f:
                power_curves_data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Output file is not valid JSON: {str(e)}")

        # Validate required keys exist
        assert "sample_sizes_tested" in power_curves_data, (
            "Missing required key 'sample_sizes_tested' in power_curves.json"
        )
        assert "empirical_rates" in power_curves_data, (
            "Missing required key 'empirical_rates' in power_curves.json"
        )

        # Validate types and content
        sample_sizes = power_curves_data["sample_sizes_tested"]
        empirical_rates = power_curves_data["empirical_rates"]

        assert isinstance(sample_sizes, list), "'sample_sizes_tested' must be a list"
        assert isinstance(empirical_rates, list), "'empirical_rates' must be a list"
        assert len(sample_sizes) > 0, "'sample_sizes_tested' must not be empty"
        assert len(empirical_rates) > 0, "'empirical_rates' must not be empty"
        assert len(sample_sizes) == len(empirical_rates), (
            f"'sample_sizes_tested' (len={len(sample_sizes)}) and "
            f"'empirical_rates' (len={len(empirical_rates)}) must have same length"
        )

        # Validate data types within lists
        for i, size in enumerate(sample_sizes):
            assert isinstance(size, int), f"'sample_sizes_tested[{i}]' must be int, got {type(size)}"
            assert size > 0, f"'sample_sizes_tested[{i}]' must be positive, got {size}"

        for i, rate in enumerate(empirical_rates):
            assert isinstance(rate, (int, float)), f"'empirical_rates[{i}]' must be numeric, got {type(rate)}"
            assert 0.0 <= rate <= 1.0, (
                f"'empirical_rates[{i}]' must be between 0 and 1, got {rate}"
            )

        # Validate that the test sample size was included
        assert TEST_SAMPLE_SIZE in sample_sizes, (
            f"Test sample size {TEST_SAMPLE_SIZE} not found in sample_sizes_tested. "
            f"Found: {sample_sizes}"
        )

    def test_pipeline_logs_convergence(self):
        """
        Verify that convergence logging occurs during pipeline execution.

        This checks that T016/T016b functionality is active.
        """
        convergence_log_path = Path("data/aggregated/convergence_log.json")

        # The pipeline should create this file if GLM fitting occurred
        # We check existence as a proxy for T016/T016b execution
        assert convergence_log_path.exists(), (
            "Convergence log file not found. "
            "This indicates T016 (GLM fitting) or T016b (logging) may not be implemented."
        )

        # Validate log structure
        try:
            with open(convergence_log_path, "r", encoding="utf-8") as f:
                convergence_data = json.load(f)
            assert isinstance(convergence_data, list), "Convergence log must be a list"
        except json.JSONDecodeError:
            pytest.fail("Convergence log is not valid JSON")

    def test_pipeline_creates_traceability_config(self):
        """
        Verify that pipeline configuration is logged for traceability.

        This checks that T013c functionality is active.
        """
        config_log_path = Path("results/paper/pipeline_config.json")

        assert config_log_path.exists(), (
            "Pipeline configuration log not found. "
            "This indicates T013c (traceability logger) may not be implemented."
        )

        try:
            with open(config_log_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Verify required fields
            assert "pipeline_config_hash" in config_data, (
                "Missing 'pipeline_config_hash' in pipeline config"
            )
            assert "roi_mask" in config_data, "Missing 'roi_mask' in pipeline config"
            assert "smoothing_kernel" in config_data, "Missing 'smoothing_kernel' in pipeline config"
            
            # Verify fmriprep is explicitly noted as not used
            assert config_data.get("fmriprep_used") is False, (
                "Pipeline config should explicitly state fmriprep was not used"
            )
            
        except json.JSONDecodeError:
            pytest.fail("Pipeline config is not valid JSON")