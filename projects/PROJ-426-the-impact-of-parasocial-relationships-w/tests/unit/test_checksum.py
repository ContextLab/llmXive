"""
Unit tests for the checksum utility (src/utils/checksum.py).

The tests create a temporary ``data`` hierarchy with a few small files,
invoke the checksum logic, and verify that:

1. All files are present in the generated manifest.
2. The recorded checksums match the expected SHA‑256 digests.
3. The manifest is written to ``data/artifact_manifest.yaml``.
"""

import hashlib
from pathlib import Path

import pytest

# Add the project ``code`` directory to ``sys.path`` so that imports work
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from src.utils.checksum import compute_sha256, gather_artifact_checksums, write_manifest, main
from llmxive_toolkit import paths


@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """
    Create a temporary ``data`` directory with a few files.
    The fixture replaces the real ``data`` folder for the duration of the test.
    """
    # Override the llmxive ``paths.data`` root for this test
    original_data_root = paths.root / "data"
    backup = original_data_root.parent / "data_backup"
    if original_data_root.exists():
        original_data_root.rename(backup)

    # Populate the temporary data directory
    (tmp_path / "raw").mkdir(parents=True)
    (tmp_path / "processed").mkdir(parents=True)

    file_contents = {
        "raw/file1.txt": b"Hello world",
        "raw/file2.csv": b"a,b,c\n1,2,3\n",
        "processed/file3.parquet": b"PAR1"  # not a real parquet but sufficient for checksum
    }

    for rel_path, content in file_contents.items():
        p = tmp_path / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    # Monkey‑patch ``paths.data`` to point to our temporary location
    paths.data = lambda *args: Path(tmp_path, *args)

    yield tmp_path

    # Restore original ``paths.data`` behaviour
    paths.data = lambda *args: Path(paths.root, "data", *args)
    if backup.exists():
        if original_data_root.exists():
            # Clean up any stray files created during the test run
            for child in original_data_root.iterdir():
                if child.is_file():
                    child.unlink()
                else:
                    # Recursively remove directories
                    import shutil
                    shutil.rmtree(child)
        backup.rename(original_data_root)


def test_compute_sha256(tmp_path: Path):
    """Direct checksum calculation should match hashlib output."""
    test_file = tmp_path / "sample.txt"
    content = b"checksum test"
    test_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    assert compute_sha256(test_file) == expected


def test_gather_and_write_manifest(temp_data_dir: Path):
    """
    End‑to‑end test that the manifest contains entries for all files
    and that the written YAML can be read back correctly.
    """
    data_root = paths.data()
    assert data_root == temp_data_dir

    manifest = gather_artifact_checksums(data_root)

    # Expected relative paths (POSIX style) inside the project
    expected_paths = {
        "data/raw/file1.txt",
        "data/raw/file2.csv",
        "data/processed/file3.parquet"
    }
    assert set(manifest.keys()) == expected_paths

    # Verify each checksum matches manual calculation
    for rel_path, checksum in manifest.items():
        absolute_path = paths.root / rel_path
        with absolute_path.open("rb") as f:
            content = f.read()
        assert checksum == hashlib.sha256(content).hexdigest()

    # Write the manifest and verify the file exists
    manifest_path = paths.data("artifact_manifest.yaml")
    write_manifest(manifest, manifest_path)

    assert manifest_path.exists()

    # Load the YAML back and compare
    loaded = yaml.safe_load(manifest_path.read_text())
    assert loaded == manifest


def test_main_creates_manifest(temp_data_dir: Path):
    """
    Running the script's ``main`` function should produce the manifest
    at the expected location without raising.
    """
    manifest_path = paths.data("artifact_manifest.yaml")
    # Ensure no leftover manifest from previous runs
    if manifest_path.exists():
        manifest_path.unlink()

    # Execute the main routine
    main()

    assert manifest_path.is_file()
    loaded = yaml.safe_load(manifest_path.read_text())
    # Should contain exactly the three temporary files
    assert set(loaded.keys()) == {
        "data/raw/file1.txt",
        "data/raw/file2.csv",
        "data/processed/file3.parquet"
    }