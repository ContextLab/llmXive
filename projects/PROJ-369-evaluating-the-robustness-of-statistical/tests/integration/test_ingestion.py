"""
Integration test for full ingestion pipeline on sample NOAA data.

This test verifies the end-to-end flow:
1. Real data fetch (NOAA ETOPO1 or similar public dataset) via `src/data/ingestion.py`
2. Missing value handling via `src/data/preprocessing.py`
3. Stationarity check (ADF) via `src/data/preprocessing.py`
4. Output validation (no missing values, stationarity status logged)

It strictly adheres to the "fail loudly" policy: if the real data fetch fails,
the test raises an error and does NOT fall back to synthetic data.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import from the project's source modules
from src.data.ingestion import load_noaa_etalon
from src.data.preprocessing import process_time_series
from src.utils.config import get_path, set_seed

# Set a fixed seed for any internal randomness in processing
set_seed(42)


@pytest.mark.integration
def test_full_ingestion_pipeline_noaa():
    """
    Integration test: Download real NOAA data, preprocess, and verify stationarity.
    """
    # 1. Setup: Define a temporary directory for intermediate artifacts if needed
    # The ingestion module should handle its own caching, but we ensure the data dir exists.
    data_root = get_path("data")
    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 2. Execute: Load REAL NOAA data
    # We use the 'load_noaa_etalon' function which is expected to fetch from a verified URL.
    # If this fetch fails (network error, 404, etc.), it MUST raise an exception.
    # We do not catch it here; the test fails loudly as required.
    try:
        df_raw = load_noaa_etalon()
    except Exception as e:
        pytest.fail(f"Failed to fetch real NOAA data: {e}")

    # 3. Precondition Check: Ensure we actually got data
    assert df_raw is not None, "Ingestion returned None"
    assert len(df_raw) > 0, "Ingestion returned empty dataframe"
    assert "value" in df_raw.columns or any("temp" in str(c).lower() for c in df_raw.columns), \
        "Dataframe missing expected value column"

    # 4. Process: Run the preprocessing pipeline
    # This includes missing value interpolation and stationarity checks (ADF).
    # The function should return the processed dataframe and a metadata dict.
    df_processed, metadata = process_time_series(df_raw, source="NOAA_ETOP")

    # 5. Assert: Verify Preprocessing Results
    # A. No missing values should remain
    assert df_processed.isnull().sum().sum() == 0, \
        "Preprocessing failed to remove all missing values"

    # B. Verify metadata contains stationarity info
    assert "stationarity" in metadata, "Metadata missing stationarity info"
    assert "adf_p_value" in metadata, "Metadata missing ADF p-value"
    assert "is_stationary" in metadata, "Metadata missing is_stationary flag"

    # C. Verify the processing logic actually ran (e.g., rows might differ if dropped)
    # We expect at least some data to remain after cleaning
    assert len(df_processed) > 10, "Too few data points remain after processing"

    # D. Log the results for verification
    print(f"Processed {len(df_processed)} rows.")
    print(f"ADF p-value: {metadata['adf_p_value']:.4f}")
    print(f"Is Stationary: {metadata['is_stationary']}")

    # E. Optional: Save the processed output to the data/processed directory
    # to satisfy the requirement that scripts produce real output files.
    processed_dir = get_path("data") / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "noaa_etop_processed.csv"
    df_processed.to_csv(output_path, index=False)
    print(f"Saved processed data to: {output_path}")
    
    # Verify the file was actually written
    assert output_path.exists(), "Output file was not written to disk"

if __name__ == "__main__":
    # Allow running directly for quick validation
    test_full_ingestion_pipeline_noaa()
    print("Integration test passed.")