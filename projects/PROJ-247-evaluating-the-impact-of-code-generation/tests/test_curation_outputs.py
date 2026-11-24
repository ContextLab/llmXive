"""
Pytest suite for verifying the outputs of the repository curation step (T002).
The script `code/01_data_curation.py` should produce two CSV files under `data/raw/`:
  - repo_list.csv
  - repo_metadata.csv

The tests assert that:
  * Both files exist.
  * Both files contain at least 50 rows (including header, so >=51 lines total).
  * `repo_list.csv` has columns: repo_id, clone_path, clone_status.
  * `repo_metadata.csv` has columns: repo_id, stars, created_at, updated_at, total_loc.
  * Each row has non‑empty values for required fields.
"""
import csv
from pathlib import Path

REPO_LIST_PATH = Path("data/raw/repo_list.csv")
REPO_METADATA_PATH = Path("data/raw/repo_metadata.csv")

def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames
    return headers, rows

def test_repo_list_exists():
    assert REPO_LIST_PATH.exists(), f"{REPO_LIST_PATH} does not exist"

def test_repo_metadata_exists():
    assert REPO_METADATA_PATH.exists(), f"{REPO_METADATA_PATH} does not exist"

def test_repo_list_structure():
    headers, rows = _read_csv(REPO_LIST_PATH)
    expected = {"repo_id", "clone_path", "clone_status"}
    assert set(headers) == expected, f"repo_list.csv headers mismatch: {headers}"
    assert len(rows) >= 50, f"Expected at least 50 repository rows, got {len(rows)}"
    for i, row in enumerate(rows):
        assert row["repo_id"], f"Row {i} missing repo_id"
        assert row["clone_path"], f"Row {i} missing clone_path"
        assert row["clone_status"] in {"success", "failed"}, f"Row {i} has invalid clone_status: {row['clone_status']}"

def test_repo_metadata_structure():
    headers, rows = _read_csv(REPO_METADATA_PATH)
    expected = {"repo_id", "stars", "created_at", "updated_at", "total_loc"}
    assert set(headers) == expected, f"repo_metadata.csv headers mismatch: {headers}"
    assert len(rows) >= 50, f"Expected at least 50 metadata rows, got {len(rows)}"
    for i, row in enumerate(rows):
        assert row["repo_id"], f"Row {i} missing repo_id"
        assert row["stars"], f"Row {i} missing stars"
        assert row["created_at"], f"Row {i} missing created_at"
        assert row["updated_at"], f"Row {i} missing updated_at"
        # total_loc can be zero if cloning failed, but the field must be present
        assert "total_loc" in row, f"Row {i} missing total_loc"