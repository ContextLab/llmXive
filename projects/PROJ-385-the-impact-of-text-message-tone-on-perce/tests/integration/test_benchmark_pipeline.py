"""
Integration test for T037: Benchmark pipeline duration.
Verifies that the pipeline runs within the SC-005 constraint (6 hours = 21600 seconds).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import get_processed_data_dir

class TestBenchmarkPipeline:
    """Test suite for T037 benchmark execution."""

    def test_pipeline_benchmark_execution(self):
        """
        Run the pipeline with --benchmark flag and verify:
        1. data/processed/benchmark.json is created.
        2. It contains total_duration_seconds, per_stage_duration.
        3. The assertion total_duration < 21600 is True.
        """
        # Ensure the benchmark file does not exist from previous runs
        benchmark_file = get_processed_data_dir() / "benchmark.json"
        if benchmark_file.exists():
            benchmark_file.unlink()

        # Run the pipeline with benchmark flag
        # We run it as a subprocess to ensure it's a clean execution
        # Assuming the script is run from the project root
        project_root = Path(__file__).parent.parent.parent
        cmd = [
            sys.executable,
            str(code_dir / "run_pipeline.py"),
            "--benchmark"
        ]

        # Execute the command
        # Note: If the pipeline takes too long or fails, this might raise CalledProcessError
        # We expect it to succeed if the data generation and analysis are fast enough.
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=21600 + 60  # Add buffer to the 6-hour limit
            )
            
            # Check if the benchmark file was created
            assert benchmark_file.exists(), "Benchmark output file was not created."

            # Load and verify the content
            with open(benchmark_file, 'r') as f:
                data = json.load(f)

            # Verify required keys
            assert "total_duration_seconds" in data, "Missing total_duration_seconds"
            assert "per_stage_duration" in data, "Missing per_stage_duration"
            assert "assertion_sc_005" in data, "Missing assertion_sc_005"

            # Verify the assertion
            assert data["assertion_sc_005"] is True, (
                f"Benchmark failed SC-005 constraint. "
                f"Duration: {data['total_duration_seconds']}s, Limit: {data['sc_005_limit_seconds']}s"
            )

            # Verify the duration is actually less than the limit
            assert data["total_duration_seconds"] < data["sc_005_limit_seconds"], (
                "Total duration exceeds SC-005 limit."
            )

        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution timed out (exceeded SC-005 limit).")
        except subprocess.CalledProcessError as e:
            # If the pipeline exits with non-zero, it might be due to the benchmark assertion
            # But we already checked the file content. If the file says pass, then the exit code
            # might be due to a stage failure.
            # However, our implementation exits with 1 if benchmark fails.
            # If the file exists and says pass, then the exit code should be 0.
            # If the file exists and says fail, then exit code is 1.
            # We already assert the file says pass.
            # So if we get here, it means the file was created but the script exited with error.
            # This might happen if a stage failed but the benchmark file was still written.
            # Let's check the file content again.
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    data = json.load(f)
                if data.get("assertion_sc_005"):
                    # The benchmark passed, but the script exited with error.
                    # This might be due to a stage failure that didn't stop the benchmark write.
                    # We should check the success flag.
                    if data.get("success"):
                        pytest.fail(f"Pipeline exited with error code {e.returncode} but benchmark passed. Check logs.")
                    else:
                        pytest.fail(f"Pipeline stages failed. Benchmark passed time constraint but stages failed.")
                else:
                    pytest.fail(f"Pipeline exited with error code {e.returncode} and benchmark failed.")
            else:
                pytest.fail(f"Pipeline exited with error code {e.returncode} and no benchmark file created.")
        except Exception as e:
            pytest.fail(f"Unexpected error during benchmark execution: {e}")

    def test_benchmark_structure(self):
        """
        Verify the structure of the benchmark.json file if it exists.
        This test can run independently if the benchmark was already run.
        """
        benchmark_file = get_processed_data_dir() / "benchmark.json"
        if not benchmark_file.exists():
            pytest.skip("Benchmark file not found. Run the pipeline with --benchmark first.")

        with open(benchmark_file, 'r') as f:
            data = json.load(f)

        # Check keys
        assert "total_duration_seconds" in data
        assert "per_stage_duration" in data
        assert isinstance(data["per_stage_duration"], dict)
        assert "total" in data["per_stage_duration"]
        assert "assertion_sc_005" in data
        assert isinstance(data["assertion_sc_005"], bool)
        assert "sc_005_limit_seconds" in data
        assert data["sc_005_limit_seconds"] == 21600