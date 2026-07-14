"""Unit tests for the download-and-filter script (T017)."""

import csv
import json
import sys
from pathlib import Path

import pytest

# Import the functions we need to test directly
from code import (
    ensure_dir,
    download_file,
    read_participants_tsv,
    is_eligible,
    filter_eligible_subjects,
    limit_subjects,
    write_eligible_csv,
    write_excluded_log,
)

# NOTE: The real network download is not exercised in CI – we only test the
# pure‑python logic.  The `download_file` helper is exercised with a tiny
# local HTTP server in the integration test suite (not shown here).


@pytest.fixture
def sample_rows():
    """Return a small set of participant rows mimicking the real TSV."""
    return [
        {
            "participant_id": "sub-01",
            "MMSE_T1": "28",
            "MMSE_T2": "27",
            "MOCA_T1": "26",
            "MOCA_T2": "25",
        },
        {
            "participant_id": "sub-02",
            "MMSE_T1": "29",
            "MMSE_T2": "",
            "MOCA_T1": "27",
            "MOCA_T2": "27",
        },
        {
            "participant_id": "sub-03",
            "MMSE_T1": "",
            "MMSE_T2": "",
            "MOCA_T1": "",
            "MOCA_T2": "",
        },
    ]


def test_is_eligible_cases(sample_rows):
    """Check that eligibility logic correctly classifies rows."""
    eligible_flags = [is_eligible(r)[0] for r in sample_rows]
    # Only the first subject has both MMSE and MOCA at two timepoints
    assert eligible_flags == [True, False, False]


def test_filter_eligible_subjects(sample_rows):
    eligible, excluded = filter_eligible_subjects(sample_rows)
    assert len(eligible) == 1
    assert eligible[0]["participant_id"] == "sub-01"
    assert len(excluded) == 2
    # Ensure the reason strings are non‑empty for excluded rows
    for _, reason in excluded:
        assert reason


def test_limit_subjects(sample_rows):
    eligible, _ = filter_eligible_subjects(sample_rows)
    # Duplicate to have >1 eligible for limiting
    duplicated = eligible * 5
    limited = limit_subjects(duplicated, max_n=3, seed=123)
    assert len(limited) == 3
    # Deterministic ordering with the same seed
    ids_first_run = [r["participant_id"] for r in limited]
    limited_again = limit_subjects(duplicated, max_n=3, seed=123)
    ids_second_run = [r["participant_id"] for r in limited_again]
    assert ids_first_run == ids_second_run


def test_write_and_read_back(tmp_path):
    """Round‑trip test for CSV and log writers."""
    out_dir = tmp_path / "out"
    eligible_path = out_dir / "eligible.csv"
    excluded_path = out_dir / "excluded.log"

    rows = [
        {"participant_id": "sub-A"},
        {"participant_id": "sub-B"},
    ]
    excluded = [
        ({"participant_id": "sub-X"}, "missing MMSE"),
        ({"participant_id": "sub-Y"}, "missing MOCA"),
    ]

    write_eligible_csv(rows, eligible_path)
    write_excluded_log(excluded, excluded_path)

    # Verify CSV contents
    with open(eligible_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        read_rows = list(reader)
    assert [r["participant_id"] for r in read_rows] == ["sub-A", "sub-B"]

    # Verify log contents
    with open(excluded_path, encoding="utf-8") as f:
        lines = [l.strip().split("\\t") for l in f.readlines()]
    assert lines == [["sub-X", "missing MMSE"], ["sub-Y", "missing MOCA"]]