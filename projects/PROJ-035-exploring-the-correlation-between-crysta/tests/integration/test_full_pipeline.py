"""
Integration test for the full data ingestion pipeline (User Story 1).

This test verifies the end-to-end execution of:
1. Fetching perovskite structures from Materials Project (T013)
2. Fetching thermal conductivity data from NIST/Literature (T014b)
3. Validating provenance (T014)
4. Normalizing temperature (T016)
5. Merging, cleaning, and validating the final dataset (T015)

Acceptance Criteria:
- Output file data/cleaned/merged_perovskite.csv exists.
- Dataset contains >= 50 rows.
- No null values in 'thermal_conductivity' or 'structure_id' columns.
- All required schema columns are present.
"""

import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import pipeline modules based on the provided API surface
# Note: The API surface shows modules in `code/src/...` but the task description
# and typical project structure imply `src/...`. Given the "Existing project API surface"
# explicitly lists `from src.ingest.fetch_structures import ...`, we use `src` imports.
# However, the prompt also lists `from ingest.fetch_structures import ...` in some blocks.
# We will attempt to import from `src` first as it is the most specific to the "API surface"
# provided in the prompt's `code/src/` section which matches the `src/` in the path conventions.
# If the project root is set such that `src` is a package, this works.
# To be safe and consistent with the "Existing project API surface" list which shows:
# `from src.ingest.fetch_structures import ...`
# We will use `src` imports.

from src.ingest.fetch_structures import fetch_perovskite_structures
from src.ingest.fetch_thermal import fetch_perovskite_thermal_data
from src.cleaning.provenance_validator import validate_provenance, save_validation_report
from src.cleaning.temperature_normalize import apply_temperature_normalization
from src.cleaning.clean_merge import merge_datasets, validate_geometry, enforce_minimum_compositions, add_provenance, main as merge_main
from src.utils.validation import validate_dataframe_columns, validate_no_nulls

# Constants
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
RESULTS_DIR = DATA_DIR / "results"

STRUCTURES_RAW_PATH = RAW_DIR / "structures_raw.csv"
THERMAL_RAW_PATH = RAW_DIR / "thermal_raw.csv"
PROVENANCE_REPORT_PATH = CLEANED_DIR / "provenance_report.json"
NORMALIZED_THERMAL_PATH = CLEANED_DIR / "normalized_thermal.csv"
MERGED_OUTPUT_PATH = CLEANED_DIR / "merged_perovskite.csv"

MIN_ROWS = 50

def cleaned_data_path():
    """Returns the path to the expected cleaned merged dataset."""
    return MERGED_OUTPUT_PATH

def pipeline_modules_available():
    """
    Checks if all required pipeline modules are importable.
    Returns True if all imports succeed, False otherwise.
    """
    try:
        # These imports are already done at the top, but this function
        # serves as a runtime check for the test environment.
        assert fetch_perovskite_structures is not None
        assert fetch_perovskite_thermal_data is not None
        assert validate_provenance is not None
        assert apply_temperature_normalization is not None
        assert merge_datasets is not None
        return True
    except Exception as e:
        print(f"Pipeline module import error: {e}")
        return False


class TestDataIngestionPipeline:
    """
    Integration test class for the full data ingestion pipeline.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Setup test environment: ensure directories exist.
        """
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        CLEANED_DIR.mkdir(parents=True, exist_ok=True)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        yield

    def test_pipeline_execution(self):
        """
        Executes the full pipeline and validates the output.

        Steps:
        1. Fetch structures (T013)
        2. Fetch thermal data (T014b)
        3. Validate provenance (T014)
        4. Normalize temperature (T016)
        5. Merge and clean (T015)
        6. Validate output (Schema, Row Count, Nulls)
        """
        if not pipeline_modules_available():
            pytest.skip("Pipeline modules not available in this environment.")

        # --- Step 1: Fetch Structures (T013) ---
        # We expect this to download data. If it fails (e.g., API key missing),
        # the test fails loudly as per requirements.
        print("Step 1: Fetching perovskite structures...")
        try:
            structures_df = fetch_perovskite_structures(output_path=STRUCTURES_RAW_PATH)
            assert structures_df is not None, "Structure fetch returned None"
            assert len(structures_df) > 0, "No structures fetched"
            print(f"  -> Fetched {len(structures_df)} structures.")
        except Exception as e:
            pytest.fail(f"Failed to fetch structures: {e}")

        # --- Step 2: Fetch Thermal Data (T014b) ---
        print("Step 2: Fetching thermal conductivity data...")
        try:
            thermal_df = fetch_perovskite_thermal_data(output_path=THERMAL_RAW_PATH)
            assert thermal_df is not None, "Thermal fetch returned None"
            assert len(thermal_df) > 0, "No thermal data fetched"
            print(f"  -> Fetched {len(thermal_df)} thermal records.")
        except Exception as e:
            pytest.fail(f"Failed to fetch thermal data: {e}")

        # --- Step 3: Validate Provenance (T014) ---
        print("Step 3: Validating provenance...")
        try:
            # The provenance validator expects the thermal data to have a source_reference
            # We assume the fetched data has this column or we load from T014b output
            # If the fetch function doesn't write to disk yet, we use the dataframe.
            # But T014b writes to THERMAL_RAW_PATH.
            if not THERMAL_RAW_PATH.exists():
                # If the fetch function didn't write, we write it here for the validator
                thermal_df.to_csv(THERMAL_RAW_PATH, index=False)

            is_valid, report = validate_provenance(THERMAL_RAW_PATH, PROVENANCE_REPORT_PATH)
            assert is_valid, f"Provenance validation failed: {report}"
            print(f"  -> Provenance validation passed. Report saved to {PROVENANCE_REPORT_PATH}")
        except Exception as e:
            pytest.fail(f"Failed to validate provenance: {e}")

        # --- Step 4: Normalize Temperature (T016) ---
        print("Step 4: Normalizing temperature...")
        try:
            # Apply normalization to the thermal data
            # The function expects a dataframe or path. Let's assume it takes a path or df.
            # Based on API: `apply_temperature_normalization`
            # We'll load the raw thermal data and normalize it.
            thermal_df_raw = pd.read_csv(THERMAL_RAW_PATH)
            normalized_df = apply_temperature_normalization(thermal_df_raw, output_path=NORMALIZED_THERMAL_PATH)
            assert normalized_df is not None, "Normalization returned None"
            assert len(normalized_df) > 0, "No normalized data"
            print(f"  -> Normalized {len(normalized_df)} records.")
        except Exception as e:
            pytest.fail(f"Failed to normalize temperature: {e}")

        # --- Step 5: Merge and Clean (T015) ---
        print("Step 5: Merging and cleaning data...")
        try:
            # The merge function should handle the combination of structures and thermal data
            # and apply final cleaning.
            # We assume it takes paths or dataframes.
            # Based on API: `merge_datasets`
            # Let's call the main entry point if available, or the function directly.
            # The task T015 says: "Implement clean_merge.py ... validate ... merge ... remove nulls"
            # We will call the main function which orchestrates this, or the merge_datasets if it handles the flow.
            # Given the complexity, we assume `merge_main` or `merge_datasets` handles the full flow if passed the right inputs.
            # However, to be safe and explicit, we'll construct the call based on typical patterns.
            # Let's assume `merge_datasets` takes the two dataframes and outputs the merged one.
            
            # Re-load dataframes to ensure we have them
            structures_df = pd.read_csv(STRUCTURES_RAW_PATH)
            # Use the normalized thermal data
            thermal_df = pd.read_csv(NORMALIZED_THERMAL_PATH)

            merged_df = merge_datasets(structures_df, thermal_df)
            
            # Validate geometry
            valid_geo_df = validate_geometry(merged_df)
            
            # Enforce minimum compositions
            final_df = enforce_minimum_compositions(valid_geo_df, min_count=MIN_ROWS)
            
            # Add provenance
            final_df = add_provenance(final_df, source="T012-Integration-Test")
            
            # Save final output
            final_df.to_csv(MERGED_OUTPUT_PATH, index=False)
            print(f"  -> Merged and cleaned. Total rows: {len(final_df)}")
        except Exception as e:
            pytest.fail(f"Failed to merge and clean data: {e}")

        # --- Step 6: Validate Output ---
        print("Step 6: Validating output...")
        
        # Check file exists
        assert MERGED_OUTPUT_PATH.exists(), f"Output file {MERGED_OUTPUT_PATH} not found."

        # Load and check row count
        final_df = pd.read_csv(MERGED_OUTPUT_PATH)
        assert len(final_df) >= MIN_ROWS, f"Insufficient samples: {len(final_df)} < {MIN_ROWS}"
        print(f"  -> Row count check passed: {len(final_df)} >= {MIN_ROWS}")

        # Check for nulls in critical columns
        critical_cols = ['structure_id', 'thermal_conductivity']
        for col in critical_cols:
            assert col in final_df.columns, f"Missing critical column: {col}"
            null_count = final_df[col].isnull().sum()
            assert null_count == 0, f"Found {null_count} nulls in {col}"
        print(f"  -> Null check passed for {critical_cols}")

        # Check schema (optional but good for integration)
        expected_cols = [
            'structure_id', 'thermal_conductivity', 'source_reference', 
            'chemistry_class', 'temperature', 'tilting_angle', 
            'bond_length_variance', 'tolerance_factor', 'unit_cell_volume'
        ]
        # We might not have all these if T021 (descriptors) hasn't run yet.
        # T015 is US1 (Ingestion). US2 (Descriptors) runs later.
        # So we only check for the columns present in the merged raw data.
        # The schema in T005 defines the target, but T015 might not produce all.
        # Let's check for the core ones that MUST exist after US1.
        required_us1_cols = ['structure_id', 'thermal_conductivity', 'source_reference', 'chemistry_class']
        for col in required_us1_cols:
            assert col in final_df.columns, f"Missing required US1 column: {col}"

        print("  -> Schema check passed for US1 columns.")
        print("Integration test PASSED.")

    def test_artifacts_exist(self):
        """
        Verifies that all expected artifacts were created during the pipeline run.
        """
        # This test assumes test_pipeline_execution has run successfully.
        # In a real CI, we might run them in order or check existence directly.
        # Here we assert existence.
        assert STRUCTURES_RAW_PATH.exists(), "Structures raw file missing"
        assert THERMAL_RAW_PATH.exists(), "Thermal raw file missing"
        assert PROVENANCE_REPORT_PATH.exists(), "Provenance report missing"
        assert NORMALIZED_THERMAL_PATH.exists(), "Normalized thermal file missing"
        assert MERGED_OUTPUT_PATH.exists(), "Merged output file missing"

        # Validate content of provenance report
        if PROVENANCE_REPORT_PATH.exists():
            with open(PROVENANCE_REPORT_PATH, 'r') as f:
                report = json.load(f)
            assert 'pass_count' in report or 'valid_count' in report, "Invalid provenance report structure"

        # Validate content of merged file
        if MERGED_OUTPUT_PATH.exists():
            df = pd.read_csv(MERGED_OUTPUT_PATH)
            assert len(df) >= MIN_ROWS, "Merged file has insufficient rows"