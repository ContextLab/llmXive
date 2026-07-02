"""
Integration test for the ``generate_full_results`` script.

The test runs the script with a very small ``--games`` value (10) to keep the
CI fast, then checks that the output CSV exists, contains a header row and
exactly the expected number of data rows.
"""

import csv
from pathlib import Path

import pytest

from generate_full_results import main as run_experiment


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "results"


def test_results_full_csv_is_created_and_has_correct_shape(temp_output_dir: Path):
    # Run the experiment with a tiny configuration.
    args = [
        "--agents",
        "5",
        "--games",
        "10",
        "--output-dir",
        str(temp_output_dir),
        "--seed",
        "123",
    ]
    run_experiment(args)

    csv_path = temp_output_dir / "results_full.csv"
    assert csv_path.is_file(), "CSV output file was not created"

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Header validation – ensure all required columns are present.
    expected_fields = {
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    }
    assert set(reader.fieldnames or []) == expected_fields

    # Exactly 10 data rows should be present (games=10).
    assert len(rows) == 10
