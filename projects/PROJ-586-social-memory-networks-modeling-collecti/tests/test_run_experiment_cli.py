"""Tests for the ``run_experiment`` CLI.

These tests verify that the ``--agents`` argument correctly parses a
comma‑separated list and that the script creates the expected CSV output
files without raising exceptions.
"""

import csv
from pathlib import Path

from run_experiment import build_parser, main


def test_parse_int_list():
    parser = build_parser()
    args = parser.parse_args(
        ["--context", "full", "--agents", "3,5,7", "--games", "2"]
    )
    assert args.agents == [3, 5, 7]
    assert args.context == "full"
    assert args.games == 2


def test_run_experiment_writes_csv(tmp_path: Path):
    # Use a temporary directory for output to avoid polluting the repo.
    output_dir = tmp_path / "results"
    output_dir.mkdir()

    exit_code = main(
        [
            "--context",
            "full",
            "--agents",
            "3,5",
            "--games",
            "1",
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0

    expected_file = output_dir / "results_full.csv"
    assert expected_file.is_file()

    # Verify CSV header and at least one data row.
    with expected_file.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert reader.fieldnames == [
            "game_id",
            "specialization_index",
            "retrieval_efficiency",
            "context_condition",
            "agent_count",
        ]
        assert len(rows) == 2  # 2 agent counts × 1 game each