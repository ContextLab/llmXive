"""
Verify that the default loader can locate the cleaned CSV file after a
successful download. The test runs the downloader first to guarantee the file
exists.
"""

from pathlib import Path

import pandas as pd

from code.download.knot_atlas_loader import main as download_main
from code.analysis.data_quantities import load_cleaned_knots_data

def test_load_cleaned_knots_data(tmp_path, monkeypatch):
    # Ensure the project uses the temporary directory for data output
    monkeypatch.chdir(tmp_path)
    # Run the downloader – it will create the expected CSV
    download_main()
    # Now load using the default loader
    df = load_cleaned_knots_data()
    assert isinstance(df, pd.DataFrame)
    # Basic sanity checks
    assert "name" in df.columns
    assert "crossing_number" in df.columns
    assert len(df) > 0
