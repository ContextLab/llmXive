import os
import pytest
from pathlib import Path
from code.data.fetch_ace import fetch_ace

def test_fetch_ace_creates_file(tmp_path, monkeypatch):
    # Redirect RAW_DATA_DIR to a temporary directory for isolation
    monkeypatch.setattr("code.config.RAW_DATA_DIR", str(tmp_path))
    output_path = fetch_ace("2003-10-01", "2003-10-31")
    assert os.path.isfile(output_path), "ACE raw CSV was not created"
    df = pd.read_csv(output_path)
    # Verify required columns are present
    for col in ["N_p", "T_p", "He2+_ratio"]:
        assert col in df.columns, f"Missing required column {col}"
