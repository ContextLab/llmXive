"""
Integration test for the full workflow – specifically the
variable‑fit verification step.

The test assumes that the pipeline has already produced the
``execution_runs.csv`` file (which is part of the repository) and
that ``analysis.aggregate.main()`` has been run, creating the
``validation_status.json`` file.  It then checks that the JSON
contains an entry for every run and that runs missing any required
variable are marked ``excluded``.
"""

import json

import pandas as pd

from llmxive_toolkit import paths
from analysis import aggregate

def test_validation_status_consistency(tmp_path, monkeypatch):
    """
    1. Run the aggregation (which also runs validation).
    2. Load ``execution_runs.csv`` and ``validation_status.json``.
    3. Verify that each run has a status entry.
    4. Ensure that runs missing any required column are marked
       ``excluded`` and runs with all required columns are marked
       ``included``.
    """
    # Run the aggregation – this also writes validation_status.json
    aggregate.main()

    csv_path = paths.processed("execution_runs.csv")
    json_path = paths.raw("validation_status.json")

    assert csv_path.exists(), "Aggregated execution runs CSV not found"
    assert json_path.exists(), "Validation status JSON not found"

    df = pd.read_csv(csv_path, dtype=str)
    with json_path.open() as f:
        status = json.load(f)

    # The number of entries should match the number of runs
    assert len(df) == len(status), "Mismatch between runs and validation entries"

    # Required logical columns (as defined in analysis.validation)
    required = {
        "cpu_variance",
        "dropout_rate",
        "node_count",
        "granularity_setting",
        "injected_latency",
        "total_throughput",
    }

    for _, row in df.iterrows():
        run_id = str(row["run_id"])
        entry = status.get(run_id)
        assert entry is not None, f"No validation entry for run {run_id}"

        # Determine which required logical columns are missing in the CSV
        missing = []
        # Mapping from logical name to actual CSV column name
        column_map = {
            "cpu_variance": "cpu_variance",
            "dropout_rate": "dropout_rate",
            "node_count": "node_count",
            "granularity_setting": "granularity_setting",
            "injected_latency": "injected_latency_ms",
            "total_throughput": "throughput_ops",
        }
        for logical, col in column_map.items():
            if col not in row or pd.isna(row[col]) or row[col] == "":
                missing.append(logical)

        if missing:
            assert entry["status"] == "excluded", (
                f"Run {run_id} missing {missing} but marked {entry['status']}"
            )
        else:
            assert entry["status"] == "included", (
                f"Run {run_id} has all required columns but marked {entry['status']}"
            )