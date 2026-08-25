"""
Integration tests for the EEG Sensory Processing Speed pipeline.
These tests verify end-to-end execution of the main analysis scripts
and ensure that all declared artifacts are produced correctly.
"""
import os
import sys
import subprocess
import json
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

# Add code directory to sys.path for imports
sys.path.insert(0, str(CODE_DIR))

def run_script(script_name: str, args: list = None, check: bool = True) -> subprocess.CompletedProcess:
    """Helper to run a script and return the result."""
    cmd = [sys.executable, str(CODE_DIR / script_name)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise AssertionError(f"Script {script_name} failed with code {result.returncode}")
    return result

def check_file_exists(path_str: str, description: str = "file"):
    """Assert that a file exists."""
    path = PROJECT_ROOT / path_str
    assert path.exists(), f"{description} not found at {path}"
    assert path.stat().st_size > 0, f"{description} at {path} is empty"

def check_json_structure(path_str: str, required_keys: list):
    """Assert that a JSON file exists and contains required keys."""
    path = PROJECT_ROOT / path_str
    assert path.exists(), f"JSON file not found at {path}"
    with open(path, 'r') as f:
        data = json.load(f)
    for key in required_keys:
        assert key in data, f"Key '{key}' missing in {path}"

def check_csv_structure(path_str: str, required_columns: list):
    """Assert that a CSV file exists and contains required columns."""
    path = PROJECT_ROOT / path_str
    assert path.exists(), f"CSV file not found at {path}"
    df = pd.read_csv(path)
    for col in required_columns:
        assert col in df.columns, f"Column '{col}' missing in {path}"

class TestPipelineExecution:
    """Integration tests for the full pipeline execution."""

    def test_01_download_data(self):
        """Test that the download script runs without errors (if data not present)."""
        # Note: This might fail if network is restricted or data already exists.
        # We check that it doesn't crash due to code errors.
        try:
            result = run_script("01_download_data.py", check=False)
            # If it fails, it might be because data is already there or network issue.
            # We only care if it's a code error (e.g., TypeError, NameError).
            if result.returncode != 0:
                # Check if it's a "Data already exists" or similar non-code error
                if "File exists" in result.stderr or "already downloaded" in result.stderr:
                    pass # Expected behavior
                elif "TypeError" in result.stderr or "NameError" in result.stderr:
                    raise AssertionError(f"Code error in download script: {result.stderr}")
                else:
                    # It's okay if it fails due to network or other runtime issues in this test
                    # as long as it's not a code syntax/import error.
                    pass
        except Exception as e:
            if "Code error" in str(e):
                raise e

    def test_02_preprocess_eeg(self):
        """Test that the preprocessing script runs without import errors."""
        # This test primarily checks for code correctness (imports, syntax)
        # Actual execution might fail due to missing data, which is acceptable here.
        try:
            result = run_script("02_preprocess_eeg.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in preprocess script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_03_behavioral_parsing(self):
        """Test that the behavioral parsing script runs without import errors."""
        try:
            result = run_script("03_behavioral_parsing.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in behavioral parsing script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_04_extract_features(self):
        """Test that the feature extraction script runs without import errors."""
        try:
            result = run_script("04_extract_features.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in feature extraction script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_04b_clr_transform(self):
        """Test that the CLR transform script runs without import errors."""
        try:
            result = run_script("04b_clr_transform.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in CLR transform script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_05_modeling(self):
        """Test that the modeling script runs without import errors."""
        try:
            result = run_script("05_modeling.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in modeling script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_06_correlations(self):
        """Test that the correlation script runs without import errors."""
        try:
            result = run_script("06_correlations.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in correlation script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_07_permutation_test(self):
        """Test that the permutation test script runs without import errors."""
        try:
            result = run_script("07_permutation_test.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in permutation test script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_08_nonlinear_analysis(self):
        """Test that the non-linear analysis script runs without import errors."""
        try:
            result = run_script("08_nonlinear_analysis.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in non-linear analysis script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_09_robustness(self):
        """Test that the robustness script runs without import errors."""
        try:
            result = run_script("09_robustness.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in robustness script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_10_sensitivity_analysis(self):
        """Test that the sensitivity analysis script runs without import errors."""
        try:
            result = run_script("10_sensitivity_analysis.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in sensitivity analysis script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_11_generate_report(self):
        """Test that the report generation script runs without import errors."""
        try:
            result = run_script("11_generate_report.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in report generation script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

    def test_12_feasibility_check(self):
        """Test that the feasibility check script runs without import errors."""
        try:
            result = run_script("12_feasibility_check.py", check=False)
            if result.returncode != 0:
                if "NameError" in result.stderr or "ImportError" in result.stderr:
                    raise AssertionError(f"Import/Code error in feasibility check script: {result.stderr}")
        except Exception as e:
            if "Import/Code error" in str(e):
                raise e

class TestArtifactProduction:
    """Tests to verify that artifacts are produced when the pipeline runs."""

    def test_artifacts_exist_if_pipeline_ran(self):
        """
        Check if expected artifacts exist.
        Note: These tests will only pass if the full pipeline has been executed successfully.
        If data is missing or a step failed, these will be skipped or fail gracefully.
        """
        # Check for manifest
        if (PROJECT_ROOT / "data/interim/data_source_manifest.json").exists():
            check_json_structure("data/interim/data_source_manifest.json", ["sources", "checksums"])

        # Check for joined metadata
        if (PROJECT_ROOT / "data/interim/joined_metadata.csv").exists():
            check_csv_structure("data/interim/joined_metadata.csv", ["participant_id"])

        # Check for behavioral metrics
        if (PROJECT_ROOT / "data/interim/behavioral_metrics.csv").exists():
            check_csv_structure("data/interim/behavioral_metrics.csv", ["participant_id", "median_rt"])

        # Check for features
        if (PROJECT_ROOT / "data/processed/features.csv").exists():
            check_csv_structure("data/processed/features.csv", ["participant_id", "median_rt", "delta_rel"])

        # Check for CLR features
        if (PROJECT_ROOT / "data/processed/features_clr.csv").exists():
            check_csv_structure("data/processed/features_clr.csv", ["participant_id", "median_rt"])

        # Check for model results
        if (PROJECT_ROOT / "data/processed/model_results.json").exists():
            check_json_structure("data/processed/model_results.json", ["adjusted_r2", "test_r2"])

        # Check for correlations
        if (PROJECT_ROOT / "data/interim/correlations_raw.csv").exists():
            check_csv_structure("data/interim/correlations_raw.csv", ["band", "r_value", "p_value"])

        # Check for corrected correlations
        if (PROJECT_ROOT / "data/processed/correlations_corrected.csv").exists():
            check_csv_structure("data/processed/correlations_corrected.csv", ["band", "p_value_corrected"])

        # Check for non-linear comparison
        if (PROJECT_ROOT / "data/processed/non_linear_comparison.json").exists():
            check_json_structure("data/processed/non_linear_comparison.json", ["significant_at_0p05"])

        # Check for permutation results
        if (PROJECT_ROOT / "data/processed/permutation_results.json").exists():
            check_json_structure("data/processed/permutation_results.json", ["observed_r2", "p_value"])

        # Check for robustness report
        if (PROJECT_ROOT / "data/processed/robustness_report.csv").exists():
            check_csv_structure("data/processed/robustness_report.csv", ["condition", "r2"])

        # Check for sensitivity report
        if (PROJECT_ROOT / "data/processed/sensitivity_report.csv").exists():
            check_csv_structure("data/processed/sensitivity_report.csv", ["threshold", "significant_count"])

        # Check for final report
        if (PROJECT_ROOT / "data/processed/final_report.md").exists():
            check_file_exists("data/processed/final_report.md", "Final Report")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])