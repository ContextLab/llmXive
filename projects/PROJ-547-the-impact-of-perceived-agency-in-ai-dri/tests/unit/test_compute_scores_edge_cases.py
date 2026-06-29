"""Unit tests for edge‑case handling in ``compute_scores``."""

import csv
from pathlib import Path

import pytest

from agency_scoring.compute_scores import compute_agency_scores

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure used by the tests."""
    return tmp_path

def write_csv(path: Path, rows: list[dict[str, str]]):
    """Helper to write a simple CSV file."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["session_id", "utterances"])
        writer.writeheader()
        writer.writerows(rows)

def test_empty_utterances_assigns_zero_score(temp_dir):
    """An empty ``utterances`` field should produce a 0.0 score and log a warning."""
    transcripts = temp_dir / "transcripts.csv"
    write_csv(
        transcripts,
        [
            {"session_id": "s1", "utterances": ""},
            {"session_id": "s2", "utterances": "   "},
        ],
    )
    weights = temp_dir / "weights.yaml"
    weights.write_text("modal_verb: 1.0\nchoice_construction: 1.0\n")
    output = temp_dir / "scores.csv"

    compute_agency_scores(transcripts, weights, output)

    # Verify output CSV contains two rows with score 0.0
    with output.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    for row in rows:
        assert row["agency_score"] == "0.0"

def test_unreadable_file_results_in_empty_output_and_warning(temp_dir, caplog):
    """If the transcript file cannot be read, an empty output file should be produced."""
    transcripts = temp_dir / "missing.csv"  # file does not exist
    weights = temp_dir / "weights.yaml"
    weights.write_text("modal_verb: 1.0\n")
    output = temp_dir / "scores.csv"

    compute_agency_scores(transcripts, weights, output)

    # Output should contain only the header (no rows)
    with output.open() as f:
        lines = f.readlines()
    assert lines[0].strip() == "session_id,agency_score"
    assert len(lines) == 1

    # Verify a warning was logged
    warnings = [rec for rec in caplog.records if rec.levelname == "WARNING"]
    assert any("transcript_file_missing" in rec.getMessage() for rec in warnings) or any(
        "transcript_file_unreadable" in rec.getMessage() for rec in warnings
    )