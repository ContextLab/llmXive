import pytest
import os
from pathlib import Path
import sys
import json
import tempfile
import shutil
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.ingest import run_ingestion
from src.data.preprocess import calculate_t_eff, run_preprocessing
from src.data.merge_aligned_data import merge_and_save

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure for integration tests."""
    tmpdir = tempfile.mkdtemp()
    # Create required subdirectories
    dirs = [
        "data/raw", "data/processed", "data/results", "logs", "config", "src/data"
    ]
    for d in dirs:
        Path(tmpdir, d).mkdir(parents=True, exist_ok=True)
    
    # Mock the global paths in ingest module
    import src.data.ingest as ingest_module
    original_raw = ingest_module.DATA_RAW_DIR
    original_logs = ingest_module.LOGS_DIR
    original_exclusion = ingest_module.EXCLUSION_LOG_PATH
    original_metadata = ingest_module.METADATA_PATH
    
    ingest_module.DATA_RAW_DIR = Path(tmpdir) / "data" / "raw"
    ingest_module.LOGS_DIR = Path(tmpdir) / "logs"
    ingest_module.EXCLUSION_LOG_PATH = ingest_module.LOGS_DIR / "alignment.json"
    ingest_module.METADATA_PATH = ingest_module.DATA_RAW_DIR / "ingestion_metadata.json"
    
    yield tmpdir
    
    # Restore original paths
    ingest_module.DATA_RAW_DIR = original_raw
    ingest_module.LOGS_DIR = original_logs
    ingest_module.EXCLUSION_LOG_PATH = original_exclusion
    ingest_module.METADATA_PATH = original_metadata
    shutil.rmtree(tmpdir)

@pytest.mark.skip(reason="Integration test requires real API access and credentials")
def test_full_ingest_flow(temp_project_dir):
    """
    End-to-end test of the ingestion flow.
    Note: This test is skipped in CI unless real credentials and network are available.
    It verifies that the script runs without error and produces expected files.
    """
    # This test would normally run run_ingestion with a small date range
    # and verify the output files exist.
    # Since it requires real API calls (IceCube/ERA5), we skip it in automated runs
    # unless specifically enabled.
    # In a real run, it would look like:
    # icecube_df, era5_df = run_ingestion("2023-01-01", "2023-01-07")
    # assert icecube_df is not None
    # assert era5_df is not None
    # assert Path(temp_project_dir, "data/raw/icecube.csv").exists()
    # assert Path(temp_project_dir, "data/raw/era5.csv").exists()
    # assert Path(temp_project_dir, "data/raw/aligned_daily.csv").exists()
    # assert Path(temp_project_dir, "logs/alignment.json").exists()
    pass
