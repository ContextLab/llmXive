"""Integration test for the Pantheon+ download script (task T002).

The test runs the ``download_pantheon.py`` script, then checks:
  * The FITS file exists at the expected location.
  * The SHA‑256 checksum recorded in ``metadata.json`` matches the
    actual checksum of the downloaded file.
  * The FITS header contains the required columns.
  * The project state YAML contains the checksum entry.
"""
import json
import pathlib
import sys

import pytest
import yaml
from astropy.io import fits

from llmxive_toolkit import paths

# Import the script as a module to invoke its ``main`` function.
sys.path.append(str(pathlib.Path(__file__).parents[3] / "code"))
import download_pantheon

@pytest.mark.integration
def test_download_and_verify(tmp_path, monkeypatch):
    # Ensure a clean environment: remove any existing raw files.
    raw_dir = paths.data("raw")
    for p in raw_dir.iterdir():
        p.unlink()

    # Run the script (it will download the real dataset).
    download_pantheon.main()

    # 1️⃣ Verify FITS file existence.
    fits_path = raw_dir / "pantheon_plus.fits"
    assert fits_path.is_file(), "FITS file was not created."

    # 2️⃣ Verify checksum matches metadata.
    metadata_path = raw_dir / "metadata.json"
    assert metadata_path.is_file(), "metadata.json was not created."
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Re‑compute checksum independently.
    import hashlib

    def compute_sha256(path: pathlib.Path) -> str:
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    expected_checksum = compute_sha256(fits_path)
    assert meta["sha256"] == expected_checksum, "Checksum mismatch in metadata."

    # 3️⃣ Verify required FITS columns.
    with fits.open(fits_path) as hdul:
        table = hdul[1].data
        cols = set(table.columns.names)
        required = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}
        missing = required - cols
        assert not missing, f"Missing columns in FITS: {missing}"

    # 4️⃣ Verify state YAML entry.
    state_path = pathlib.Path(__file__).parents[4] / "state" / "projects" / "PROJ-753-testing-the-isotropy-of-cosmic-expansion.yaml"
    assert state_path.is_file(), "State YAML file was not created."
    with open(state_path, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f) or {}
    artifact_hashes = state.get("artifact_hashes", {})
    assert artifact_hashes.get("pantheon_plus.fits") == expected_checksum, "Checksum not recorded in state YAML."