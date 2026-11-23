import pytest
import pandas as pd
from pathlib import Path
from code.data.download import DataLoader, VERIFIED_DATASET_CONFIG
from llmxive_toolkit import paths

def test_download_required_columns_exist():
    """
    Verify that the DataLoader successfully fetches the dataset and 
    the resulting file contains the required target column.
    """
    loader = DataLoader()
    df = loader.process()
    
    # Verify dataframe returned by process
    smiles_key = VERIFIED_DATASET_CONFIG["smiles_keyword"]
    target_key = VERIFIED_DATASET_CONFIG["target_keyword"]
    
    # Check case-insensitive presence in columns
    cols_lower = [c.lower() for c in df.columns]
    assert smiles_key.lower() in cols_lower, f"SMILES column {smiles_key} missing"
    assert target_key.lower() in cols_lower, f"Target column {target_key} missing"
    
    # Verify file was actually written to disk
    raw_file = paths.data("raw", VERIFIED_DATASET_CONFIG["filename"])
    assert raw_file.exists(), "Raw data file was not written to disk"
    
    # Verify checksum file was written
    checksum_file = raw_file.parent / "checksums.json"
    assert checksum_file.exists(), "Checksum file was not written to disk"

def test_dataloader_fails_on_invalid_config():
    """
    Verify that the DataLoader fails loudly if the target column is missing.
    """
    bad_config = {
        "hf_path": "deepchem/lipophilicity",
        "split": "train",
        "smiles_keyword": "smiles",
        "target_keyword": "non_existent_column",
        "filename": "fail_test.csv"
    }
    loader = DataLoader(config=bad_config)
    
    with pytest.raises(RuntimeError) as excinfo:
        # We manually trigger fetch and validate to avoid writing files
        df = loader.fetch_dataset()
        loader.validate_columns(df)
    
    assert "Missing required columns" in str(excinfo.value)