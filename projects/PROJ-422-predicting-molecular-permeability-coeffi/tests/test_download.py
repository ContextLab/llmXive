import pytest
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths
from code.data.download import DataLoader, VERIFIED_DATASET_CONFIG

def test_download_produces_artifacts():
    """Verify that the download script produces the required files."""
    loader = DataLoader()
    # We can run process() or check if the files already exist from the execute:true run
    # For a unit test, we ensure the output paths are valid and contain data.
    raw_file = paths.data("raw", VERIFIED_DATASET_CONFIG["filename"])
    checksum_file = paths.data("raw", "checksums.json")
    
    assert raw_file.exists(), "Raw data file was not created."
    assert checksum_file.exists(), "Checksum file was not created."

def test_dataset_contains_required_columns():
    """Verify that the downloaded dataset contains the configured target column."""
    raw_file = paths.data("raw", VERIFIED_DATASET_CONFIG["filename"])
    df = pd.read_csv(raw_file)
    
    assert VERIFIED_DATASET_CONFIG["smiles_column"] in df.columns, "SMILES column missing."
    assert VERIFIED_DATASET_CONFIG["target_column"] in df.columns, "Target column missing."
    assert not df[VERIFIED_DATASET_CONFIG["target_column"]].isna().all(), "Target column is empty."

def test_loader_fails_on_missing_column():
    """Verify that the DataLoader fails loudly if a required column is missing."""
    # Create a dummy dataframe missing the target column
    df_bad = pd.DataFrame({"SMILES": ["CCO", "CCN"]})
    
    # Use a config that expects a target column not present in df_bad
    bad_config = VERIFIED_DATASET_CONFIG.copy()
    bad_config["expected_columns"] = ["SMILES", "non_existent_column"]
    
    loader = DataLoader(config=bad_config)
    with pytest.raises(RuntimeError, match="Missing required columns"):
        loader.validate_columns(df_bad)