"""Unit tests for the download‑and‑filter script."""

import csv
from pathlib import Path

import pytest

# Import the functions directly for isolated testing
from code import (
    ensure_dir,
    read_participants_tsv,
    is_eligible,
    filter_eligible_subjects,
    limit_subjects,
    write_eligible_csv,
    write_excluded_log,
)


@pytest.fixture
def tmp_raw_dir(tmp_path):
    """Create a temporary raw directory with a synthetic participants.tsv."""
    raw_dir = tmp_path / "data" / "raw" / "ds000246"
    raw_dir.mkdir(parents=True)
    participants = raw_dir / "participants.tsv"
    # Minimal TSV with two subjects, each having two timepoints for both scores
    participants.write_text(
        "participant_id\\tmmse_1\\tmmse_2\\tmoca_1\\tmoca_2\\n"
        "sub-01\\t30\\t28\\t28\\t27\\n"
        "sub-02\\t\\t\\t\\t\\n"
    )
    return raw_dir


def test_read_participants_tsv(tmp_raw_dir):
    rows = read_participants_tsv(tmp_raw_dir / "participants.tsv")
    assert len(rows) == 2
    assert rows[0]["participant_id"] == "sub-01"


def test_is_eligible():
    row_ok = {
        "participant_id": "sub-01",
        "mmse_1": "30",
        "mmse_2": "28",
        "moca_1": "28",
        "moca_2": "27",
    }
    row_bad = {
        "participant_id": "sub-02",
        "mmse_1": "",
        "mmse_2": "",
        "moca_1": "",
        "moca_2": "",
    }
    assert is_eligible(row_ok)[0] is True
    assert is_eligible(row_bad)[0] is False


def test_filter_and_limit(tmp_raw_dir):
    rows = read_participants_tsv(tmp_raw_dir / "participants.tsv")
    eligible, excluded = filter_eligible_subjects(rows)
    assert len(eligible) == 1
    assert len(excluded) == 1
    limited = limit_subjects(eligible, max_n=100)
    assert limited == eligible


def test_write_outputs(tmp_path):
    out_dir = tmp_path / "out"
    eligible = [
        {"participant_id": "sub-01"},
    ]
    excluded = [
        ({"participant_id": "sub-02"}, "both MMSE and MoCA missing at ≥2 timepoints")
    ]
    eligible_csv = out_dir / "eligible_subjects.csv"
    excluded_log = out_dir / "excluded_subjects.log"
    write_eligible_csv(eligible, eligible_csv)
    write_excluded_log(excluded, excluded_log)

    # Verify CSV
    with eligible_csv.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    assert rows[0] == ["participant_id"]
    assert rows[1] == ["sub-01"]

    # Verify log
    content = excluded_log.read_text()
    assert "sub-02" in content
    assert "both MMSE and MoCA missing" in content