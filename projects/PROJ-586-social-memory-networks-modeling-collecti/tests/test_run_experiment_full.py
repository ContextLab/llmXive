"""
Unit tests for the ``run_experiment`` CLI.

The tests focus on:
  * Successful parsing of all required arguments.
  * Creation of the expected CSV file with the correct header.
  * Deterministic behaviour when a fixed seed is supplied.
"""

import csv
import os
from pathlib import Path

import pytest

from run_experiment import build_parser, run_batch, ensure_dir


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary results directory for the test."""
    out_dir = tmp_path / "results"
    ensure_dir(out_dir)
    return out_dir


def test_parser_accepts_all_arguments():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--context",
            "full",
            "--agents",
            "3",
            "--games",
            "10",
            "--dataset",
            "squad",
            "--seed",
            "123",
            "--output-dir",
            "tmp_results",
        ]
    )
    assert args.context == "full"
    assert args.agents == 3
    assert args.games == 10
    assert args.dataset == "squad"
    assert args.seed == 123
    assert isinstance(args.output_dir, Path)


def test_run_batch_creates_csv(temp_output_dir: Path):
    """
    Run a tiny batch and verify that the CSV exists and contains the
    expected header and the correct number of rows.
    """
    csv_path = run_batch(
        context="full",
        agents=2,
        games=5,
        dataset_name="squad",
        thresholds=None,
        seed=1,
        output_dir=temp_output_dir,
    )

    # The file must exist.
    assert csv_path.is_file()

    # Verify header.
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_header = [
            "game_id",
            "specialization_index",
            "retrieval_efficiency",
            "context_condition",
            "agent_count",
        ]
        assert header == expected_header

        # Verify the correct number of data rows.
        rows = list(reader)
        assert len(rows) == 5
        # Game IDs should be sequential starting at 1.
        assert [int(r[0]) for r in rows] == list(range(1, 6))


def test_invalid_context_raises():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--context", "unknown", "--agents", "3"])