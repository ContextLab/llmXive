"""
Integration test for ``code/ingestion/download_data.py``.

The test runs the script (which may download the OpenNeuro dataset if it is not
already present) and then checks that:

1. The script exits with status code ``0``.
2. The checksum manifest ``data/raw/checksums.json`` exists.
3. The manifest contains at least one file entry and that each entry includes
   the required keys (``path``, ``sha256``, ``size``).
"""
import subprocess
import json
from pathlib import Path

import pytest

@pytest.mark.integration
def test_download_and_checksum(tmp_path, monkeypatch):
    """
    Run the download script and verify the produced checksum manifest.
    """
    # Ensure we are operating from the project root.
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "code" / "ingestion" / "download_data.py"

    # Execute the script.
    result = subprocess.run(
        ["python", str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    # The script must exit cleanly.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the checksum file exists.
    checksum_path = project_root / "data" / "raw" / "checksums.json"
    assert checksum_path.is_file(), "checksums.json was not created."

    # Load and validate the JSON structure.
    with checksum_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert isinstance(manifest, dict), "Manifest should be a JSON object."
    assert "files" in manifest, "Manifest missing 'files' key."
    assert isinstance(manifest["files"], list), "'files' should be a list."
    assert len(manifest["files"]) > 0, "Manifest contains no file entries."

    # Check required keys in the first entry.
    first_entry = manifest["files"][0]
    for key in ("path", "sha256", "size"):
        assert key in first_entry, f"Manifest entry missing required key: {key}"
