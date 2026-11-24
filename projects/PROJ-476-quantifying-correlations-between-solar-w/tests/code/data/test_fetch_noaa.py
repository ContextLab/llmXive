import os
import pytest
from pathlib import Path
from code.data.fetch_noaa import fetch_noaa

def test_fetch_noaa_creates_file(tmp_path, monkeypatch):
    # Redirect RAW_DATA_DIR to a temporary directory for isolation
    monkeypatch.setattr("code.config.RAW_DATA_DIR", str(tmp_path))
    output_path = fetch_noaa("2003-10-01", "2003-10-31")
    assert os.path.isfile(output_path), "NOAA raw CSV was not created"
    df = pd.read_csv(output_path)
    for col in ["Kp", "Dst"]:
        assert col in df.columns, f"Missing required column {col}"