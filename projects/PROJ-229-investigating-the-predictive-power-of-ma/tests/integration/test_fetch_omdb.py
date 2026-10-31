"""
Integration test for the OMDB CIF fetching script (T003).

The test runs the ``fetch_omdb_structures`` script and then checks that at
least 80 % of the material IDs present in ``data/raw/pcm.parquet`` have a
corresponding ``.cif`` file in ``data/raw/omdb_structures``.
"""

import pathlib

import pytest
from llmxive_toolkit import paths

# Import the script to ensure it can be executed without error.
from code.data.fetch_omdb_structures import main as fetch_main

@pytest.mark.integration
def test_fetch_omdb_structures(tmp_path: pathlib.Path):
    """
    Run the fetch script and verify coverage.

    The test assumes that ``data/raw/pcm.parquet`` already exists (produced by
    T002).  It executes the script (which writes to the project data folder)
    and then checks that the proportion of material IDs with a CIF meets the
    80 % threshold.
    """
    # Run the script – any exception will cause the test to fail.
    fetch_main()

    # Locate the input parquet and output directory.
    pcm_path = paths.data("raw", "pcm.parquet")
    output_dir = paths.data("raw", "omdb_structures")

    # Load the list of material IDs.
    import pandas as pd

    df = pd.read_parquet(pcm_path, engine="pyarrow")
    material_ids = set(df["material_id"].astype(str).unique())

    # Count how many CIF files exist.
    existing_cifs = {
        p.stem
        for p in output_dir.glob("*.cif")
        if p.is_file()
    }

    coverage = len(existing_cifs) / len(material_ids)
    assert coverage >= 0.80, (
        f"CIF coverage is {coverage:.2%}, which is below the required 80 %."
    )