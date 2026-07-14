"""Test that the T015 CSV generation script creates a valid file."""
import csv
from pathlib import Path

import pytest

# Import the function directly – this avoids spawning a subprocess and
# makes the test fast and deterministic.
from t015_generate_full_results import generate_full_results

@pytest.fixture
def tmp_results_path(tmp_path: Path) -> Path:
    """Provide a temporary path for the CSV output."""
    return tmp_path / "results_full.csv"

def test_generate_full_results_creates_file(tmp_results_path: Path) -> None:
    # Run the generation with a small, deterministic configuration.
    generate_full_results(num_games=3, num_agents=4, output_path=tmp_results_path)

    # The file must exist and be readable.
    assert tmp_results_path.is_file()

    # Verify header and a few rows.
    with tmp_results_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        assert header == [
            "game_id",
            "specialization_index",
            "retrieval_efficiency",
            "context_condition",
            "agent_count",
        ]

        rows = list(reader)
        # Exactly three rows because we asked for three games.
        assert len(rows) == 3
        for i, row in enumerate(rows, start=1):
            assert int(row["game_id"]) == i
            # All metrics should be zero (the deterministic minimal simulation).
            assert float(row["specialization_index"]) == pytest.approx(0.0)
            assert float(row["retrieval_efficiency"]) == pytest.approx(0.0)
            assert row["context_condition"] == "full"
            assert int(row["agent_count"]) == 4