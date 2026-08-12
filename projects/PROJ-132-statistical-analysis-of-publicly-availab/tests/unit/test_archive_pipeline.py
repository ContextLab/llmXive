"""
Unit tests for the archive pipeline.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

# Mock the archive_utils to avoid dependency on actual data download in tests
# We will test the logic of the pipeline by mocking the source directories

@pytest.fixture
def temp_env():
    """Create a temporary directory structure mimicking the project data layout."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create mock data directories
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    ebird_dir = raw_dir / "ebird_sample"
    ebird_dir.mkdir()
    (ebird_dir / "sample.csv").write_text("species,lat,lon,count\nTurdus migratorius,40.1,-75.1,1")
    
    noaa_dir = raw_dir / "noaa_prism"
    noaa_dir.mkdir()
    (noaa_dir / "climate.parquet").write_text("dummy")
    
    # Create a temporary archive dir
    archive_dir = temp_dir / "data" / "raw" / "archive"
    
    yield {
        "root": temp_dir,
        "ebird_dir": ebird_dir,
        "noaa_dir": noaa_dir,
        "archive_dir": archive_dir
    }
    
    shutil.rmtree(temp_dir)

def test_run_archive_pipeline(temp_env):
    """Test that the archive pipeline correctly copies files and generates a manifest."""
    # Temporarily override the module-level paths in archive_pipeline
    import src.data.archive_pipeline as pipeline_module
    from unittest.mock import patch, MagicMock
    
    original_root = pipeline_module.PROJECT_ROOT
    original_ebird = pipeline_module.RAW_EBIRD_DIR
    original_noaa = pipeline_module.RAW_NOAA_DIR
    original_daymet = pipeline_module.RAW_DAYMET_DIR
    original_archive = pipeline_module.ARCHIVE_DIR
    original_manifest = pipeline_module.MANIFEST_PATH

    try:
        # Patch the paths to use our temp directories
        pipeline_module.PROJECT_ROOT = temp_env["root"]
        pipeline_module.RAW_EBIRD_DIR = temp_env["ebird_dir"]
        pipeline_module.RAW_NOAA_DIR = temp_env["noaa_dir"]
        pipeline_module.RAW_DAYMET_DIR = temp_env["root"] / "data" / "raw" / "daymet" # Ensure non-existent
        pipeline_module.ARCHIVE_DIR = temp_env["archive_dir"]
        pipeline_module.MANIFEST_PATH = temp_env["archive_dir"] / "archive_manifest.json"

        # Run the pipeline logic directly (bypassing main() sys.exit)
        # We need to ensure the functions we import in the module are available
        # Since we are patching the module globals, we can call run_archive_pipeline
        result = pipeline_module.run_archive_pipeline()

        # Assertions
        assert result["status"] == "success"
        assert pipeline_module.ARCHIVE_DIR.exists()
        assert (pipeline_module.ARCHIVE_DIR / "ebird_sample").exists()
        assert (pipeline_module.ARCHIVE_DIR / "noaa_prism").exists()
        assert pipeline_module.MANIFEST_PATH.exists()

        # Check manifest content
        with open(pipeline_module.MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
        
        assert "files" in manifest
        assert len(manifest["files"]) > 0
        
        # Verify file presence in manifest
        file_names = [f["filename"] for f in manifest["files"]]
        assert any("sample.csv" in f for f in file_names)
        assert any("climate.parquet" in f for f in file_names)

    finally:
        # Restore original paths
        pipeline_module.PROJECT_ROOT = original_root
        pipeline_module.RAW_EBIRD_DIR = original_ebird
        pipeline_module.RAW_NOAA_DIR = original_noaa
        pipeline_module.RAW_DAYMET_DIR = original_daymet
        pipeline_module.ARCHIVE_DIR = original_archive
        pipeline_module.MANIFEST_PATH = original_manifest