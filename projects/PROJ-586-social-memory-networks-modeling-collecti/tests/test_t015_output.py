"""Integration test that ensures the full results CSV is produced."""
import csv
from pathlib import Path

import pytest

from run_experiment import main as run_main


@pytest.fixture(scope="module")
def output_path(tmp_path_factory):
    # Use a temporary directory to avoid polluting the repository.
    return tmp_path_factory.mktemp("results") / "results_full.csv"


def test_results_csv_is_created(output_path: Path):
    # Run the experiment with a tiny configuration for speed.
    exit_code = run_main(
        [
            "--agents",
            "3",
            "--games",
            "5",
            "--context",
            "full",
            "--output",
            str(output_path),
        ]
    )
    assert exit_code == 0
    assert output_path.is_file()

    # Verify header and a few rows.
    with output_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 5
        for row in rows:
            assert set(row.keys()) == {
                "game_id",
                "specialization_index",
                "retrieval_efficiency",
                "context_condition",
                "agent_count",
            }
            # Basic sanity checks – values should be convertible to float/int.
            assert int(row["game_id"]) >= 1
            float(row["specialization_index"])
            float(row["retrieval_efficiency"])
            assert row["context_condition"] in {"full", "limited"}
            assert int(row["agent_count"]) == 3