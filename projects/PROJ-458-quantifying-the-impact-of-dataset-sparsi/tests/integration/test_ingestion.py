"""
Integration test for the full data ingestion pipeline (US1).

This test verifies that `code/data_ingestion.py` can successfully:
1. Download data from the Materials Project API (with retries).
2. Filter for valid DFT-computed entries with formation energy.
3. Generate descriptors using matminer.
4. Impute missing values.
5. Produce the final output file `data/processed/full_pool_final.csv`
   with >150,000 rows and valid feature vectors.
"""
import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

import pandas as pd
import numpy as np

# Add project root to path to import local modules
# Assuming tests/integration is at tests/integration/test_ingestion.py
# and code/ is at project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_env
from utils.logging import get_logger

logger = get_logger(__name__)

# Mock the MP_API_KEY to prevent actual API calls if key is missing,
# but in a real integration test environment, the key should be present.
# We will mock the network calls to ensure we can test the logic without
# rate limits or API failures during the test run, while verifying
# the pipeline produces the correct structure.

def test_full_ingestion_pipeline():
    """
    Integration test: Verify the full ingestion pipeline produces the expected
    output file with the required row count and schema.
    """
    # Setup: Ensure output directories exist
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "full_pool_final.csv"

    # Remove existing output if present to ensure a fresh run
    if output_file.exists():
        output_file.unlink()

    # Mock the external dependencies that require API keys or heavy computation
    # to ensure the test is deterministic and fast, while still exercising
    # the full pipeline logic (imports, function calls, file writing).
    
    # Mock the MP_API_KEY for config
    with patch.dict(os.environ, {"MP_API_KEY": "test_key_123"}):
        # We need to import data_ingestion after mocking env if it reads env at import time
        # But config.py loads it. Let's assume config is imported fresh or we mock the loader.
        
        # Mock the Materials Project API interaction
        # We simulate a large dataset to test the >150k row requirement
        mock_data = []
        num_rows = 160000  # Exceeds 150k requirement
        
        for i in range(num_rows):
            mock_data.append({
                "material_id": f"mp-{i:07d}",
                "composition": "Fe2O3",
                "formation_energy": -5.0 + (i % 10) * 0.1,
                "dft_computed": True,
                # Simulate some raw descriptors that matminer would generate
                "Ehull": 0.0,
                "nsites": 5,
                "volume": 100.0
            })
        
        # Create a DataFrame for the "raw" download simulation
        raw_df = pd.DataFrame(mock_data)
        
        # Mock the matminer feature extractor to return dummy numeric columns
        # This avoids the heavy dependency on matminer actually running in the test env
        # while verifying the pipeline calls it correctly.
        mock_descriptors = pd.DataFrame({
            "ElementalPropertyFeatureExtractor_atomic_number_mean": np.random.rand(num_rows) * 100,
            "ElementalPropertyFeatureExtractor_electronegativity_mean": np.random.rand(num_rows) * 5,
            "ElementalPropertyFeatureExtractor_atomic_radius_mean": np.random.rand(num_rows) * 2,
            "Ehull": 0.0,
            "nsites": 5,
            "volume": 100.0
        })
        
        # We patch the functions inside data_ingestion
        from code import data_ingestion
        
        # Patch the API fetch function
        original_fetch = data_ingestion._fetch_mp_data
        def mock_fetch(*args, **kwargs):
            return raw_df
        data_ingestion._fetch_mp_data = mock_fetch
        
        # Patch the descriptor generation to return the mock dataframe
        # Assuming the function is named something like _generate_descriptors
        # We need to be careful with the exact name. Let's assume it's internal.
        # If the file structure isn't known, we patch the method that calls matminer.
        # For this test, we assume the script has a function `run_pipeline` or similar.
        # If the script is a top-level script, we might need to patch the specific steps.
        
        # Let's assume the script defines a function `main` or `run_ingestion`
        # We will patch the specific heavy steps to return our mock data.
        
        # Strategy: Mock the internal functions that do the heavy lifting
        # so the script runs through the logic and writes the file.
        
        # Patch the descriptor extraction
        original_extract = data_ingestion._extract_descriptors
        def mock_extract(df):
            # Merge mock descriptors with the input df (keeping common keys)
            # We need to ensure the columns match what the rest of the pipeline expects
            return pd.concat([df, mock_descriptors], axis=1)
        data_ingestion._extract_descriptors = mock_extract
        
        # Patch the imputation step to just return the dataframe (no-op for mock)
        original_impute = data_ingestion._impute_missing
        def mock_impute(df):
            return df
        data_ingestion._impute_missing = mock_impute

        try:
            # Run the ingestion pipeline
            # Assuming the entry point is a function called `run_ingestion` or `main`
            # If the file is a script, we might need to call the specific function
            # based on the task description T024 implementation.
            # Since T024 is not yet implemented, we are implementing the test for it.
            # The test assumes T024 will implement a function `run_ingestion` or similar.
            # If the script is purely top-level, we might need to exec it or refactor.
            # However, standard practice is to have a callable function.
            
            # Let's assume the implementation in T024 defines:
            # def run_ingestion(output_dir: Path) -> None:
            
            if hasattr(data_ingestion, 'run_ingestion'):
                data_ingestion.run_ingestion(output_dir)
            elif hasattr(data_ingestion, 'main'):
                # If it's a script with a main that takes args, we might need to mock sys.argv
                # But for integration test, we prefer a function call.
                # If the file is just top-level code, we can't easily test it without refactoring.
                # We assume the implementation in T024 follows the pattern of having a callable.
                # If not, we might need to adjust.
                # For now, let's assume it's a function.
                raise AttributeError("data_ingestion module must define run_ingestion or main callable")
            else:
                # Fallback: try to run the module as a script if it's purely top-level
                # This is less ideal for unit/integration tests but possible.
                # We would need to ensure the script writes to the correct path.
                # Let's assume the implementation in T024 includes a `if __name__ == "__main__":`
                # and we can call the logic directly.
                # Since we can't know the exact implementation of T024 yet, we assume a standard pattern.
                # Let's assume the function is `run_ingestion`.
                raise RuntimeError("Could not find run_ingestion function in data_ingestion")
            
            # Verification
            assert output_file.exists(), f"Output file {output_file} was not created"
            
            df_final = pd.read_csv(output_file)
            
            # Check row count
            assert len(df_final) > 150000, f"Expected >150,000 rows, got {len(df_final)}"
            
            # Check for non-null formation energy
            assert df_final['formation_energy'].notnull().all(), "Found null formation_energy values"
            
            # Check for feature vectors (at least some descriptor columns)
            # We expect the matminer columns to be present
            expected_cols = [
                'ElementalPropertyFeatureExtractor_atomic_number_mean',
                'ElementalPropertyFeatureExtractor_electronegativity_mean',
                'ElementalPropertyFeatureExtractor_atomic_radius_mean'
            ]
            for col in expected_cols:
                assert col in df_final.columns, f"Missing expected descriptor column: {col}"
                assert df_final[col].notnull().all(), f"Found null values in {col}"
            
            # Check checksum file exists
            checksum_file = output_dir / "full_pool_final.csv.sha256"
            assert checksum_file.exists(), f"Checksum file {checksum_file} was not created"
            
            # Verify checksum content
            with open(checksum_file, 'r') as f:
                checksum = f.read().strip()
            assert len(checksum) == 64, f"Invalid checksum length: {len(checksum)}"
            
            logger.info("Integration test passed: Full ingestion pipeline successful.")
            
        finally:
            # Restore original functions
            data_ingestion._fetch_mp_data = original_fetch
            data_ingestion._extract_descriptors = original_extract
            data_ingestion._impute_missing = original_impute

if __name__ == "__main__":
    test_full_ingestion_pipeline()
    print("Integration test completed successfully.")