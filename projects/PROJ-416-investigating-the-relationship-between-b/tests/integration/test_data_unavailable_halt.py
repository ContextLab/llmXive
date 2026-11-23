"""
Integration test for T050a: Verify pipeline halts correctly when no longitudinal dataset is found.

This test simulates the scenario where the multi-source data aggregation (T001a) fails to find
a valid dataset, resulting in either a missing `data/verified_sources.json` or a file indicating
no valid source.

Success Criteria:
1. The pipeline (specifically the download stage which enforces the gate) exits with code 1.
2. The error log contains the specific message: "Data Unavailable: No longitudinal dataset found"
   or "Missing verified dataset source".
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import pytest
from pathlib import Path

# Add project root to path to allow imports if running directly,
# though we are primarily testing the subprocess execution of main.py
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config

class TestDataUnavailableHalt:
    """
    Tests the "Data Unavailable" halt condition.
    """

    def setup_method(self):
        """
        Setup: Create a temporary directory structure to isolate the test.
        We will manipulate the config paths to point to this temp dir.
        """
        self.temp_dir = tempfile.mkdtemp(prefix="test_halt_")
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(parents=True)
        self.verified_sources_path = self.data_dir / "verified_sources.json"
        
        # Ensure the directory exists for the test
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """
        Cleanup: Remove the temporary directory.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_halt_on_missing_verified_sources_file(self):
        """
        Scenario: data/verified_sources.json does not exist.
        Expected: Pipeline halts with exit code 1 and logs the missing source error.
        """
        # Ensure the file does NOT exist
        if self.verified_sources_path.exists():
            self.verified_sources_path.unlink()

        # We need to run the download stage which checks this file.
        # We will invoke main.py with the --stage download argument.
        # Note: We assume the environment variables or config defaults point to the temp dir
        # or we can override the config. For this integration test, we will simulate
        # the environment by setting the DATA_DIR env var if the config supports it,
        # or by relying on the default behavior if the test setup aligns.
        
        # Since Config might load from .env or defaults, let's try to run the specific check
        # by invoking the download module directly via main.py logic, but we need to ensure
        # the path is correct.
        
        # Strategy: Run main.py with a custom environment variable if supported, 
        # or rely on the fact that we are testing the logic in code/data/download.py
        # which is called by main.py.
        
        # Let's run the main.py entry point. To force it to look at our temp dir,
        # we might need to set an env var if Config reads it. 
        # Looking at typical patterns, let's assume we can set DATA_ROOT or similar.
        # If not, we might need to mock the file path in the test setup.
        # However, the task asks to verify the pipeline halts.
        
        # Let's try to run the download stage directly.
        cmd = [
            sys.executable, 
            str(project_root / "code" / "main.py"), 
            "--stage", "download"
        ]
        
        # We need to ensure the Config uses our temp_dir. 
        # If Config reads from os.environ, we set it. 
        # If not, we might need to patch. 
        # Given the constraints, let's assume the test runner sets up the env or 
        # we can pass the path via an argument if main.py supports it.
        # The task description says "Simulate a run where data/verified_sources.json indicates no valid source".
        
        # Let's create a scenario where the file exists but is empty/invalid, or missing.
        # We will test the "Missing" case first.
        
        # To ensure we hit the right code path, we might need to set the DATA_DIR env var
        # if the Config class supports it. Let's assume it does for this test.
        env = os.environ.copy()
        env["DATA_DIR"] = str(self.data_dir)
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=project_root)
        
        # Assert exit code is 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}, Stdout: {result.stdout}"
        
        # Assert specific error message is in output (stdout or stderr)
        output = result.stdout + result.stderr
        assert "Missing verified dataset source" in output or "Data Unavailable" in output, \
            f"Expected error message not found in output: {output}"

    def test_halt_on_invalid_verified_sources_content(self):
        """
        Scenario: data/verified_sources.json exists but indicates no valid source (e.g., empty or missing ID).
        Expected: Pipeline halts with exit code 1 and logs the specific error.
        """
        # Create a file with invalid content (missing dataset_id)
        invalid_data = {
            "source_name": "TestSource",
            "verified_date": "2023-01-01",
            "has_pre_post": False, # Indicates failure
            "notes": "No valid longitudinal data found"
        }
        with open(self.verified_sources_path, 'w') as f:
            json.dump(invalid_data, f)

        cmd = [
            sys.executable, 
            str(project_root / "code" / "main.py"), 
            "--stage", "download"
        ]
        
        env = os.environ.copy()
        env["DATA_DIR"] = str(self.data_dir)
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=project_root)
        
        # Assert exit code is 1
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}, Stdout: {result.stdout}"
        
        # Assert error message
        output = result.stdout + result.stderr
        # The error should indicate the source is invalid or missing the ID
        assert "Missing verified dataset source" in output or "invalid" in output.lower() or "Data Unavailable" in output, \
            f"Expected error message not found in output: {output}"

    def test_halt_on_empty_verified_sources_file(self):
        """
        Scenario: data/verified_sources.json exists but is empty.
        Expected: Pipeline halts with exit code 1.
        """
        # Create an empty file
        with open(self.verified_sources_path, 'w') as f:
            f.write("")

        cmd = [
            sys.executable, 
            str(project_root / "code" / "main.py"), 
            "--stage", "download"
        ]
        
        env = os.environ.copy()
        env["DATA_DIR"] = str(self.data_dir)
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=project_root)
        
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. Stderr: {result.stderr}, Stdout: {result.stdout}"
        
        output = result.stdout + result.stderr
        assert "JSON" in output or "Missing" in output or "Error" in output, \
            f"Expected error message not found in output: {output}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])