import pytest
import pandas as pd
import json
from pathlib import Path
from llmxive_toolkit import paths
from code.data.download import DataLoader

def test_download_produces_artifacts():
    """Verify that the download script creates the expected files."""
    loader = DataLoader()
    loader.process()
    
    raw_file = paths.data("raw", "permeability_data.csv")
    checksum_file = paths.data("raw", "checksums.json")
    
    assert raw_file.exists(), "Raw data CSV was not created."
    assert checksum_file.exists(), "Checksum JSON was not created."
    
    with open(checksum_file, 'r') as f:
        checksums = json.load(f)
        assert "permeability_data.csv" in checksums, "Checksum file missing entry for raw data."

def test_download_contains_required_columns():
    """Verify that the downloaded dataset contains the required columns."""
    raw_file = paths.data("raw", "permeability_data.csv")
    if not raw_file.exists():
        pytest.fail("Raw data file missing; run download script first.")
    
    df = pd.read_csv(raw_file)
    cols = [c.lower() for c in df.columns]
    
    assert 'smiles' in cols, f"SMILES column missing from {df.columns}"
    assert 'logp' in cols, f"logP column missing from {df.columns}"
    assert len(df) > 0, "Downloaded dataset is empty."