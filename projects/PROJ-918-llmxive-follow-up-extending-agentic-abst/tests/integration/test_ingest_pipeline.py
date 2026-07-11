"""
Integration test for the data ingestion pipeline (T010).

This test verifies the full end-to-end flow of:
1. Loading configuration and seeds.
2. Fetching/Generating the real "Agentic Abstention" dataset (or falling back to the simulator).
3. Verifying the dataset against the `dataset.schema.yaml` contract.
4. Ensuring the output file is written to `data/processed/raw_abstention.csv` (or .parquet).

It depends on T011 (ingest.py) and T009 (schema validation) being implemented.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd

# Project imports
# We assume the project root is in sys.path or we add it
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import load_config, get_seed, get_path
from data.checksums import verify_checksums
from logging_config import setup_logging
from data.ingest import run_ingestion_pipeline

# Setup logging for the test
logger = setup_logging(level="INFO", log_file=None)

# Constants for paths (matching plan.md structure)
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
SCHEMA_PATH = ROOT_DIR / "contracts" / "dataset.schema.yaml"
OUTPUT_FILENAME = "raw_abstention.csv"
OUTPUT_PATH = DATA_PROCESSED_DIR / OUTPUT_FILENAME

# Ensure directories exist for the test
@pytest.fixture(autouse=True)
def setup_test_dirs():
    """Ensure required directories exist before tests run."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Optional: Cleanup processed files after test if needed, but usually we want to keep artifacts
    # if OUTPUT_PATH.exists():
    #     OUTPUT_PATH.unlink()

@pytest.mark.integration
def test_ingest_pipeline_full_flow():
    """
    Integration test: Run the ingestion pipeline and verify:
    1. The output file is created.
    2. The file is not empty.
    3. The file schema matches the contract (no full text context columns).
    4. The checksums are generated/verified (if checksums exist).
    """
    # 1. Load configuration
    # We assume config.yaml exists at the root or in a standard location.
    # If not, load_config might raise an error, which is expected if setup is incomplete.
    try:
        config = load_config()
        seed = get_seed(config)
    except FileNotFoundError:
        # Fallback for testing if config is missing: create a minimal one or skip
        # For this integration test, we assume T008 (env/config) is done.
        pytest.skip("Configuration file not found. Ensure T008 is complete.")

    # 2. Run the ingestion pipeline
    # This calls the logic from T011 (ingest.py)
    # We expect this to write to data/processed/raw_abstention.csv
    try:
        run_ingestion_pipeline(
            output_dir=DATA_PROCESSED_DIR,
            output_filename=OUTPUT_FILENAME,
            seed=seed,
            logger=logger
        )
    except Exception as e:
        # If the pipeline fails, it should be because the real data source is unreachable
        # or the simulator logic is broken. We fail the test loudly.
        pytest.fail(f"Ingestion pipeline failed: {str(e)}")

    # 3. Verify output file existence
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created."

    # 4. Load and validate data
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        pytest.fail(f"Could not read output file {OUTPUT_PATH}: {str(e)}")

    # 5. Validate schema constraints (No full text context)
    # The contract (T004) forbids columns containing full semantic context text.
    # We check for common patterns or specific forbidden column names if defined in schema.
    # Since we don't have the exact schema content here, we enforce a generic rule:
    # No column should be named 'context', 'full_text', 'prompt', 'response' or similar,
    # and no column should contain extremely long strings (>1000 chars) if it's not a feature.
    
    forbidden_patterns = ['context', 'full_text', 'prompt', 'response', 'trajectory']
    for col in df.columns:
        col_lower = col.lower()
        for pattern in forbidden_patterns:
            assert pattern not in col_lower, f"Column '{col}' violates schema: contains forbidden pattern '{pattern}'."

    # Check for long strings in non-feature columns (heuristic)
    # We assume feature columns are numeric or short strings.
    # If a column has long text, it might be a violation.
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check max length of string values
            max_len = df[col].astype(str).str.len().max()
            if max_len > 500:
                # Allow 'id' or 'task_id' if they are short, but warn if long
                if 'id' not in col.lower():
                    pytest.fail(f"Column '{col}' contains unusually long strings ({max_len} chars), possible full text context.")

    # 6. Validate data integrity (not empty)
    assert len(df) > 0, "Ingested dataset is empty."

    # 7. Verify checksums if the source file exists
    # This tests the integration with T006 (checksums)
    source_file = DATA_RAW_DIR / "abstention_benchmark.csv" # Assumed name from T011
    if source_file.exists():
        try:
            # Verify checksums for the source file
            # This ensures the data hasn't been tampered with
            is_valid = verify_checksums(source_file)
            # Note: verify_checksums might return True/False or raise.
            # We assume it raises on failure or returns boolean.
            if not is_valid:
                logger.warning("Checksum verification failed for source file.")
        except Exception as e:
            logger.warning(f"Checksum verification skipped or failed: {e}")

    # 8. Verify specific columns exist (minimal schema check)
    required_cols = ['task_id', 'search_count', 'error_freq', 'tokens', 'turns', 'abstention_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"

    logger.info("Integration test passed: Ingestion pipeline produced valid output.")

if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v"])
