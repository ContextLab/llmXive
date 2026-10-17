"""
Unit test for the T006 taxonomy download script.

The test checks that:
* The script exits with status 0.
* The expected JSON file is created under ``data/taxonomy/survey_2023.json``.
* The file is valid JSON and contains a top‑level ``tags`` array.
* The SHA‑256 checksum of the produced file matches the published value
  defined in the script (ensuring the “fail loudly” contract is honoured).
"""

import json
import hashlib
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

# Path to the script under test
SCRIPT = Path("code/data/download_taxonomy.py")

def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def test_taxonomy_download_runs_successfully():
    """
    Execute the script and verify the output file.
    """
    # Ensure a clean state: remove the output if it exists.
    output_path = paths.data("taxonomy", "survey_2023.json")
    if output_path.is_file():
        output_path.unlink()

    # Run the script as a subprocess to capture the exit code.
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # The script must exit with code 0.
    assert result.returncode == 0, f"Script failed (code {result.returncode}): {result.stderr}"

    # The output file must now exist.
    assert output_path.is_file(), f"Expected taxonomy file not found at {output_path}"

    # Verify the JSON structure.
    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict), "Taxonomy JSON should be an object"
    assert "tags" in data, "Taxonomy JSON must contain a 'tags' key"
    assert isinstance(data["tags"], list), "'tags' must be a list"

    # Verify checksum matches the published value (the script’s constant).
    expected_checksum = "b32d843c60537f7b23e2b43f50186f1c9f14a364d128a2fa677e38c6c0d628ab"
    actual_checksum = compute_sha256(output_path)
    assert (
        actual_checksum == expected_checksum
    ), f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"