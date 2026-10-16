"""
Test suite for the reproducibility manifest generator (T051).

The test runs the ``code/generate_manifest.py`` script and verifies that
the produced ``manifest.json`` contains the required top‑level keys and
that the JSON structure is well‑formed.
"""

import json
import subprocess
from pathlib import Path

def run_manifest_generator():
    """
    Execute the manifest generation script. The script is expected to exit
    with status 0 and create ``manifest.json`` in the repository root.
    """
    repo_root = Path(__file__).resolve().parents[2]  # tests/ -> repo root
    script_path = repo_root / "code" / "generate_manifest.py"
    result = subprocess.run(
        ["python", str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return repo_root / "manifest.json"

def test_manifest_structure():
    """
    Verify that the generated manifest contains all required sections.
    """
    manifest_file = run_manifest_generator()
    assert manifest_file.is_file(), "manifest.json was not created"

    with manifest_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Required top‑level keys
    required_keys = {"commit_hash", "datasets", "software_versions", "checksums"}
    assert required_keys.issubset(data.keys()), f"Missing keys in manifest: {required_keys - data.keys()}"

    # Basic sanity checks for each section
    assert isinstance(data["datasets"], dict) and data["datasets"], "datasets section must be a non‑empty dict"
    assert isinstance(data["software_versions"], dict), "software_versions must be a dict"
    assert isinstance(data["checksums"], list), "checksums must be a list"

    # Ensure the commit hash is a non‑empty string (\"N/A\" is acceptable if Git is unavailable)
    assert isinstance(data["commit_hash"], str) and len(data["commit_hash"]) > 0, "commit_hash must be a non‑empty string"

    # Clean‑up: the test suite may be run multiple times; ensure the file can be overwritten
    # (no explicit removal needed – the generator overwrites on each run).