"""
Unit tests for the Archive Pipeline (T005d).
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

# Add parent directory to path for imports if running standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.archive_pipeline import run_archive_pipeline


@pytest.fixture
def temp_env():
    """Create a temporary directory structure simulating raw data and archive."""
    base = Path(tempfile.mkdtemp())
    sources = base / "sources"
    archive = base / "archive"
    sources.mkdir()

    # Create mock eBird source
    ebird_dir = sources / "ebird_sample"
    ebird_dir.mkdir()
    (ebird_dir / "data.csv").write_text("col1,col2\n1,2\n3,4")
    (ebird_dir / "subdir").mkdir()
    (ebird_dir / "subdir" / "meta.json").write_text('{"key": "val"}')

    # Create mock Daymet source
    daymet_dir = sources / "daymet"
    daymet_dir.mkdir()
    (daymet_dir / "climate.parquet").write_bytes(b"fake parquet data")

    yield {
        "base": base,
        "sources": [ebird_dir, daymet_dir],
        "archive": archive
    }

    # Cleanup
    shutil.rmtree(base)


def test_run_archive_pipeline(temp_env):
    """Test that the pipeline correctly copies files and generates a manifest."""
    sources = temp_env["sources"]
    archive_dest = temp_env["archive"]
    manifest_path = archive_dest / "manifest.json"

    result = run_archive_pipeline(sources, archive_dest, manifest_path)

    # Assertions
    assert result["status"] == "success"
    assert result["total_files"] == 3  # data.csv, meta.json, climate.parquet
    assert "data.csv" in result["files"]
    assert "subdir/meta.json" in result["files"]
    assert "climate.parquet" in result["files"]

    # Verify file existence
    assert archive_dest.exists()
    assert (archive_dest / "data.csv").exists()
    assert (archive_dest / "subdir" / "meta.json").exists()
    assert (archive_dest / "climate.parquet").exists()

    # Verify manifest content
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        manifest_content = json.load(f)
    assert manifest_content["total_files"] == 3
    assert "files" in manifest_content
    assert "archive_destination" in manifest_content