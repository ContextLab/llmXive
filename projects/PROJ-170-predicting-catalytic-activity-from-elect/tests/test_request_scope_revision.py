"""
Unit test for the T015 scope‑revision request script.

The test verifies that:
1. The JSON file ``outputs/scope_revision_request.json`` is created.
2. The file contains the required fields:
   - ``request_id``
   - ``missing_dataset``
   - ``impact``
   - ``proposed_action``
3. ``data/checksums.txt`` contains a line with the filename and a valid SHA‑256 hash.
"""

import json
import re
from pathlib import Path

import pytest

# Import the script's main function to trigger execution
from request_scope_revision import main as run_script

@pytest.fixture(scope="module")
def run_and_collect():
    """Execute the script once for the whole test module."""
    exit_code = run_script()
    assert exit_code == 0, "Scope‑revision script exited with non‑zero status"
    # Paths used by the script
    json_path = Path("outputs") / "scope_revision_request.json"
    checksum_path = Path("data") / "checksums.txt"
    return json_path, checksum_path

def test_json_file_exists(run_and_collect):
    json_path, _ = run_and_collect
    assert json_path.is_file(), f"Expected JSON file at {json_path}"

def test_json_structure(run_and_collect):
    json_path, _ = run_and_collect
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Required fields
    required_fields = {"request_id", "missing_dataset", "impact", "proposed_action"}
    missing = required_fields - payload.keys()
    assert not missing, f"Missing required fields in JSON: {missing}"

    # ``request_id`` should be a UUID4 string
    uuid_regex = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    assert uuid_regex.match(payload["request_id"]), "request_id is not a valid UUID4"

def test_checksum_recorded(run_and_collect):
    _, checksum_path = run_and_collect
    assert checksum_path.is_file(), f"Checksum file missing at {checksum_path}"

    with open(checksum_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Find the line corresponding to the JSON file
    matching = [ln for ln in lines if ln.startswith("scope_revision_request.json ")]
    assert matching, "Checksum entry for scope_revision_request.json not found"

    # Verify the hash looks like a SHA‑256 hex string (64 hex chars)
    _, hash_str = matching[0].split()
    assert re.fullmatch(r"[0-9a-f]{64}", hash_str, re.IGNORECASE), "Invalid SHA‑256 hash format"