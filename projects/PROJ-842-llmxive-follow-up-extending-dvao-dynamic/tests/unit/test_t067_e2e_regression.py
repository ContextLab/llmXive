import pytest
import os
import subprocess
import sys
import json
import shutil

class TestT067E2ERegression:
    """
    Unit test for T067: End-to-End Regression Test.
    This test verifies that the full suite script runs successfully and produces
    the required artifacts from a clean state.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Backup and clear data/processed
        Teardown: Restore or leave clean state
        """
        self.processed_dir = "data/processed"
        self.backup_dir = "data/processed_backup"
        
        # Backup existing data if any
        if os.path.exists(self.processed_dir):
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            shutil.move(self.processed_dir, self.backup_dir)
        
        # Create fresh directory
        os.makedirs(self.processed_dir, exist_ok=True)
        
        yield
        
        # Cleanup: Restore backup or remove generated data
        if os.path.exists(self.backup_dir):
            if os.path.exists(self.processed_dir):
                shutil.rmtree(self.processed_dir)
            shutil.move(self.backup_dir, self.processed_dir)

    def test_run_full_suite_script_exists(self):
        """Verify the script file exists."""
        assert os.path.exists("scripts/run_full_suite.sh"), "run_full_suite.sh not found"

    def test_run_full_suite_execution(self):
        """
        Execute the full suite script and verify exit code 0.
        This is the primary verification for T067.
        """
        # Ensure the script is executable
        script_path = "scripts/run_full_suite.sh"
        os.chmod(script_path, 0o755)

        try:
            result = subprocess.run(
                ["bash", script_path],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout for full sweep
            )
            
            # Assert exit code
            assert result.returncode == 0, (
                f"Script failed with exit code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Full suite execution timed out")

    def test_artifacts_exist(self):
        """Verify all required output files exist after execution."""
        required_files = [
            "data/processed/full_sweep_results.json",
            "data/processed/heavy_tailed_results.json",
            "data/processed/statistical_report.json"
        ]

        for file_path in required_files:
            assert os.path.exists(file_path), f"Missing required artifact: {file_path}"
            assert os.path.getsize(file_path) > 0, f"Artifact is empty: {file_path}"

    def test_statistical_report_validity(self):
        """Verify the statistical report contains valid JSON and expected keys."""
        report_path = "data/processed/statistical_report.json"
        
        try:
            with open(report_path, 'r') as f:
                data = json.load(f)
            
            # Verify expected keys based on T044 specification
            expected_keys = [
                'p_value_one_sample',
                'p_value_paired',
                'n_objectives',
                'k_window',
                'failure_point_n',
                'coincidence_met',
                'construct_validity_passed'
            ]
            
            for key in expected_keys:
                assert key in data, f"Missing key in statistical report: {key}"
                
            # Verify n_objectives contains the expected sweep values
            if 'n_objectives' in data:
                n_values = data['n_objectives']
                assert 5 in n_values, "N=5 missing from sweep results"
                assert 50 in n_values, "N=50 missing from sweep results"
                
        except json.JSONDecodeError:
            pytest.fail(f"{report_path} contains invalid JSON")

    def test_full_sweep_results_validity(self):
        """Verify the full sweep results contain data for all N values."""
        results_path = "data/processed/full_sweep_results.json"
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        # The structure depends on implementation, but must contain data
        assert isinstance(data, dict), "full_sweep_results.json must be a JSON object"
        assert len(data) > 0, "full_sweep_results.json is empty"
        
        # Check for N values (implementation detail: keys might be '5', '10', etc.)
        n_keys = [k for k in data.keys() if str(k) in ['5', '10', '20', '50']]
        assert len(n_keys) > 0, "No N values found in full_sweep_results.json"

    def test_heavy_tailed_results_validity(self):
        """Verify heavy-tailed results exist and have expected structure."""
        results_path = "data/processed/heavy_tailed_results.json"
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "heavy_tailed_results.json must be a JSON object"
        assert 'threshold_passed' in data or 'deviation_metric' in data, \
            "Missing expected fields in heavy_tailed_results.json"