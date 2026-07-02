import os
import csv
from pathlib import Path

from run_experiment import main

def test_limited_context_simulation(tmp_path, monkeypatch):
    """
    Verify that the limited‑context run creates the correct CSV file
    with the expected number of rows and columns.
    """
    # Prepare arguments: limited context, 5 agents, 10 games (small for test)
    args = [
        "--context",
        "limited",
        "--agents",
        "5",
        "--games",
        "10",
        "--output-dir",
        str(tmp_path),
    ]
    monkeypatch.setattr("sys.argv", ["run_experiment.py"] + args)

    # Run the experiment
    main()

    # Check that the CSV file exists and has the correct shape
    csv_path = Path(tmp_path) / "results_limited.csv"
    assert csv_path.is_file()

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Expect 10 rows (one per game)
    assert len(rows) == 10
    # Verify required columns are present
    expected_fields = {
        "game_id",
        "specialization_index",
        "retrieval_efficiency",
        "context_condition",
        "agent_count",
    }
    assert set(reader.fieldnames) == expected_fields
    # Spot‑check deterministic values
    first = rows[0]
    assert first["context_condition"] == "limited"
    assert int(first["agent_count"]) == 5
    # specialization_index should be log2(5) and retrieval_efficiency 1/5
    import math
    assert math.isclose(float(first["specialization_index"]), math.log2(5), rel_tol=1e-9)
    assert math.isclose(float(first["retrieval_efficiency"]), 1.0 / 5, rel_tol=1e-9)