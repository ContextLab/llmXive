"""
Integration test for the ``code/data/curate_reference_substructures.py`` script.

The test invokes the script (as a module) and checks that:
  1. ``data/raw/reference_substructures_raw.csv`` exists after execution.
  2. The CSV contains the required columns: ``smiles``, ``source_doi``, ``description``.
  3. ``data/raw/checksums.json`` exists and contains a ``reference_substructures``
     entry whose ``hash`` matches the SHA‑256 of the CSV file.
The test will fail loudly if any of these conditions are not met,
ensuring that the curation step is reproducible and reliable.
"""

import json
import hashlib
from pathlib import Path

import pytest

from llmxive_toolkit import paths, get_logger

# Import the script as a module to run its ``main`` function
import importlib.util

SCRIPT_PATH = paths.code("data", "curate_reference_substructures.py")

@pytest.fixture(scope="module")
def run_curation():
    """Execute the curation script once for the whole test module."""
    spec = importlib.util.spec_from_file_location(
        "curate_reference_substructures", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    # The script's ``main`` runs on import; if not, call explicitly
    if hasattr(module, "main"):
        module.main()
    return module

def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_reference_substructures_created(run_curation):
    csv_path = paths.data("raw", "reference_substructures_raw.csv")
    assert csv_path.is_file(), f"CSV not found at {csv_path}"

    # Verify required columns are present
    import pandas as pd

    df = pd.read_csv(csv_path)
    required = {"smiles", "source_doi", "description"}
    missing = required.difference(df.columns.str.lower())
    assert not missing, f"Missing columns in CSV: {missing}"

def test_checksums_entry(run_curation):
    csv_path = paths.data("raw", "reference_substructures_raw.csv")
    checksums_path = paths.data("raw", "checksums.json")
    assert checksums_path.is_file(), f"checksums.json not found at {checksums_path}"

    with checksums_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "reference_substructures" in manifest, "Entry missing in checksums.json"
    entry = manifest["reference_substructures"]
    expected_hash = calculate_sha256(csv_path)
    assert entry["hash"] == expected_hash, (
        f"Checksum mismatch: expected {expected_hash}, got {entry.get('hash')}"
    )
    assert entry["file"] == csv_path.name
    assert Path(entry["path"]).resolve() == csv_path.resolve()