import pytest
import time
import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path

# Ensure the code directory is in the path for imports if running directly
# though pytest usually handles this via conftest or sys.path manipulation
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

class TestPerformanceVerification:
    """
    Performance verification for T039.
    Runs the CLI with N=10,000 synthetic records and verifies exit time < 600s.
    Constraints: 2-core CPU, 7GB RAM (simulated via resource limits if available, 
    but primarily verified by wall-clock time).
    """

    def test_synthetic_generation_performance(self):
        """
        Verify that generating and processing 10,000 synthetic records
        completes within 600 seconds (10 minutes) wall-clock time.
        """
        # Create a temporary directory for the output to avoid cluttering the repo
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            output_file = output_dir / "performance_test_output.json"
            
            # Construct the command
            # We use the main entry point directly via python -m or the script
            # Assuming the CLI is runnable as: python -m src.cli ...
            cmd = [
                sys.executable, "-m", "src.cli",
                "--mode", "synthetic",
                "--n_samples", "10000",
                "--output", str(output_file),
                "--seed", "42"
            ]

            start_time = time.time()
            
            try:
                # Run the command
                result = subprocess.run(
                    cmd,
                    cwd=code_root,
                    capture_output=True,
                    text=True,
                    timeout=600  # Hard timeout at 10 minutes
                )
            except subprocess.TimeoutExpired:
                pytest.fail("Process timed out after 600 seconds. Performance requirement failed.")
            
            end_time = time.time()
            elapsed = end_time - start_time

            # Check exit code
            if result.returncode != 0:
                pytest.fail(
                    f"CLI exited with code {result.returncode}.\n"
                    f"Stdout: {result.stdout}\n"
                    f"Stderr: {result.stderr}"
                )

            # Verify the output file exists
            if not output_file.exists():
                pytest.fail(f"Output file {output_file} was not created.")

            # Verify the elapsed time
            assert elapsed < 600, (
                f"Performance requirement failed. "
                f"Execution took {elapsed:.2f} seconds, which exceeds the 600s limit."
            )

            # Log the result for verification
            print(f"Performance Test PASSED: {elapsed:.2f} seconds for N=10,000 records.")
            
            # Optional: Verify the output content is valid JSON and contains expected keys
            try:
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    # Basic sanity check that we got a result
                    assert 'analysis' in data or 'results' in data, "Output JSON missing expected keys."
            except json.JSONDecodeError:
                pytest.fail("Output file is not valid JSON.")

    def test_resource_usage_heuristic(self):
        """
        A heuristic check to ensure we aren't spawning excessive processes 
        or doing something obviously inefficient that would blow up on 2-core/7GB.
        This is a soft check compared to the hard timing test.
        """
        # This test primarily ensures the script runs without crashing due to 
        # memory errors (OOM) or spawning too many threads.
        # If it completes the timing test, it passes this implicitly, 
        # but we run it separately to ensure the code path is clean.
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "check.json"
            cmd = [
                sys.executable, "-m", "src.cli",
                "--mode", "synthetic",
                "--n_samples", "10000",
                "--output", str(output_file),
                "--seed", "123"
            ]
            
            # Run without timeout for the heuristic check, but catch OOM
            try:
                result = subprocess.run(
                    cmd,
                    cwd=code_root,
                    capture_output=True,
                    text=True,
                    timeout=300 # Shorter timeout for sanity check
                )
                assert result.returncode == 0, f"Failed during heuristic check: {result.stderr}"
            except subprocess.TimeoutExpired:
                pytest.fail("Heuristic check timed out unexpectedly.")
            except MemoryError:
                pytest.fail("MemoryError detected during execution.")