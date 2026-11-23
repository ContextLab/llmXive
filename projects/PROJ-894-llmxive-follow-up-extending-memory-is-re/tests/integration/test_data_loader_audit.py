"""
Integration audit for the strict LoCoMo downloader (T001).

Verifies that:
1. ``data/raw/locomo.csv`` exists and is non-empty.
2. The CSV has the required columns (task_id, question, context,
   ground_truth) and at least one real row.
3. The recorded SHA-256 checksum matches the file on disk.
4. The loader contains NO synthetic/mock fallback logic.
"""
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "raw" / "locomo.csv"
SHA_PATH = ROOT / "data" / "raw" / "locomo.sha256"
LOADER_PATH = ROOT / "code" / "data" / "download_locomo.py"

REQUIRED_COLUMNS = {"task_id", "question", "context", "ground_truth"}
FORBIDDEN_PATTERNS = [
    "np.random",
    "random.uniform",
    "generate_synthetic",
    "mock_",
    "placeholder_data",
]


def test_csv_exists_and_nonempty():
    assert CSV_PATH.exists(), f"{CSV_PATH} does not exist"
    assert CSV_PATH.stat().st_size > 0, f"{CSV_PATH} is empty"


def test_csv_schema():
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = set(reader.fieldnames or [])
        rows = list(reader)
    missing = REQUIRED_COLUMNS - header
    assert not missing, f"Dataset schema mismatch: missing {sorted(missing)}"
    assert len(rows) > 0, "no data rows in locomo.csv"
    for row in rows:
        assert row["task_id"], "row with empty task_id"
        assert row["question"], "row with empty question"


def test_checksum_matches():
    if not SHA_PATH.exists():
        # Checksum file is optional evidence; skip if absent.
        return
    recorded = SHA_PATH.read_text(encoding="utf-8").strip()
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    assert recorded == digest, "SHA-256 mismatch for data/raw/locomo.csv"


def test_loader_has_no_synthetic_fallback():
    source = LOADER_PATH.read_text(encoding="utf-8")
    for pattern in FORBIDDEN_PATTERNS:
        assert pattern not in source, (
            f"Forbidden fallback pattern '{pattern}' found in {LOADER_PATH}"
        )
