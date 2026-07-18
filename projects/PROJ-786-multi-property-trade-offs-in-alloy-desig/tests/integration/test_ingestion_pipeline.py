"""
Integration test for full ingestion pipeline in User Story 1.

This test verifies that the entire pipeline (Data Ingestion -> Filtering -> Encoding)
runs successfully and produces the expected output file with correct schema.

Requirements:
- Assert `data/processed/encoded_alloys.csv` exists.
- Assert the CSV has the correct columns (elemental fractions + periodic descriptors + targets).
- Assert no nulls in key columns.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data
from code.feature_encoder import encode_dataframe, save_encoded_data
from code.config import get_config

# Expected columns based on T013 (elemental fractions + periodic descriptors)
# T013 says: "encode compositions using elemental fractions and periodic descriptors"
# We assume the output contains at least: 'formula', 'bulk_modulus', 'shear_modulus',
# and some encoded features (e.g., 'elem_frac_Al', 'atomic_radius_mean', etc.)
EXPECTED_TARGET_COLUMNS = ['bulk_modulus', 'shear_modulus']
MIN_REQUIRED_COLUMNS = ['formula'] + EXPECTED_TARGET_COLUMNS

def create_mock_oqmd_data(num_rows: int) -> pd.DataFrame:
    """
    Creates a mock OQMD-like dataset for integration testing.
    In a real scenario, this would be replaced by the actual HuggingFace fetch.
    This mock data is used ONLY within this test to simulate the pipeline flow
    without requiring network access or large dataset downloads during the test run.
    """
    formulas = []
    bulk_moduli = []
    shear_moduli = []
    compositions = []
    
    elements = ["Al", "Fe", "Ni", "Cu", "Ti"]
    
    for i in range(num_rows):
        e1 = elements[i % len(elements)]
        e2 = elements[(i + 1) % len(elements)]
        formula = f"{e1}_{50+i%50}{e2}_{50-i%50}"
        formulas.append(formula)
        
        # Ensure valid moduli for this test
        bulk = 100.0 + (i % 50)
        shear = 40.0 + (i % 20)
        bulk_moduli.append(float(bulk))
        shear_moduli.append(float(shear))
        
        # Mock composition string
        comp = f"{e1}:0.5,{e2}:0.5"
        compositions.append(comp)

    return pd.DataFrame({
        "formula": formulas,
        "bulk_modulus": bulk_moduli,
        "shear_modulus": shear_moduli,
        "elemental_composition": compositions,
        "energy_per_atom": [-5.0] * num_rows
    })

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory to simulate data/processed."""
    # We create a temp dir and set it as the output path
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_full_pipeline_execution(temp_output_dir):
    """
    Integration Test: Run ingestion and encoding, verify output file exists and has correct schema.
    """
    # 1. Setup: Create mock data
    # We simulate the input that would come from HuggingFace
    mock_data = create_mock_oqmd_data(num_rows=1000) # Large enough to pass threshold
    
    # 2. Ingestion Step (Simulated)
    # Since load_oqmd_data fetches from HF, we mock it for this integration test
    # to ensure it runs without network dependency in the test suite.
    import code.data_ingestion as di_module
    original_load = di_module.load_oqmd_data
    di_module.load_oqmd_data = lambda *args, **kwargs: mock_data

    try:
        # Run filtering
        df_filtered = filter_valid_entries(mock_data)
        assert len(df_filtered) >= 500, "Mock data should have >= 500 valid entries"
        
        # Run encoding
        # We need to ensure feature_encoder.py can handle our mock composition format
        # T013 says it uses elemental fractions and periodic descriptors.
        # We assume encode_dataframe handles the 'elemental_composition' column.
        df_encoded = encode_dataframe(df_filtered)
        
        # 3. Save Output
        output_path = temp_output_dir / "encoded_alloys.csv"
        save_encoded_data(df_encoded, str(output_path))
        
        # 4. Verification
        assert output_path.exists(), f"Output file {output_path} does not exist"
        
        df_output = pd.read_csv(output_path)
        
        # Check columns
        for col in MIN_REQUIRED_COLUMNS:
            assert col in df_output.columns, f"Missing required column: {col}"
        
        # Check for encoded features (at least some numeric columns besides targets)
        # We expect at least one elemental fraction or periodic property column
        numeric_cols = df_output.select_dtypes(include=['float64', 'int64']).columns
        assert len(numeric_cols) > len(EXPECTED_TARGET_COLUMNS), "Should have more numeric columns than just targets"
        
        # Check for nulls in key columns
        for col in EXPECTED_TARGET_COLUMNS:
            assert df_output[col].isnull().sum() == 0, f"Null values found in {col}"
        
        # Check row count
        assert len(df_output) == len(df_filtered), "Row count mismatch after encoding"

    finally:
        # Restore original function
        di_module.load_oqmd_data = original_load

if __name__ == "__main__":
    pytest.main([__file__, "-v"])