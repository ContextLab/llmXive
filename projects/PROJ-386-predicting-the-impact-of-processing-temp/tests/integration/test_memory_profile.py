"""
Integration test for memory profiling of the full pipeline.
Verifies that the pipeline runs within the 6.5 GB RAM limit on ubuntu-latest.
"""
import os
import sys
import subprocess
import re
import tempfile
import json
from pathlib import Path

import pytest

# Constants
MAX_MEMORY_GB = 6.5
SAMPLE_SIZE = 100
TIMEOUT_SECONDS = 3600  # 1 hour for the test run

def run_memory_profile():
    """
    Run the main pipeline with memory profiling enabled.
    Returns the parsed memory usage log or raises an error.
    """
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    os.chdir(project_root)

    # Construct the command
    # We use a temporary file to capture the memory profiler output
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_file:
        output_file = tmp_file.name

    try:
        # Run: python -m memory_profiler code/main.py --sample-size 100 --timeout 3600
        cmd = [
            sys.executable, "-m", "memory_profiler",
            "--include-children",
            "--multiprocess",
            "-o", output_file,
            "-v",
            "code/main.py",
            "--sample-size", str(SAMPLE_SIZE),
            "--timeout", str(TIMEOUT_SECONDS)
        ]

        # Execute with a longer timeout for the test itself
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS + 60,  # Extra buffer
            env={**os.environ, "PYTHONHASHSEED": "42"}
        )

        # If the main script failed, raise that error
        if result.returncode != 0:
            error_msg = f"Pipeline execution failed with code {result.returncode}.\n"
            if result.stdout:
                error_msg += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                error_msg += f"STDERR:\n{result.stderr}\n"
            raise RuntimeError(error_msg)

        # Parse the memory profiler output
        max_rss_mb = 0
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                content = f.read()
                # Look for "Maximum RSS" in the output
                # memory-profiler usually prints "Maximum RSS: XXXX MiB"
                match = re.search(r"Maximum RSS:\s*(\d+(?:\.\d+)?)\s*(?:MiB|MB)", content, re.IGNORECASE)
                if match:
                    max_rss_mb = float(match.group(1))
                else:
                    # Fallback: try to parse line by line for peak memory if specific tag missing
                    lines = content.split('\n')
                    for line in lines:
                        if 'MiB' in line or 'MB' in line:
                            # Try to extract number
                            nums = re.findall(r'\d+(?:\.\d+)?', line)
                            if nums:
                                val = float(nums[-1])
                                if val > max_rss_mb:
                                    max_rss_mb = val

        return max_rss_mb

    finally:
        # Cleanup temp file
        if os.path.exists(output_file):
            os.remove(output_file)

@pytest.mark.integration
def test_memory_usage_within_limit():
    """
    Test that the full pipeline execution does not exceed 6.5 GB RAM.
    """
    max_memory_mb = run_memory_profile()
    max_memory_gb = max_memory_mb / 1024.0

    print(f"Maximum RSS observed: {max_memory_gb:.2f} GB ({max_memory_mb:.2f} MB)")

    assert max_memory_gb <= MAX_MEMORY_GB, (
        f"Memory limit exceeded! "
        f"Observed: {max_memory_gb:.2f} GB, Limit: {MAX_MEMORY_GB} GB"
    )
