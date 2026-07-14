"""Unit tests for ``code/11_external_outcome_check.py``.

The tests verify that the script correctly writes a limitation note when
MCI conversion data is absent and does not write a note when the data is
present.
"""

import csv
from pathlib import Path
import importlib.util
import sys
import tempfile

import pytest

# Helper to import the module from its source file without executing it on import
def import_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)

@pytest.fixture
def module_under_test(temp_dir):
    """Import the external outcome check module and monkey‑patch its paths."""
    module_path = Path(__file__).resolve().parents[2] / "code" / "11_external_outcome_check.py"
    mod = import_module_from_path("external_outcome_check", module_path)

    # Redirect the file locations to the temporary directory
    mod.PARTICIPANTS_TSV = temp_dir / "participants.tsv"
    mod.LIMITATIONS_FILE = temp_dir / "limitations.txt"
    return mod

def write_participants_tsv(path: Path, rows: list[dict], fieldnames: list[str]):
    """Write a minimal participants.tsv file."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def test_limitation_written_when_mci_column_missing(module_under_test, temp_dir):
    # Create participants.tsv without any MCI column
    rows = [
        {"participant_id": "sub-01", "age": "70"},
        {"participant_id": "sub-02", "age": "68"},
    ]
    write_participants_tsv(
        module_under_test.PARTICIPANTS_TSV,
        rows,
        fieldnames=["participant_id", "age"],
    )

    exit_code = module_under_test.main()
    assert exit_code == 0
    # The limitation note should have been created
    assert module_under_test.LIMITATIONS_FILE.is_file()
    content = module_under_test.LIMITATIONS_FILE.read_text()
    assert "MCI conversion data not available" in content

def test_no_limitation_when_mci_column_present_and_populated(module_under_test, temp_dir):
    # Create participants.tsv with a valid MCI column containing data
    rows = [
        {"participant_id": "sub-01", "MCI_conversion": "yes"},
        {"participant_id": "sub-02", "MCI_conversion": ""},
    ]
    write_participants_tsv(
        module_under_test.PARTICIPANTS_TSV,
        rows,
        fieldnames=["participant_id", "MCI_conversion"],
    )

    exit_code = module_under_test.main()
    assert exit_code == 0
    # No limitation file should be written because data exists
    assert not module_under_test.LIMITATIONS_FILE.is_file()

def test_limitation_written_when_mci_column_present_but_empty(module_under_test, temp_dir):
    # Create participants.tsv with the MCI column but no non‑empty entries
    rows = [
        {"participant_id": "sub-01", "MCI_conversion": ""},
        {"participant_id": "sub-02", "MCI_conversion": "   "},
    ]
    write_participants_tsv(
        module_under_test.PARTICIPANTS_TSV,
        rows,
        fieldnames=["participant_id", "MCI_conversion"],
    )

    exit_code = module_under_test.main()
    assert exit_code == 0
    assert module_under_test.LIMITATIONS_FILE.is_file()
    content = module_under_test.LIMITATIONS_FILE.read_text()
    assert "MCI conversion data not available" in content

def test_limitation_written_when_participants_file_missing(module_under_test, temp_dir):
    # Ensure the participants.tsv does not exist
    if module_under_test.PARTICIPANTS_TSV.is_file():
        module_under_test.PARTICIPANTS_TSV.unlink()

    exit_code = module_under_test.main()
    assert exit_code == 0
    assert module_under_test.LIMITATIONS_FILE.is_file()
    content = module_under_test.LIMITATIONS_FILE.read_text()
    assert "participants.tsv not found" in content