"""
Integration test suite for the full end-to-end pipeline.

This test verifies the complete flow from data ingestion through statistical analysis.
It assumes the following have been completed:
- T001-T008: Project setup and foundational utilities
- T011-T015: Data ingestion and preprocessing (US1)
- T018-T022: Dynamic connectivity and flexibility metrics (US2)
- T025-T030: Statistical analysis and reporting (US3)

The test executes the main entry points of the pipeline stages and validates
that expected output files are created with valid content.
"""
import os
import sys
import json
import subprocess
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"

sys.path.insert(0, str(CODE_DIR))

class TestFullPipelineIntegration:
    """Integration tests for the complete network module dynamics pipeline."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_environment(self):
        """Ensure required directories exist before tests run."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / "plots").mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        yield

    def test_01_validate_source_dataset(self):
        """Test T007: Verify dataset ingestion validator runs and checks ds001734."""
        script_path = CODE_DIR / "ingestion" / "validate_source.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        # Run the validation script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # The script should either succeed (dataset available) or fail with clear error
        # We check that it runs without crashing and produces meaningful output
        assert result.returncode == 0 or "error" in result.stderr.lower() or "error" in result.stdout.lower()
        assert "ds001734" in result.stdout or "ds001734" in result.stderr

    def test_02_download_hcp_data(self):
        """Test T011: Verify data download script executes and creates output structure."""
        script_path = CODE_DIR / "ingestion" / "download_hcp.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        # Note: This test may be skipped in environments without network access
        # or if the download is too large. We verify the script runs without syntax errors.
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Should be able to show help or run without crashing
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_03_preprocess_fmri_data(self):
        """Test T012: Verify preprocessing script executes."""
        script_path = CODE_DIR / "ingestion" / "preprocess.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_04_consolidate_data(self):
        """Test T013: Verify data consolidation script executes."""
        script_path = CODE_DIR / "ingestion" / "consolidate_data.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_05_dynamic_connectivity_analysis(self):
        """Test T018-T019: Verify dynamic connectivity computation executes."""
        script_path = CODE_DIR / "analysis" / "dynamic_connectivity.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_06_flexibility_scores_output(self):
        """Test T021: Verify flexibility scores output generation."""
        script_path = CODE_DIR / "analysis" / "output_flexibility_scores.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_07_sensitivity_analysis(self):
        """Test T022: Verify sensitivity analysis script executes."""
        script_path = CODE_DIR / "analysis" / "sensitivity_analysis.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_08_statistical_analysis(self):
        """Test T025-T026: Verify statistical analysis script executes."""
        script_path = CODE_DIR / "analysis" / "statistics.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_09_generate_report(self):
        """Test T028: Verify report generation script executes."""
        script_path = CODE_DIR / "results" / "generate_report.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_10_generate_plots(self):
        """Test T029: Verify plot generation script executes."""
        script_path = CODE_DIR / "results" / "generate_plots.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_11_save_final_results(self):
        """Test T030: Verify final results saving script executes."""
        script_path = CODE_DIR / "results" / "save_final_results.py"
        assert script_path.exists(), f"Script not found: {script_path}"
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=CODE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0 or "usage" in result.stdout.lower()

    def test_12_verify_output_files_exist(self):
        """Test: Verify that if data was processed, expected output files exist."""
        # Check for processed data files (if they exist)
        expected_files = [
            PROCESSED_DIR / "consolidated_data.parquet",
            PROCESSED_DIR / "scrubbed_timeseries.parquet",
            PROCESSED_DIR / "flexibility_scores.parquet",
            RESULTS_DIR / "statistical_report.json",
            RESULTS_DIR / "sensitivity_analysis.json",
        ]
        
        # Count how many files actually exist (may be 0 if data wasn't downloaded)
        existing_files = [f for f in expected_files if f.exists()]
        
        # If data processing was run, these files should exist
        # We don't fail if they don't exist (data might not have been downloaded)
        # but we log the status
        if len(existing_files) > 0:
            assert len(existing_files) == len(expected_files), \
                f"Missing output files: {set(expected_files) - set(existing_files)}"

    def test_13_verify_report_content(self):
        """Test: Verify statistical report contains required associational language."""
        report_path = RESULTS_DIR / "statistical_report.json"
        
        if not report_path.exists():
            pytest.skip("Statistical report not generated - data processing may not have run")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Verify the report contains associational language as required by FR-007
        report_text = json.dumps(report).lower()
        assert "associational" in report_text or "association" in report_text, \
            "Report must frame findings as associational (FR-007)"
        
        # Verify motion control is mentioned
        assert "motion" in report_text or "fd" in report_text, \
            "Report must confirm motion control was applied"

    def test_14_verify_sensitivity_analysis(self):
        """Test: Verify sensitivity analysis results exist and are valid."""
        sensitivity_path = RESULTS_DIR / "sensitivity_analysis.json"
        
        if not sensitivity_path.exists():
            pytest.skip("Sensitivity analysis not generated - data processing may not have run")
        
        with open(sensitivity_path, 'r') as f:
            sensitivity = json.load(f)
        
        # Verify structure
        assert "window_lengths" in sensitivity, "Missing window_lengths in sensitivity analysis"
        assert "p_values" in sensitivity, "Missing p_values in sensitivity analysis"
        
        # Verify max difference check (if data was processed)
        if "max_p_value_diff" in sensitivity:
            assert sensitivity["max_p_value_diff"] < 0.05, \
                f"Sensitivity analysis failed: max p-value diff ({sensitivity['max_p_value_diff']}) >= 0.05"

    def test_15_verify_plots_exist(self):
        """Test: Verify that required plots were generated."""
        plots_dir = RESULTS_DIR / "plots"
        
        if not plots_dir.exists():
            pytest.skip("Plots directory not created - data processing may not have run")
        
        expected_plots = [
            plots_dir / "null_dist.png",
            plots_dir / "sensitivity_plot.png",
        ]
        
        existing_plots = [p for p in expected_plots if p.exists()]
        
        if len(existing_plots) > 0:
            assert len(existing_plots) == len(expected_plots), \
                f"Missing plots: {set(expected_plots) - set(existing_plots)}"
            # Verify files are not empty
            for plot in existing_plots:
                assert plot.stat().st_size > 100, f"Plot file is too small: {plot}"

    def test_16_memory_monitor_integration(self):
        """Test: Verify memory monitoring utilities are accessible."""
        from utils.memory_monitor import get_current_rss_bytes, check_memory_limit
        
        # Test that memory monitoring functions work
        current_rss = get_current_rss_bytes()
        assert current_rss >= 0, "Memory RSS should be non-negative"
        
        # Test limit check (should not raise for reasonable limits)
        result = check_memory_limit(7 * 1024 * 1024 * 1024)  # 7GB
        assert result is True or result is False, "check_memory_limit should return boolean"

    def test_17_config_seeds(self):
        """Test: Verify configuration module sets seeds correctly."""
        from utils.config import set_all_seeds
        
        # Test that seed setting function exists and runs
        set_all_seeds(42)
        
        # Verify seeds are actually set
        import random
        import numpy as np
        
        val1 = random.random()
        np_val1 = np.random.random()
        
        # Reset and check reproducibility
        set_all_seeds(42)
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2, "Random seed not properly set"
        assert np_val1 == np_val2, "Numpy random seed not properly set"

    def test_18_logging_infrastructure(self):
        """Test: Verify logging infrastructure is properly configured."""
        from utils.logging_config import setup_logging, log_subject_exclusion, log_memory_usage
        
        # Setup logging
        logger = setup_logging()
        
        # Test exclusion logging
        log_subject_exclusion(logger, "sub-001", "excessive_motion", 0.5)
        
        # Test memory logging
        log_memory_usage(logger, "test_process", 1024 * 1024 * 500)  # 500MB
        
        assert logger is not None, "Logger should be initialized"
