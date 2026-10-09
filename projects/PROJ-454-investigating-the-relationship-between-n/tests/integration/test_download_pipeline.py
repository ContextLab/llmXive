"""
Integration test that runs the download script on a very small,
publicly‑available OpenNeuro dataset (ds000246) and checks that
at least one EDF/BDF file appears under ``data/raw/ds000246`` and that
``data/raw/checksums.json`` contains a matching entry.
This test will be executed in CI where network access is allowed.
"""
import json
from pathlib import Path
import subprocess
import sys

def test_download_pipeline():
    # Run the script as a subprocess (no arguments required)
    result = subprocess.run(
        [sys.executable, "code/01_download_data.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    raw_dir = Path("data/raw")
    # At least one .edf or .bdf file must exist for ds000246
    eeg_files = list(raw_dir.glob("ds000246/**/*.edf")) + list(
        raw_dir.glob("ds000246/**/*.bdf")
    )
    assert len(eeg_files) > 0, "No EEG files were downloaded for ds000246"

    checksum_path = raw_dir / "checksums.json"
    assert checksum_path.is_file(), "checksums.json missing"

    with checksum_path.open() as f:
        checksums = json.load(f)
    # Verify that each downloaded file has an entry in the manifest.
    paths_in_manifest = {Path(rec["file_path"]).resolve() for rec in checksums}
    for f in eeg_files:
        assert f.resolve() in paths_in_manifest, f"Missing checksum for {f}"