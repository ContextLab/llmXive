"""
Basic test to ensure the download script runs without raising an exception
and produces the expected output files (parquet and sample_sizes.csv).
The test is deliberately lightweight – it does not assert on the exact
number of isolates because that depends on the live NCBI dataset.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_download_script_runs():
    # Execute the module as a script
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline.download"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    # The script should exit with status 0
    assert result.returncode == 0, f"Download script failed: {result.stderr}"

    # Verify that the parquet file exists
    parquet_file = paths.data("raw", "ncbi_parquet", "isolates.parquet")
    assert parquet_file.is_file(), f"Missing parquet file at {parquet_file}"

    # Verify that the sample size CSV exists
    sample_sizes = paths.results("sample_sizes.csv")
    assert sample_sizes.is_file(), f"Missing sample sizes CSV at {sample_sizes}"