import os
import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_data_path

def test_downloaded_files_exist():
    """Verify that all required raw data files were created."""
    raw_dir = get_data_path() / "raw"
    
    files = {
        "oc20_sample.parquet": True,
        "mp_descriptors.json": True,
        "experimental_tof.csv": True,
        "oc20_revision.txt": True,
        "checksums.json": True
    }
    
    for filename, expected in files.items():
        path = raw_dir / filename
        assert path.exists(), f"File {filename} is missing from {raw_dir}"
        assert path.stat().st_size > 0, f"File {filename} is empty"

def test_oc20_sample_content():
    """Verify OC20 sample contains data."""
    path = get_data_path() / "raw" / "oc20_sample.parquet"
    df = pd.read_parquet(path)
    assert len(df) > 0, "OC20 sample dataframe is empty"
    assert "composition" in df.columns, "OC20 sample missing composition column"

def test_experimental_tof_content():
    """Verify experimental TOF contains data."""
    path = get_data_path() / "raw" / "experimental_tof.csv"
    df = pd.read_csv(path)
    assert len(df) > 0, "Experimental TOF dataframe is empty"
    assert "experimental_tof" in df.columns, "Experimental TOF missing target column"

def test_mp_descriptors_content():
    """Verify MP descriptors contains data."""
    path = get_data_path() / "raw" / "mp_descriptors.json"
    with open(path, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), "MP descriptors should be a JSON dictionary"
    assert len(data) > 0, "MP descriptors dictionary is empty"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])