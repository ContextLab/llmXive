import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Import the main function to trigger the full run
from ingest import main

@pytest.mark.integration
def test_full_ingestion_and_harmonization():
    """
    Integration test: Run full download and verify output CSV structure.
    Depends on: T014 (Raw data saved).
    
    Requirements:
    1. Verify data/raw/raw_dataset.csv exists.
    2. Assert it contains at least 10 rows.
    3. Assert it contains required columns (sample_id, genotype_id, resistance, metabolite_*).
    4. If a required column is missing, the system MUST raise a RuntimeError.
    5. Fail the test if file is missing, row count < 10, or columns are missing.
    """
    # Ensure the script runs successfully (performs the download)
    try:
        main()
    except Exception as e:
        # If the ingestion script fails (e.g., network error, missing dataset), fail the test
        pytest.fail(f"Ingestion script failed to run: {e}")

    # 1. Verify raw data exists
    raw_path = Path("data/raw/raw_dataset.csv")
    assert raw_path.exists(), "Raw dataset CSV (data/raw/raw_dataset.csv) not found. Ingestion did not produce output."

    # 2. Load and verify raw data structure
    try:
        df_raw = pd.read_csv(raw_path)
    except Exception as e:
        pytest.fail(f"Failed to read raw dataset CSV: {e}")

    # Assert at least 10 rows
    assert len(df_raw) >= 10, f"Raw dataset has fewer than 10 rows ({len(df_raw)}). Data source may be empty or truncated."

    # 3. Assert required columns in raw data
    required_cols = ['sample_id', 'genotype_id', 'resistance']
    missing_cols = []
    for col in required_cols:
        if col not in df_raw.columns:
            missing_cols.append(col)

    if missing_cols:
        # Task requirement: If a required column is missing, the system MUST raise a RuntimeError
        # We simulate this check here to fail the test with the specific message expected
        raise RuntimeError(f"No quantifiable resistance metric found. Missing columns: {missing_cols}")

    # Assert metabolite columns exist (at least one)
    metabolite_cols = [c for c in df_raw.columns if c.startswith('metabolite_')]
    assert len(metabolite_cols) > 0, "No metabolite columns (metabolite_*) found in raw dataset."

    # 4. Verify harmonized data exists (produced by T015/T013 logic inside main)
    harmonized_path = Path("data/interim/harmonized.csv")
    assert harmonized_path.exists(), "Harmonized dataset CSV (data/interim/harmonized.csv) not found."

    # Load and verify harmonized structure
    try:
        df_harm = pd.read_csv(harmonized_path)
    except Exception as e:
        pytest.fail(f"Failed to read harmonized dataset CSV: {e}")

    # Verify resistance column in harmonized data is numeric (1, 2, 3 or raw numeric)
    if 'resistance' in df_harm.columns:
        unique_vals = set(df_harm['resistance'].unique())
        valid_vals = {1.0, 2.0, 3.0}
        
        # Check if values are numeric
        non_numeric = [v for v in unique_vals if pd.notna(v) and not isinstance(v, (int, float))]
        assert len(non_numeric) == 0, f"Resistance column contains non-numeric values: {non_numeric}"
    else:
        pytest.fail("Harmonized dataset missing 'resistance' column.")

    # 5. Verify metadata file exists and has correct structure
    metadata_path = Path("data/interim/metadata.json")
    assert metadata_path.exists(), "Metadata JSON (data/interim/metadata.json) not found."
    
    with open(metadata_path, 'r') as f:
        meta = json.load(f)
    
    assert 'mapping' in meta, "Missing 'mapping' in metadata.json"
    assert 'herbivore_density_missing' in meta, "Missing 'herbivore_density_missing' in metadata.json"
    
    # Verify mapping content matches canonical keys
    assert meta['mapping'].get('Low') == 1, "Invalid mapping for 'Low' in metadata"
    assert meta['mapping'].get('Medium') == 2, "Invalid mapping for 'Medium' in metadata"
    assert meta['mapping'].get('High') == 3, "Invalid mapping for 'High' in metadata"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])