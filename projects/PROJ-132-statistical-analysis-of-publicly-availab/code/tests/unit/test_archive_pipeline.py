import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

from src.data.archive_pipeline import run_archive_pipeline

@pytest.fixture
def temp_env():
    """Create a temporary directory structure for testing."""
    base = tempfile.mkdtemp()
    ebird_dir = Path(base) / "data" / "raw" / "ebird_sample"
    ebird_dir.mkdir(parents=True)
    
    # Create a dummy eBird file
    (ebird_dir / "sample_ebird.parquet").write_text("dummy_ebird_data")
    
    climate_dir = Path(base) / "data" / "raw" / "noaa_prism"
    climate_dir.mkdir(parents=True)
    (climate_dir / "noaa_2020.parquet").write_text("dummy_climate_data")

    archive_dir = Path(base) / "data" / "raw" / "archive"
    manifest_path = Path(base) / "data" / "provenance" / "archive_manifest.json"
    ci_meta_path = archive_dir / "ci_upload_metadata.json"

    yield {
        "base": base,
        "ebird": str(ebird_dir),
        "climate": str(climate_dir),
        "archive": str(archive_dir),
        "manifest": str(manifest_path),
        "ci_meta": str(ci_meta_path)
    }

    # Cleanup
    shutil.rmtree(base, ignore_errors=True)

def test_run_archive_pipeline(temp_env):
    """
    Test that run_archive_pipeline correctly copies files, generates checksums,
    and creates CI metadata.
    """
    result = run_archive_pipeline(
        ebird_source=temp_env["ebird"],
        climate_source=temp_env["climate"],
        archive_dest=temp_env["archive"],
        manifest_path=temp_env["manifest"],
        ci_upload_flag=True
    )

    # Assertions on return value
    assert result["status"] == "success"
    assert Path(result["archive_path"]).exists()
    assert Path(result["manifest_path"]).exists()
    assert Path(result["ci_metadata_path"]).exists()

    # Verify files were copied
    archive_path = Path(result["archive_path"])
    assert (archive_path / "ebird_sample" / "sample_ebird.parquet").exists()
    assert (archive_path / "noaa_prism" / "noaa_2020.parquet").exists()

    # Verify manifest content
    with open(result["manifest_path"], 'r') as f:
        manifest = json.load(f)
    assert "total_files" in manifest
    assert "checksums" in manifest
    assert len(manifest["checksums"]) > 0

    # Verify CI metadata
    with open(result["ci_metadata_path"], 'r') as f:
        ci_meta = json.load(f)
    assert ci_meta["ci_action"] == "upload_artifact"
    assert ci_meta["artifact_name"] == "raw_data_provenance"
    assert "sources_archived" in ci_meta
    assert len(ci_meta["sources_archived"]) == 2