"""
test_gen_synthetic.py
---------------------
Integration test for the deterministic synthetic dataset generator (task T015).

The test runs the generator once, then checks that:
  1. The CSV file exists at the expected location.
  2. Exactly 10 000 rows are present.
  3. The file‑level checksum stored in ``data/raw/checksums.json`` matches
     the actual checksum of the generated CSV (ensuring reproducibility).
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.gen_synthetic import main as gen_main

CSV_PATH = Path("data/raw/synthetic_fatigue.csv")
CHECKSUMS_PATH = Path("data/raw/checksums.json")

@pytest.fixture(scope="module")
def run_generator():
    """Execute the synthetic generator once for the whole test module."""
    gen_main()
    assert CSV_PATH.is_file(), f"Synthetic CSV not found at {CSV_PATH}"
    assert CHECKSUMS_PATH.is_file(), f"Checksums file not found at {CHECKSUMS_PATH}"
    return {
        "csv_path": CSV_PATH,
        "checksums": json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8")),
    }

def _file_checksum(path: Path) -> str:
    """Compute the SHA‑256 checksum of *path*."""
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_synthetic_file_exists_and_row_count(run_generator):
    """The synthetic CSV must exist and contain exactly 10 000 rows."""
    df = pd.read_csv(run_generator["csv_path"])
    assert len(df) == 10_000, f"Expected 10 000 rows, got {len(df)}"

def test_checksum_consistency(run_generator):
    """The checksum recorded in checksums.json must match the actual file checksum."""
    csv_path = run_generator["csv_path"]
    recorded = run_generator["checksums"].get(str(csv_path))
    assert recorded is not None, f"No checksum entry for {csv_path}"
    actual = _file_checksum(csv_path)
    assert actual == recorded, f"Checksum mismatch: recorded {recorded}, actual {actual}"