import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Mock the dependencies if needed, but we will test the logic directly
# by creating temporary test data.
from data_ingestion import impute_and_finalize

@pytest.fixture
def temp_dirs(tmp_path):
    # Create a mock directory structure
    data_processed = tmp_path / "data" / "processed"
    data_results = tmp_path / "data" / "results"
    data_processed.mkdir(parents=True)
    data_results.mkdir(parents=True)
    return {
        "processed": data_processed,
        "results": data_results,
        "input_desc": str(data_processed / "descriptors_pool.csv"),
        "test_indices": str(data_processed / "test_set_indices.csv"),
        "output_final": str(data_processed / "full_pool_final.csv"),
        "log_file": str(data_results / "ingestion_log.json")
    }

def create_mock_descriptors(path, n_rows=100, n_cols=5):
    """Create a mock descriptors CSV with some NaNs."""
    data = np.random.rand(n_rows, n_cols)
    # Introduce NaNs randomly
    mask = np.random.rand(n_rows, n_cols) < 0.2
    data[mask] = np.nan
    # Add a non-numeric column
    df = pd.DataFrame(data, columns=[f"desc_{i}" for i in range(n_cols)])
    df["material_id"] = [f"mp-{i}" for i in range(n_rows)]
    df.to_csv(path, index=False)

def create_mock_test_indices(path, n_indices=10):
    """Create a mock test indices CSV."""
    indices = list(range(n_indices))
    pd.DataFrame({"index": indices}).to_csv(path, index=False)

def test_imputation_logic(temp_dirs):
    """Test that imputation correctly fills means and drops high-missing rows."""
    # Setup
    create_mock_descriptors(temp_dirs["input_desc"], n_rows=100, n_cols=5)
    create_mock_test_indices(temp_dirs["test_indices"], n_indices=10)
    
    # Patch paths in the function temporarily? 
    # Since the function uses global constants, we need to either refactor or test differently.
    # For this test, we assume the constants are set to the temp paths or we mock them.
    # However, the prompt requires extending existing files. 
    # To test without modifying global constants in the main file, we will 
    # verify the logic by inspecting the output if we run the function with mocked paths.
    # But the function `impute_and_finalize` uses hardcoded global paths.
    # To make this testable, we must assume the environment is set up correctly or 
    # we test the helper logic. 
    # Given constraints, let's verify the file existence and structure after a run 
    # assuming the paths are set to the temp directory for this test run.
    
    # Since we cannot easily change the global constants in the imported module without 
    # reloading or monkey-patching, we will perform a structural test.
    # We will create the files at the EXPECTED global paths relative to the repo root 
    # (which we can't do in a temp dir easily without changing CWD).
    # Instead, we will test the logic by creating a small script that mimics the function.
    
    # Alternative: Test the logic by creating a pandas DataFrame and applying the steps.
    df = pd.read_csv(temp_dirs["input_desc"])
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Calculate mean
    means = df[numeric_cols].mean()
    
    # Fill
    df_filled = df.copy()
    for col in numeric_cols:
        df_filled[col].fillna(means[col], inplace=True)
    
    # Check no NaNs left in numeric cols
    assert df_filled[numeric_cols].isna().sum().sum() == 0, "Imputation failed to fill all NaNs"
    
    # Test drop logic
    missing_pct = df.isna().sum(axis=1) / len(numeric_cols)
    rows_to_drop = missing_pct > 0.50
    dropped_count = rows_to_drop.sum()
    
    assert dropped_count >= 0, "Dropped count should be non-negative"
    
    # Now test the actual function by patching the constants
    import data_ingestion
    original_input = data_ingestion.INPUT_DESCRIPTORS_PATH
    original_test = data_ingestion.INPUT_TEST_INDICES_PATH
    original_output = data_ingestion.OUTPUT_FINAL_POOL_PATH
    original_log = data_ingestion.OUTPUT_INGESTION_LOG_PATH
    
    try:
        data_ingestion.INPUT_DESCRIPTORS_PATH = temp_dirs["input_desc"]
        data_ingestion.INPUT_TEST_INDICES_PATH = temp_dirs["test_indices"]
        data_ingestion.OUTPUT_FINAL_POOL_PATH = temp_dirs["output_final"]
        data_ingestion.OUTPUT_INGESTION_LOG_PATH = temp_dirs["log_file"]
        
        # Run
        result_df = impute_and_finalize()
        
        # Verify output file exists
        assert os.path.exists(temp_dirs["output_final"]), "Output file not created"
        assert os.path.exists(temp_dirs["log_file"]), "Log file not created"
        
        # Verify log content
        with open(temp_dirs["log_file"], "r") as f:
            log_data = json.load(f)
        assert log_data["task"] == "T027"
        assert "rows_output" in log_data
        
        # Verify output df
        assert len(result_df) == len(df) - dropped_count
        
    finally:
        # Restore
        data_ingestion.INPUT_DESCRIPTORS_PATH = original_input
        data_ingestion.INPUT_TEST_INDICES_PATH = original_test
        data_ingestion.OUTPUT_FINAL_POOL_PATH = original_output
        data_ingestion.OUTPUT_INGESTION_LOG_PATH = original_log

def test_imputation_drops_high_missing(temp_dirs):
    """Test that rows with >50% missing are dropped."""
    # Create a file with a row that has 100% missing
    df = pd.DataFrame({
        "desc_0": [1.0, np.nan, 3.0],
        "desc_1": [2.0, np.nan, 4.0],
        "material_id": ["a", "b", "c"]
    })
    df.to_csv(temp_dirs["input_desc"], index=False)
    create_mock_test_indices(temp_dirs["test_indices"], 0)
    
    import data_ingestion
    original_input = data_ingestion.INPUT_DESCRIPTORS_PATH
    original_test = data_ingestion.INPUT_TEST_INDICES_PATH
    original_output = data_ingestion.OUTPUT_FINAL_POOL_PATH
    original_log = data_ingestion.OUTPUT_INGESTION_LOG_PATH
    
    try:
        data_ingestion.INPUT_DESCRIPTORS_PATH = temp_dirs["input_desc"]
        data_ingestion.INPUT_TEST_INDICES_PATH = temp_dirs["test_indices"]
        data_ingestion.OUTPUT_FINAL_POOL_PATH = temp_dirs["output_final"]
        data_ingestion.OUTPUT_INGESTION_LOG_PATH = temp_dirs["log_file"]
        
        result_df = impute_and_finalize()
        
        # Row 'b' has 2/2 = 100% missing, should be dropped.
        # Row 'a' and 'c' have 0% missing.
        assert len(result_df) == 2, "Row with >50% missing should be dropped"
        assert "b" not in result_df["material_id"].values
        
    finally:
        data_ingestion.INPUT_DESCRIPTORS_PATH = original_input
        data_ingestion.INPUT_TEST_INDICES_PATH = original_test
        data_ingestion.OUTPUT_FINAL_POOL_PATH = original_output
        data_ingestion.OUTPUT_INGESTION_LOG_PATH = original_log