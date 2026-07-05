"""
Integration tests for the full ingestion flow.
"""
import pytest
import os
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.ingest import run_ingestion
from src.data.utils import setup_logger

logger = setup_logger("test_ingest_flow")

@pytest.mark.skipif(
    not os.environ.get("CDSAPI_KEY"),
    reason="CDSAPI_KEY environment variable not set"
)
def test_full_ingest_flow():
    """
    Run the full ingestion flow and verify outputs.
    Requires CDSAPI_KEY to be set in environment.
    """
    # Run ingestion
    try:
        run_ingestion()
    except Exception as e:
        logger.error(f"Ingestion flow failed: {e}")
        pytest.fail(f"Ingestion flow failed: {e}")

    # Verify outputs exist
    assert Path("data/raw/icecube_raw.csv").exists(), "IceCube raw file not found"
    assert Path("data/raw/era5_temperature_raw.csv").exists(), "ERA5 raw file not found"
    
    # Verify metadata log
    metadata_path = Path("logs/ingest_metadata.json")
    assert metadata_path.exists(), "Ingest metadata log not found"

    # Verify release identifiers are present in metadata
    with open(metadata_path, 'r') as f:
        logs = json.load(f)
    
    # Check that we have entries with release identifiers
    found_icecube = False
    found_era5 = False
    
    for entry in logs:
        if "icecube" in entry.get("source", "").lower():
            assert "release_identifier" in entry, "IceCube entry missing release_identifier"
            assert "sha256:" in entry["release_identifier"], "IceCube release ID format invalid"
            found_icecube = True
        if "era5" in entry.get("source", "").lower():
            assert "release_identifier" in entry, "ERA5 entry missing release_identifier"
            assert "sha256:" in entry["release_identifier"], "ERA5 release ID format invalid"
            found_era5 = True
    
    assert found_icecube, "No IceCube metadata found"
    assert found_era5, "No ERA5 metadata found"

    logger.info("Integration test passed: All outputs verified with release identifiers.")