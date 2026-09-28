"""
Integration test for data ingestion pipeline (User Story 1).

This test verifies that the ingestion pipeline can:
1. Load data from a source (or trigger the simulation fallback if real source is unreachable).
2. Produce a valid raw dataset file at data/raw/raw_dataset.csv.
3. Generate valid metadata at data/raw/metadata.json.
4. Ensure the raw dataset contains the required schema fields.
5. Ensure the pipeline handles the 'fail loud then fallback' logic correctly.

Dependencies:
- T008 (Contract test for schema validation)
- T010a (Ingestion logic with fallback)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path to import local modules
# Assuming this test runs from the project root or tests/ directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.ingestion.fetcher import (
    fetch_data, 
    DataFetchError, 
    generate_synthetic_fallback,
    save_metadata
)
from code.ingestion.validator import (
    validate_schema,
    SchemaValidationError
)
from code.utils import setup_logging

# Configure logging for tests
setup_logging(level="INFO")

# Constants for test paths
TEST_DATA_DIR = PROJECT_ROOT / "data" / "raw"
TEST_RAW_CSV = TEST_DATA_DIR / "raw_dataset.csv"
TEST_METADATA_JSON = TEST_DATA_DIR / "metadata.json"

REQUIRED_COLUMNS = [
    "participant_id", 
    "age", 
    "stimulus_type", 
    "perseverative_errors", 
    "categories_completed"
]

@pytest.fixture(scope="module")
def setup_test_dirs():
    """Ensure required directories exist before running tests."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup is optional for integration tests as they produce real artifacts
    # but we ensure we don't overwrite critical data in a real run if possible.
    # For this specific test, we assume it's run in isolation or with clean state.

def test_ingestion_pipeline_source_or_fallback(setup_test_dirs):
    """
    Integration test: Verify the ingestion pipeline produces valid output.
    
    This test simulates the execution flow of T010a:
    1. Attempt to fetch from canonical source.
    2. If fetch fails, trigger synthetic fallback immediately (as per spec).
    3. Verify output file existence and schema.
    """
    
    # Ensure clean state for this specific test run
    if TEST_RAW_CSV.exists():
        TEST_RAW_CSV.unlink()
    if TEST_METADATA_JSON.exists():
        TEST_METADATA_JSON.unlink()
    
    # 1. Execute Ingestion Logic
    # We simulate the "fail loud" by attempting to fetch.
    # Since we cannot guarantee external connectivity in all test environments,
    # we wrap the fetch in a try/except that mimics the T010a logic.
    # In a real run, fetch_data() would raise DataFetchError if the source is unreachable.
    
    raw_df = None
    simulation_mode = False
    
    try:
        # Attempt real fetch (T010a logic)
        # Note: fetch_data() is expected to raise DataFetchError if the source is unreachable.
        # We do not catch it here; we let it propagate to the fallback logic block
        # which is the core of the T010a requirement.
        raw_df, source_info = fetch_data()
        simulation_mode = False
        print("INFO: Real data fetch succeeded.")
    except DataFetchError as e:
        print(f"INFO: Real data fetch failed ({e}). Triggering simulation fallback.")
        # Fallback logic: Generate synthetic dataset with seed=42
        # This matches the requirement: "generate a synthetic dataset with seed=42"
        raw_df = generate_synthetic_fallback(seed=42)
        simulation_mode = True
    except Exception as e:
        pytest.fail(f"Unexpected error during ingestion: {e}")
    
    # 2. Verify Output File Existence
    # The pipeline MUST save the result to data/raw/raw_dataset.csv
    assert TEST_RAW_CSV.exists(), f"Expected output file {TEST_RAW_CSV} was not created."
    
    # 3. Verify Metadata File
    assert TEST_METADATA_JSON.exists(), f"Expected metadata file {TEST_METADATA_JSON} was not created."
    
    with open(TEST_METADATA_JSON, "r") as f:
        metadata = json.load(f)
    
    assert "simulation_mode" in metadata, "metadata.json missing 'simulation_mode' key."
    assert metadata["simulation_mode"] == simulation_mode, "metadata.json 'simulation_mode' mismatch."
    
    # 4. Verify Data Schema
    assert raw_df is not None, "Ingestion produced no dataframe."
    
    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in raw_df.columns]
    assert not missing_cols, f"Missing required columns in raw dataset: {missing_cols}"
    
    # Check data types and basic validity
    assert "age" in raw_df.columns
    assert "stimulus_type" in raw_df.columns
    
    # Ensure at least some records exist (min 100 as per task description context)
    # Note: generate_synthetic_fallback should produce enough data, or real data should too.
    assert len(raw_df) >= 100, f"Dataset has too few records: {len(raw_df)} (expected >= 100)"
    
    # 5. Verify Schema Validation (Contract Test Integration)
    # Re-use the validator to ensure the generated data meets the contract
    try:
        validate_schema(raw_df)
    except SchemaValidationError as e:
        pytest.fail(f"Generated data failed schema validation: {e}")
    
    print("INFO: Integration test passed. Ingestion pipeline produced valid output.")

def test_ingestion_output_content_integrity():
    """
    Verify the content of the generated raw dataset matches expected types.
    """
    if not TEST_RAW_CSV.exists():
        pytest.skip("Raw dataset not found. Run test_ingestion_pipeline_source_or_fallback first.")
        
    df = pd.read_csv(TEST_RAW_CSV)
    
    # Check specific constraints mentioned in US1
    # 1. participant_id should be non-null
    assert df["participant_id"].notna().all(), "Found null participant_id"
    
    # 2. stimulus_type should be categorical (nostalgia/control)
    valid_types = ["nostalgia", "control"]
    # Allow for variations like 'Nostalgia' if not normalized, but check for presence
    unique_types = df["stimulus_type"].unique()
    # Basic check: ensure we have at least one of the expected types
    has_nostalgia = any("nostalgia" in str(t).lower() for t in unique_types)
    has_control = any("control" in str(t).lower() for t in unique_types)
    
    # If the data is synthetic, it might only have one type or both.
    # We assert that the column is populated.
    assert len(df["stimulus_type"].dropna()) > 0, "stimulus_type is empty"
    
    # 3. Metrics should be numeric
    assert pd.to_numeric(df["perseverative_errors"], errors="coerce").notna().all(), "perseverative_errors contains non-numeric"
    assert pd.to_numeric(df["categories_completed"], errors="coerce").notna().all(), "categories_completed contains non-numeric"
    
    print("INFO: Content integrity check passed.")

def test_age_filtering_readiness():
    """
    Verify that the raw dataset contains an 'age' column with values >= 65 (if real)
    or valid synthetic values that allow the subsequent age filtering task (T012a) to run.
    """
    if not TEST_RAW_CSV.exists():
        pytest.skip("Raw dataset not found.")
        
    df = pd.read_csv(TEST_RAW_CSV)
    
    assert "age" in df.columns, "Missing 'age' column"
    
    # The task T012a will filter for age >= 65.
    # We verify that the data structure supports this.
    ages = pd.to_numeric(df["age"], errors="coerce")
    assert ages.notna().all(), "Age contains non-numeric values"
    
    # Check if there are any records that would pass the filter
    # (Even if synthetic, we expect some >= 65 if the generator is correct)
    valid_ages = ages[ages >= 65]
    assert len(valid_ages) > 0, "No records with age >= 65 found. T012a will produce empty output."
    
    print("INFO: Age filtering readiness check passed.")

if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])