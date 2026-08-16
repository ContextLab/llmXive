import os
import sys
import subprocess
import json
import pytest
from pathlib import Path

# Add project root to path if needed (though in CI this is usually handled)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import Config

class TestE2EPositive:
    """
    T050b: Implement tests/integration/test_e2e_positive.py to verify the entire
    pipeline (Download -> Preprocess -> Metrics -> Stats -> Report) executes
    without manual intervention on a small N=10 subset (if data is available).
    """

    @pytest.fixture(scope="class")
    def config(self):
        """Load configuration for the test."""
        return Config()

    @pytest.fixture(scope="class", autouse=True)
    def setup_environment(self, config):
        """
        Ensure the environment is ready.
        If data is not available (verified_sources.json missing or invalid),
        this test is skipped as per T050a/T050b logic.
        """
        source_file = config.PROJECT_ROOT / "data" / "verified_sources.json"
        if not source_file.exists():
            pytest.skip("Data Unavailable: data/verified_sources.json not found. T050a should have passed.")

        try:
            with open(source_file, 'r') as f:
                data = json.load(f)
            if not data.get("has_pre_post") or not data.get("has_clinical_scores"):
                pytest.skip("Data Unavailable: Verified source lacks required pre/post or clinical scores.")
        except (json.JSONDecodeError, KeyError):
            pytest.skip("Data Unavailable: verified_sources.json is corrupted or invalid.")

    def test_full_pipeline_execution(self, config, tmp_path):
        """
        Run the full pipeline end-to-end.
        We execute the main.py script with the 'all' stage.
        We assert that the process exits with code 0.
        We assert that the critical output files exist.
        """
        # Change to project root to ensure relative paths work
        os.chdir(config.PROJECT_ROOT)

        # Construct the command
        cmd = [
            sys.executable,
            "code/main.py",
            "--stage", "all"
        ]

        # Run the pipeline
        # We allow a longer timeout as preprocessing and stats can take time
        # Note: In a real CI environment with N=10, this might take a while.
        # We rely on the fact that T014-T035 are implemented to be CPU efficient.
        try:
            result = subprocess.run(
                cmd,
                timeout=3600, # 1 hour timeout for safety
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution timed out after 1 hour.")

        # Check exit code
        if result.returncode != 0:
            # Log error for debugging if it fails
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            pytest.fail(f"Pipeline execution failed with code {result.returncode}.")

        # Verify critical deliverables exist
        # 1. QC Metrics
        qc_path = config.PROJECT_ROOT / "data" / "metrics" / "qc_metrics.csv"
        assert qc_path.exists(), f"Missing deliverable: {qc_path}"

        # 2. Network Metrics
        network_path = config.PROJECT_ROOT / "data" / "metrics" / "network_metrics.csv"
        assert network_path.exists(), f"Missing deliverable: {network_path}"

        # 3. Statistical Results (The specific missing file mentioned in failure)
        stats_path = config.PROJECT_ROOT / "data" / "metrics" / "statistical_results.csv"
        assert stats_path.exists(), f"Missing deliverable: {stats_path}"

        # 4. Power Analysis JSON
        power_path = config.PROJECT_ROOT / "data" / "metrics" / "power_analysis.json"
        assert power_path.exists(), f"Missing deliverable: {power_path}"

        # 5. Final Report
        report_path = config.PROJECT_ROOT / "reports" / "results.md"
        assert report_path.exists(), f"Missing deliverable: {report_path}"

        # 6. Log file
        log_path = config.PROJECT_ROOT / "logs" / "pipeline.log"
        assert log_path.exists(), f"Missing deliverable: {log_path}"

        # Write a success log for T050b verification
        ci_log = config.PROJECT_ROOT / "ci_e2e_log.txt"
        with open(ci_log, 'w') as f:
            f.write(f"E2E Positive Test Successful at {config.current_time}\n")
            f.write(f"Output files verified:\n")
            f.write(f"  - {qc_path}\n")
            f.write(f"  - {network_path}\n")
            f.write(f"  - {stats_path}\n")
            f.write(f"  - {power_path}\n")
            f.write(f"  - {report_path}\n")

    def test_report_framing(self, config):
        """
        Verify the report explicitly states 'ASSOCIATIONAL' if not randomized.
        """
        report_path = config.PROJECT_ROOT / "reports" / "results.md"
        if not report_path.exists():
            # If report doesn't exist, the previous test would have failed
            pytest.skip("Report not generated, skipping framing check.")

        with open(report_path, 'r') as f:
            content = f.read()

        # Check for the framing logic.
        # The spec says: if not randomized, default to ASSOCIATIONAL.
        # We expect the string "ASSOCIATIONAL" to appear in the report if the data
        # is not explicitly randomized (which is the case for most public datasets).
        # We check that the report *contains* the framing statement.
        assert "ASSOCIATIONAL" in content, "Report must explicitly frame findings as ASSOCIATIONAL."

    def test_power_analysis_schema(self, config):
        """
        Verify power_analysis.json contains min_N_required.
        """
        power_path = config.PROJECT_ROOT / "data" / "metrics" / "power_analysis.json"
        if not power_path.exists():
            pytest.skip("Power analysis not generated.")

        with open(power_path, 'r') as f:
            data = json.load(f)

        assert "min_N_required" in data, "power_analysis.json must contain 'min_N_required'."
        assert "effect_size" in data, "power_analysis.json must contain 'effect_size'."
        assert "method" in data, "power_analysis.json must contain 'method'."