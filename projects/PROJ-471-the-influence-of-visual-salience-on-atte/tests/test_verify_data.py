import json
import subprocess
import shutil
from pathlib import Path
import pytest

from llmxive_toolkit import paths

def run_verify():
    """Helper to run the verification script as a module."""
    return subprocess.run(
        ["python", "-m", "code.ingestion.verify_data"],
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
    )

def setup_dummy_dataset(raw_root: Path):
    """Creates a minimal valid dataset structure for testing."""
    ds_dir = raw_root / "ds003123"
    ds_dir.mkdir(parents=True, exist_ok=True)
    (ds_dir / "stimuli").mkdir(parents=True, exist_ok=True)
    (ds_dir / "sub-01").mkdir(parents=True, exist_ok=True)

    # Create a few dummy files
    (ds_dir / "stimuli" / "img1.png").write_bytes(b"fake-image-data")
    (ds_dir / "sub-01" / "gaze.csv").write_text("trial,x,y\n1,10,20")
    return ds_dir

def teardown_dummy_dataset(raw_root: Path):
    """Cleans up the dummy dataset and checksums."""
    ds_dir = raw_root / "ds003123"
    if ds_dir.is_dir():
        shutil.rmtree(ds_dir)
    checksum_path = raw_root / "checksums.json"
    if checksum_path.is_file():
        checksum_path.unlink()

def test_verify_success():
    """Test that a valid dataset structure is verified successfully."""
    raw_root = paths.data("raw")
    setup_dummy_dataset(raw_root)
    try:
        result = run_verify()
        assert result.returncode == 0
        assert "Dataset verification succeeded" in result.stdout

        checksum_path = raw_root / "checksums.json"
        assert checksum_path.is_file()
        with checksum_path.open() as f:
            manifest = json.load(f)
        # Expect two files: the image and the gaze csv
        assert len(manifest["files"]) == 2
    finally:
        teardown_dummy_dataset(raw_root)

def test_verify_missing_dir():
    """Test that missing dataset directory raises DATA_MISSING_001."""
    raw_root = paths.data("raw")
    teardown_dummy_dataset(raw_root)

    result = run_verify()
    assert result.returncode != 0
    assert "DATA_MISSING_001" in result.stderr
    assert "ds003123 incomplete" in result.stderr

def test_verify_incomplete_structure():
    """Test that missing stimuli/ or sub-*/ raises DATA_MISSING_001."""
    raw_root = paths.data("raw")
    ds_dir = raw_root / "ds003123"
    ds_dir.mkdir(parents=True, exist_ok=True)
    # Missing stimuli/ and sub-*/

    try:
        result = run_verify()
        assert result.returncode != 0
        assert "DATA_MISSING_001" in result.stderr
        assert "ds003123 incomplete" in result.stderr
    finally:
        teardown_dummy_dataset(raw_root)

def test_verify_checksum_generation():
    """Test that the manifest is written correctly with hashes."""
    raw_root = paths.data("raw")
    setup_dummy_dataset(raw_root)
    try:
        run_verify()
        with (raw_root / "checksums.json").open() as f:
            manifest = json.load(f)
        
        # Verify the relative path is correct
        assert "ds003123/stimuli/img1.png" in manifest["files"]
        # Verify the hash is a valid hex string (64 chars for SHA-256)
        hash_val = manifest["files"]["ds003123/stimuli/img1.png"]
        assert len(hash_val) == 64
    finally:
        teardown_dummy_dataset(raw_root)