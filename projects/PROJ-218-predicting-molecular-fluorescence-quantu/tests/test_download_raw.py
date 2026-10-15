"""
test_download_raw.py
--------------------
Integration test for the T001 download and seed‑pinning script.
The test runs the script (via subprocess) and checks that:
* The raw data files exist under ``data/raw/``.
* ``checksums.txt`` contains entries for both files.
* ``results/seeds.json`` exists and contains the expected keys.
"""

import subprocess
import json
import sys
from pathlib import Path

from llmxive_toolkit import paths

def test_download_and_seeds(tmp_path, monkeypatch):
    # Ensure we run in the project root (the test runner does this)
    # Run the script
    result = subprocess.run(
        [sys.executable, "-m", "code.data.download_raw"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify raw files
    raw_dir = paths.data("raw")
    assert (raw_dir / "smiles.parquet").is_file()
    assert (raw_dir / "fqy.json").is_file()

    # Verify checksums file
    checksum_file = raw_dir / "checksums.txt"
    assert checksum_file.is_file()
    content = checksum_file.read_text().splitlines()
    assert any("smiles.parquet" in line for line in content)
    assert any("fqy.json" in line for line in content)

    # Verify seeds JSON
    seeds_json = paths.results("seeds.json")
    assert seeds_json.is_file()
    with open(seeds_json, "r", encoding="utf-8") as f:
        seeds = json.load(f)
    expected_keys = {"pythonhashseed", "random_seed", "numpy_seed", "torch_seed"}
    assert expected_keys.issubset(seeds.keys())
