"""
test_generate_manifest.py
-------------------------

Minimal test that ensures the manifest is created and contains the expected top‑level keys.
The test runs the ``generate_manifest.py`` script (via subprocess) and then loads the
resulting JSON file to assert the presence of:

* ``datasets``
* ``commit_hash``
* ``software_versions``
* ``checksums``

The test deliberately does **not** validate the exact values – those depend on the
environment (e.g. the current Git commit).  It only checks that the structure is
correct and that at least one checksum entry exists, confirming that the script
performed a file‑walk.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_manifest_structure(tmp_path):
    # Run the manifest generator script from the project root
    repo_root = Path(__file__).resolve().parents[2]  # repository root
    script_path = repo_root / "code" / "generate_manifest.py"

    # Execute the script; any failure will raise a CalledProcessError
    subprocess.run([sys.executable, str(script_path)], check=True)

    manifest_file = repo_root / "manifest.json"
    assert manifest_file.is_file(), "manifest.json was not created"

    with manifest_file.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Top‑level keys
    for key in ("datasets", "commit_hash", "software_versions", "checksums"):
        assert key in manifest, f"Missing top‑level key '{key}' in manifest"

    # Basic sanity checks
    assert isinstance(manifest["datasets"], dict) and manifest["datasets"], "datasets dict empty"
    assert isinstance(manifest["software_versions"], dict), "software_versions not a dict"
    assert isinstance(manifest["checksums"], dict) and manifest["checksums"], "checksums dict empty"

    # The commit hash should be a non‑empty string of hex characters
    commit = manifest["commit_hash"]
    assert isinstance(commit, str) and len(commit) >= 7, "commit_hash looks invalid"