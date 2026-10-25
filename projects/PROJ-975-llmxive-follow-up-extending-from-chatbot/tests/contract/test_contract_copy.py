"""
Test that contract schema files have been copied verbatim.
The script `code/copy_contracts.py` writes a JSON mapping of SHA‑256
hashes for each contract file. This test loads that mapping and asserts
that the source and destination hashes match for every file.
"""
import json
import os
import pytest
from llmxive_toolkit import paths

@pytest.fixture
def hash_mapping():
    """Load the JSON mapping produced by copy_contracts.py."""
    json_path = paths.data("raw", "contract_hashes.json")
    if not os.path.exists(json_path):
        pytest.fail(f"Hash mapping file not found at {json_path}. Did you run copy_contracts.py?")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_hashes_match(hash_mapping):
    """
    Ensure that for each contract file the source and destination
    SHA‑256 hashes are identical, guaranteeing a verbatim copy.
    """
    assert isinstance(hash_mapping, dict), "Hash mapping should be a dictionary."
    for filename, hashes in hash_mapping.items():
        assert "src_hash" in hashes, f"Missing src_hash for {filename}"
        assert "dst_hash" in hashes, f"Missing dst_hash for {filename}"
        src = hashes["src_hash"]
        dst = hashes["dst_hash"]
        assert src == dst, f"Hash mismatch for {filename}: {src} != {dst}"