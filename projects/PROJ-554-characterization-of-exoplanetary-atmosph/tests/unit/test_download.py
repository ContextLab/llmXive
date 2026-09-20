import pytest
import pandas as pd
import json
import os
from pathlib import Path
from code.download import count_unique_planets, save_metadata_csv, METADATA_COLUMNS

def test_count_unique_planets_empty_file(tmp_path):
    """Test counting unique planets from an empty metadata file."""
    metadata_path = tmp_path / "metadata.csv"
    df = pd.DataFrame(columns=METADATA_COLUMNS)
    df.to_csv(metadata_path, index=False)

    count = count_unique_planets(str(metadata_path))
    assert count == 0

def test_count_unique_planets_with_data(tmp_path):
    """Test counting unique planets from a metadata file with data."""
    metadata_path = tmp_path / "metadata.csv"
    data = {
        "planet_name": ["Kepler-1b", "Kepler-2b", "Kepler-1b", "WASP-1b"],
        "temperature": [1000, 1200, 1000, 1500],
        "metallicity": [0.1, 0.2, 0.1, 0.3],
        "snr": [10, 15, 10, 20],
        "resolution": [50, 60, 50, 70],
        "planet_category": ["Hot Jupiter", "Hot Jupiter", "Hot Jupiter", "Hot Jupiter"],
        "instrument": ["HST", "HST", "HST", "Spitzer"],
        "wavelength_range": ["0.5-1.5", "0.5-1.5", "0.5-1.5", "1.0-2.0"]
    }
    df = pd.DataFrame(data)
    df.to_csv(metadata_path, index=False)

    count = count_unique_planets(str(metadata_path))
    assert count == 3  # Kepler-1b, Kepler-2b, WASP-1b

def test_save_metadata_csv_creates_file(tmp_path):
    """Test that save_metadata_csv creates the file with correct columns."""
    output_path = tmp_path / "metadata.csv"
    data = [
        {
            "planet_name": "Kepler-1b",
            "temperature": 1000,
            "metallicity": 0.1,
            "snr": 10,
            "resolution": 50,
            "planet_category": "Hot Jupiter",
            "instrument": "HST",
            "wavelength_range": "0.5-1.5"
        }
    ]

    save_metadata_csv(data, str(output_path))

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert list(df.columns) == METADATA_COLUMNS
    assert len(df) == 1