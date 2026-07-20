"""
Integration test for the complete quickstart flow.

This test verifies that the entire pipeline runs end-to-end
and produces all expected outputs.
"""
import os
import sys
import pytest
from pathlib import Path
import subprocess
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

class TestQuickstartFlow:
    """Integration tests for the complete quickstart pipeline."""

    @pytest.fixture(scope="class")
    def config(self):
        """Provide config for all tests in this class."""
        return Config()

    @pytest.fixture(scope="class", autouse=True)
    def run_pipeline(self, config):
        """Run the complete pipeline before tests."""
        # Skip if we're in a minimal test environment
        if os.environ.get("SKIP_FULL_PIPELINE", "false").lower() == "true":
            pytest.skip("Skipping full pipeline execution")
        
        # Run the quickstart validation script
        result = subprocess.run(
            [sys.executable, "-m", "scripts.run_quickstart_validation"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hours for full pipeline
        )
        
        # Store result for other tests
        self.pipeline_result = result
        
        # If pipeline failed, log and skip further tests
        if result.returncode != 0:
            pytest.fail(f"Pipeline execution failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

    def test_pipeline_execution_succeeds(self, config):
        """Test that the pipeline completes without errors."""
        assert self.pipeline_result.returncode == 0, "Pipeline execution failed"

    def test_preprocessed_subjects_json_exists(self, config):
        """Test that preprocessed subjects list is created."""
        path = config.DATA_PROCESSED_DIR / "preprocessed_subjects.json"
        assert path.exists(), f"File not found: {path}"
        
        with open(path) as f:
            data = json.load(f)
        
        assert "subjects" in data, "Missing 'subjects' key in preprocessed_subjects.json"
        assert isinstance(data["subjects"], list), "'subjects' should be a list"

    def test_network_metrics_csv_exists_and_valid(self, config):
        """Test that network metrics CSV is created and has expected columns."""
        path = config.DATA_METRICS_DIR / "network_metrics.csv"
        assert path.exists(), f"File not found: {path}"
        
        df = pd.read_csv(path)
        
        # Check required columns
        required_columns = ["subject_id", "modularity_q", "global_efficiency", "local_efficiency"]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check for FD column (mandatory covariate)
        assert "fd_mean" in df.columns or "framewise_displacement" in df.columns, \
            "Missing FD covariate column in network_metrics.csv"

    def test_statistical_results_csv_exists_and_valid(self, config):
        """Test that statistical results CSV is created and has expected structure."""
        path = config.DATA_METRICS_DIR / "statistical_results.csv"
        assert path.exists(), f"File not found: {path}"
        
        df = pd.read_csv(path)
        
        # Check for key statistical columns
        expected_cols = ["metric_name", "coefficient", "p_value", "vif", "fdr_corrected_p"]
        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_subject_info_json_exists(self, config):
        """Test that subject info JSON is created."""
        path = config.DATA_METRICS_DIR / "subject_info.json"
        assert path.exists(), f"File not found: {path}"
        
        with open(path) as f:
            data = json.load(f)
        
        assert "subjects" in data, "Missing 'subjects' key"
        assert "exclusions" in data, "Missing 'exclusions' key"
        assert "motion_metrics" in data, "Missing 'motion_metrics' key"

    def test_final_report_exists(self, config):
        """Test that the final report is generated."""
        path = config.REPORTS_DIR / "results.md"
        assert path.exists(), f"File not found: {path}"
        
        with open(path) as f:
            content = f.read()
        
        # Check for key sections
        assert "## Statistical Results" in content or "# Results" in content, \
            "Missing statistical results section in report"
        assert "Associational" in content or "Association" in content, \
            "Report should frame findings as associational"

    def test_scatter_plot_exists(self, config):
        """Test that the scatter plot is generated."""
        path = config.FIGURES_DIR / "scatter_post_vs_pre.png"
        assert path.exists(), f"File not found: {path}"
        
        # Check file size (should be non-trivial)
        assert path.stat().st_size > 10000, "Scatter plot file is suspiciously small"

    def test_residual_plot_exists(self, config):
        """Test that the residual plot is generated."""
        path = config.FIGURES_DIR / "residuals.png"
        assert path.exists(), f"File not found: {path}"
        
        # Check file size
        assert path.stat().st_size > 10000, "Residual plot file is suspiciously small"

    def test_preprocessing_log_exists(self, config):
        """Test that preprocessing log is created."""
        path = config.LOGS_DIR / "preprocessing.log"
        assert path.exists(), f"File not found: {path}"
        
        with open(path) as f:
            content = f.read()
        
        # Check for exclusion logging
        assert "excluded" in content.lower() or "exclusion" in content.lower(), \
            "Preprocessing log should contain exclusion information"

    def test_no_synthetic_data_fallback(self, config):
        """Test that no synthetic data fallback was used."""
        # Check the logs for any mention of synthetic data
        log_path = config.LOGS_DIR / "quickstart_validation.log"
        if log_path.exists():
            with open(log_path) as f:
                content = f.read().lower()
            
            assert "synthetic" not in content or "using synthetic" not in content, \
                "Pipeline should not use synthetic data fallback"

    def test_motion_threshold_enforcement(self, config):
        """Test that motion threshold enforcement is logged."""
        log_path = config.LOGS_DIR / "preprocessing.log"
        assert log_path.exists(), "Preprocessing log not found"
        
        with open(log_path) as f:
            content = f.read()
        
        # Check for motion threshold mentions
        assert "motion" in content.lower() and ("threshold" in content.lower() or "fd" in content.lower()), \
            "Preprocessing log should mention motion threshold checks"

    def test_fdr_correction_applied(self, config):
        """Test that FDR correction is applied and logged."""
        results_path = config.DATA_METRICS_DIR / "statistical_results.csv"
        assert results_path.exists(), "Statistical results not found"
        
        df = pd.read_csv(results_path)
        
        # Check that FDR corrected p-values exist
        assert "fdr_corrected_p" in df.columns, "Missing FDR corrected p-values"
        
        # Check that some values are not NaN
        fdr_col = df["fdr_corrected_p"]
        assert fdr_col.notna().any(), "All FDR corrected p-values are NaN"