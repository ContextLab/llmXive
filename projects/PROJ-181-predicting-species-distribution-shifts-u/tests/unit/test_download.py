import json
import os
from pathlib import Path

import pytest

# Import the download main function directly
from code.download import main as download_main
from code.manifest_manager import load_manifest

@pytest.mark.timeout(300)
def test_download_climate_historical(tmp_path, monkeypatch):
    """
    Run the download script in a mode that only fetches the historical
    WorldClim bioclimatic rasters. Verify that the expected number of
    raster files are written and that manifest entries are created.
    """
    # Use a temporary data directory to avoid polluting the real project data
    # The config module reads DATA_DIR from the project root; we monkeypatch it
    # to point to the temporary directory for this test run.
    from code import config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path, raising=False)

    # Run the download script with arguments to only download historical rasters
    # The script parses sys.argv; we simulate the CLI call by providing the args.
    import sys

    test_argv = ["download.py", "--climate", "historical"]
    monkeypatch.setattr(sys, "argv", test_argv)

    # Execute the download workflow
    download_main()

    # Verify that the historical climate directory exists and contains 19 .tif files
    climate_dir = tmp_path / "raw" / "climate_historical"
    assert climate_dir.is_dir(), "Historical climate directory was not created"
    tif_files = list(climate_dir.glob("*.tif"))
    assert len(tif_files) == 19, f"Expected 19 raster files, found {len(tif_files)}"

    # Load the manifest and check that an entry for the collection exists
    manifest = load_manifest()
    datasets = manifest.get("datasets", {})
    # The collection entry is recorded with the directory path as the key
    collection_key = str(climate_dir)
    # Because the manifest records the relative path, we look for any entry whose
    # file_path starts with the climate directory.
    matching = [
        v for v in datasets.values()
        if v.get("file_path", "").startswith("data/raw/climate_historical")
    ]
    assert matching, "No manifest entry found for the historical climate collection"

    # Clean up: the temporary directory will be removed automatically by pytest
    # (no explicit cleanup needed)
