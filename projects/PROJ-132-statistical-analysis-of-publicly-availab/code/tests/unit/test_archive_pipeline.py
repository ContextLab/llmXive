import os
import tempfile
import shutil
from pathlib import Path
import pytest
import json

from src.data.archive_pipeline import run_archive_pipeline

@pytest.fixture
def temp_env():
    """Setup temporary directories for pipeline testing."""
    base = tempfile.mkdtemp()
    src_dir = Path(base) / "source"
    src_dir.mkdir()
    (src_dir / "data.txt").write_text("test data")
    (src_dir / "sub").mkdir()
    (src_dir / "sub" / "nested.txt").write_text("nested data")

    yield {
        "base": Path(base),
        "source": src_dir,
        "archive": Path(base) / "archive",
        "manifest": Path(base) / "manifest.json"
    }

    shutil.rmtree(base, ignore_errors=True)

def test_run_archive_pipeline(temp_env):
    run_archive_pipeline(
        source_dirs=[str(temp_env["source"])],
        archive_root=str(temp_env["archive"]),
        checksum_manifest=str(temp_env["manifest"])
    )

    assert temp_env["archive"].exists()
    assert (temp_env["archive"] / "data.txt").exists()
    assert (temp_env["archive"] / "sub" / "nested.txt").exists()
    assert temp_env["manifest"].exists()

    with open(temp_env["manifest"]) as f:
        manifest = json.load(f)

    assert "files" in manifest
    assert len(manifest["files"]) == 2
    paths = [f["path"] for f in manifest["files"]]
    assert "data.txt" in paths
    assert "sub/nested.txt" in paths
