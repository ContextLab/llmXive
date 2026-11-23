"""
Integration test for the full data ingestion pipeline (US1).

This test verifies the end-to-end execution of:
1. Loading environment configuration (MP_API_KEY).
2. Fetching data from the Materials Project API.
3. Processing and saving the raw pool.
4. Filtering the pool (removing null energies and non-DFT entries).
5. Generating descriptors using matminer.
6. Imputing missing values and finalizing the dataset.

It ensures that all intermediate and final artifacts are written to disk
at the expected paths with valid content.
"""

import os
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Import the pipeline functions from the main module
# Note: We assume these are defined in code/data_ingestion.py
# We import them relative to the project root structure expected by the runner
import sys
# Add the code directory to the path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from data_ingestion import (
    load_env_config,
    exponential_backoff,
    fetch_material_data,
    process_and_save,
    filter_pool,
    generate_descriptors,
    impute_and_finalize,
    main
)
from utils.logging import get_logger
from utils.cpu_constraints import enforce_memory_limit

# Constants for test paths
TEST_DIR = None
RAW_POOL_PATH = None
FILTERED_POOL_PATH = None
DESCRIPTORS_PATH = None
FINAL_POOL_PATH = None
LOG_PATH = None

def setup_module(module):
    """Create a temporary directory structure for the integration test."""
    global TEST_DIR, RAW_POOL_PATH, FILTERED_POOL_PATH, DESCRIPTORS_PATH, FINAL_POOL_PATH, LOG_PATH
    TEST_DIR = tempfile.mkdtemp(prefix="ingestion_integration_test_")
    
    # Create directory structure
    data_raw = Path(TEST_DIR) / "data" / "raw"
    data_processed = Path(TEST_DIR) / "data" / "processed"
    data_results = Path(TEST_DIR) / "data" / "results"
    data_metadata = Path(TEST_DIR) / "data" / "metadata"
    
    data_raw.mkdir(parents=True, exist_ok=True)
    data_processed.mkdir(parents=True, exist_ok=True)
    data_results.mkdir(parents=True, exist_ok=True)
    data_metadata.mkdir(parents=True, exist_ok=True)

    RAW_POOL_PATH = str(data_raw / "raw_pool.csv")
    FILTERED_POOL_PATH = str(data_processed / "filtered_pool.csv")
    DESCRIPTORS_PATH = str(data_processed / "descriptors_pool.csv")
    FINAL_POOL_PATH = str(data_processed / "full_pool_final.csv")
    LOG_PATH = str(data_results / "ingestion_log.json")

    # Set environment variables for the test
    os.environ["MP_API_KEY"] = "test_api_key_integration"
    os.environ["DATA_RAW_DIR"] = str(data_raw)
    os.environ["DATA_PROCESSED_DIR"] = str(data_processed)
    os.environ["DATA_RESULTS_DIR"] = str(data_results)

def teardown_module(module):
    """Clean up the temporary directory."""
    global TEST_DIR
    if TEST_DIR and os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)

def test_full_ingestion_pipeline():
    """
    Integration test: test_full_ingestion_pipeline.

    Runs the full ingestion pipeline with mocked API responses to verify
    that:
    1. Data is fetched and saved to `data/raw/raw_pool.csv`.
    2. Filtering removes invalid entries and saves to `data/processed/filtered_pool.csv`.
    3. Descriptors are generated and saved to `data/processed/descriptors_pool.csv`.
    4. Imputation is performed and the final dataset is saved to `data/processed/full_pool_final.csv`.
    5. A log file is generated at `data/results/ingestion_log.json`.
    """
    logger = get_logger("test_ingestion_integration")
    logger.info("Starting full ingestion pipeline integration test.")

    # Mock the API response to simulate real data without hitting the network
    # We create a realistic mock response structure
    mock_response_data = [
        {
            "material_id": "mp-12345",
            "composition": "Si O2",
            "formation_energy": -1.5,
            "dft_computed": True,
            "elements": ["Si", "O"],
            "nelements": 2,
            "nsites": 3,
            "volume": 100.0,
            "density": 2.5,
            "space_group_number": 227
        },
        {
            "material_id": "mp-67890",
            "composition": "Fe2O3",
            "formation_energy": -2.1,
            "dft_computed": True,
            "elements": ["Fe", "O"],
            "nelements": 2,
            "nsites": 5,
            "volume": 150.0,
            "density": 4.0,
            "space_group_number": 167
        },
        {
            "material_id": "mp-11111",
            "composition": "NaCl",
            "formation_energy": -0.8,
            "dft_computed": True,
            "elements": ["Na", "Cl"],
            "nelements": 2,
            "nsites": 2,
            "volume": 50.0,
            "density": 2.0,
            "space_group_number": 225
        },
        {
            "material_id": "mp-22222",
            "composition": "H2O",
            "formation_energy": None, # Should be filtered out
            "dft_computed": True,
            "elements": ["H", "O"],
            "nelements": 2,
            "nsites": 3,
            "volume": 20.0,
            "density": 1.0,
            "space_group_number": 1
        },
        {
            "material_id": "mp-33333",
            "composition": "C",
            "formation_energy": -0.5,
            "dft_computed": False, # Should be filtered out
            "elements": ["C"],
            "nelements": 1,
            "nsites": 1,
            "volume": 10.0,
            "density": 2.2,
            "space_group_number": 194
        }
    ]

    # Mock the requests.get call used in fetch_material_data
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": mock_response_data, "meta": {"total": 5}}
    
    # Patch the requests.get function within data_ingestion module
    # We need to patch where it is used, which is inside data_ingestion
    with patch('data_ingestion.requests.get', return_value=mock_response):
        try:
            # Run the pipeline steps manually to ensure each step is tested
            
            # Step 1: Fetch and save raw pool
            # The actual fetch_material_data function might need to be called directly
            # or via the main entry point. For integration, we simulate the flow.
            # Assuming fetch_material_data writes to RAW_POOL_PATH
            # We will call the functions as they would be called in main()
            
            # Re-load config to ensure paths are picked up from env
            config = load_env_config()
            
            # Fetch data
            raw_data = fetch_material_data(config)
            assert raw_data is not None, "Raw data fetch failed"
            assert len(raw_data) > 0, "Raw data is empty"
            
            # Save raw pool
            process_and_save(raw_data, RAW_POOL_PATH)
            assert os.path.exists(RAW_POOL_PATH), f"Raw pool not saved at {RAW_POOL_PATH}"
            
            # Verify raw pool content
            raw_df = pd.read_csv(RAW_POOL_PATH)
            assert len(raw_df) == 5, f"Expected 5 rows in raw pool, got {len(raw_df)}"
            logger.info(f"Raw pool saved with {len(raw_df)} rows.")

            # Step 2: Filter pool
            filter_pool(RAW_POOL_PATH, FILTERED_POOL_PATH)
            assert os.path.exists(FILTERED_POOL_PATH), f"Filtered pool not saved at {FILTERED_POOL_PATH}"
            
            filtered_df = pd.read_csv(FILTERED_POOL_PATH)
            # Should have removed formation_energy is null (mp-22222) and dft_computed is False (mp-33333)
            assert len(filtered_df) == 3, f"Expected 3 rows in filtered pool, got {len(filtered_df)}"
            logger.info(f"Filtered pool saved with {len(filtered_df)} rows.")

            # Step 3: Generate descriptors
            # This step might be heavy, but with mock data it should be fast
            generate_descriptors(FILTERED_POOL_PATH, DESCRIPTORS_PATH)
            assert os.path.exists(DESCRIPTORS_PATH), f"Descriptors not saved at {DESCRIPTORS_PATH}"
            
            descriptors_df = pd.read_csv(DESCRIPTORS_PATH)
            assert len(descriptors_df) == 3, f"Expected 3 rows in descriptors, got {len(descriptors_df)}"
            # Check if some descriptor columns exist (matminer output)
            # We expect columns like 'Element Property: Atomic Number' etc.
            assert any("Element" in col for col in descriptors_df.columns), "No elemental property columns found"
            logger.info(f"Descriptors generated with {len(descriptors_df.columns)} columns.")

            # Step 4: Impute and finalize
            impute_and_finalize(DESCRIPTORS_PATH, FINAL_POOL_PATH, LOG_PATH)
            assert os.path.exists(FINAL_POOL_PATH), f"Final pool not saved at {FINAL_POOL_PATH}"
            assert os.path.exists(LOG_PATH), f"Log file not saved at {LOG_PATH}"
            
            final_df = pd.read_csv(FINAL_POOL_PATH)
            assert len(final_df) == 3, f"Expected 3 rows in final pool, got {len(final_df)}"
            
            # Verify log content
            with open(LOG_PATH, 'r') as f:
                log_data = json.load(f)
            assert "rows_imputed" in log_data or "rows_dropped" in log_data, "Log missing expected keys"
            logger.info(f"Final pool saved with {len(final_df)} rows. Log: {log_data}")

            logger.info("Integration test PASSED: All pipeline steps executed successfully.")

        except Exception as e:
            logger.error(f"Integration test FAILED: {str(e)}")
            raise

if __name__ == "__main__":
    test_full_ingestion_pipeline()
    print("Integration test completed successfully.")