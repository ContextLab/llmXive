"""
Integration test for memory-constrained preprocessing (US1).

This test verifies that the dataset ingestion and preprocessing pipeline
operates within the 7GB RAM constraint while producing a valid corpus
of at least 200 Python-to-JavaScript pairs.

It downloads a subset of the real dataset, processes it in chunks,
and validates the output file and memory usage.
"""
import os
import sys
import tempfile
import gc
import resource
import time
import pytest
from pathlib import Path

# Add project root to path to import src modules
# Assuming this test runs from project root or is invoked via pytest with correct cwd
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.ingestion.download_datasets import fetch_and_process_corpus
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MIN_ENTRIES = 200
MAX_MEMORY_GB = 7.0
MEMORY_TOLERANCE_GB = 0.5  # Allow some buffer for OS/Python overhead in test env
TEST_TIMEOUT_SECONDS = 300  # 5 minutes for download + processing

@pytest.mark.integration
@pytest.mark.timeout(TEST_TIMEOUT_SECONDS)
def test_memory_constrained_preprocessing():
    """
    Integration test: Verify that preprocessing the dataset stays within memory limits
    and produces a valid CSV with >= 200 entries.
    """
    # Setup temporary directories for this test run
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "data" / "raw"
        processed_dir = Path(tmp_dir) / "data" / "processed"
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        output_csv_path = processed_dir / "corpus.csv"

        # Record initial memory state
        gc.collect()
        time.sleep(0.5)
        initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ru_maxrss is in KB on Linux/macOS
        initial_memory_gb = initial_memory / (1024 * 1024)
        
        logger.info(f"Starting memory usage: {initial_memory_gb:.2f} GB")

        # Execute the preprocessing pipeline
        # This function is expected to download, cache, validate, and chunk-process
        # the data to stay within memory limits.
        try:
            result = fetch_and_process_corpus(
                raw_dir=str(raw_dir),
                processed_dir=str(processed_dir),
                output_filename="corpus.csv",
                min_entries=MIN_ENTRIES,
                max_memory_gb=MAX_MEMORY_GB
            )
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise

        # Force garbage collection before final measurement
        gc.collect()
        time.sleep(0.5)
        
        final_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        final_memory_gb = final_memory / (1024 * 1024)
        peak_memory_gb = max(initial_memory_gb, final_memory_gb)

        logger.info(f"Peak memory usage during test: {peak_memory_gb:.2f} GB")
        logger.info(f"Output file created: {output_csv_path}")

        # Assertions
        
        # 1. Verify output file exists
        assert output_csv_path.exists(), f"Output file {output_csv_path} was not created."

        # 2. Verify entry count
        # Read the CSV to count lines (excluding header)
        with open(output_csv_path, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f) - 1 # Subtract header

        assert line_count >= MIN_ENTRIES, (
            f"Corpus contains {line_count} entries, "
            f"which is less than the required minimum of {MIN_ENTRIES}."
        )
        logger.info(f"Validated corpus contains {line_count} entries (>= {MIN_ENTRIES}).")

        # 3. Verify memory constraint
        # Note: resource.getrusage ru_maxrss is the peak resident set size of the process.
        # We check if the peak observed during the test (approximated by final maxrss + buffer)
        # is within the limit. A more precise measurement would require a profiler,
        # but this is sufficient for an integration test constraint check.
        effective_limit = MAX_MEMORY_GB + MEMORY_TOLERANCE_GB
        
        # On macOS, ru_maxrss is in bytes, on Linux in KB. 
        # The standard Python resource module behavior varies by platform.
        # Assuming Linux environment (common for CI) where it is KB.
        # If running on macOS, we'd need to adjust, but 7GB is 7*1024*1024 KB.
        # Let's assume standard Linux CI behavior.
        
        if sys.platform == 'darwin':
            # macOS returns bytes
            peak_memory_gb = peak_memory_gb / 1024 / 1024
        
        assert peak_memory_gb < effective_limit, (
            f"Peak memory usage {peak_memory_gb:.2f} GB exceeded limit of "
            f"{effective_limit:.2f} GB (limit {MAX_MEMORY_GB} GB + tolerance {MEMORY_TOLERANCE_GB} GB)."
        )
        
        logger.info(f"Memory constraint satisfied: {peak_memory_gb:.2f} GB < {effective_limit:.2f} GB")

        # 4. Verify basic data integrity (non-empty code columns)
        import pandas as pd
        df = pd.read_csv(output_csv_path)
        
        assert "python_code" in df.columns, "Missing 'python_code' column."
        assert "javascript_code" in df.columns, "Missing 'javascript_code' column."
        
        # Check for non-empty strings
        empty_py = df["python_code"].astype(str).str.strip() == ""
        empty_js = df["javascript_code"].astype(str).str.strip() == ""
        
        assert not empty_py.any(), "Found empty python_code entries."
        assert not empty_js.any(), "Found empty javascript_code entries."

        logger.info("All integration tests passed successfully.")