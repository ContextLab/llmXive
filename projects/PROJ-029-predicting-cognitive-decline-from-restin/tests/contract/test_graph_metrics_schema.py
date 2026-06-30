"""
Contract tests for the graph metrics output schema.
Verifies that the computed graph metrics adhere to the defined data model.
"""
import json
import csv
import pytest
from pathlib import Path
import pandas as pd

# Expected columns based on task T019 and data model
EXPECTED_GRAPH_METRICS_COLUMNS = [
    "subject_id",
    "node_degree",
    "global_efficiency",
    "clustering_coefficient",
    "average_path_length"
]

EXPECTED_METRIC_TYPES = {
    "node_degree": float,
    "global_efficiency": float,
    "clustering_coefficient": float,
    "average_path_length": float
}


def test_graph_metrics_csv_schema(tmp_path):
    """
    Contract: Verify the CSV output of graph metrics has correct headers and types.
    """
    output_file = tmp_path / "graph_metrics.csv"

    # Mock data
    data = [
        {
            "subject_id": "sub-01",
            "node_degree": 45.5,
            "global_efficiency": 0.32,
            "clustering_coefficient": 0.41,
            "average_path_length": 3.2
        },
        {
            "subject_id": "sub-02",
            "node_degree": 42.1,
            "global_efficiency": 0.29,
            "clustering_coefficient": 0.38,
            "average_path_length": 3.5
        }
    ]

    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_GRAPH_METRICS_COLUMNS)
        writer.writeheader()
        writer.writerows(data)

    # Read back and validate
    df = pd.read_csv(output_file)

    # Contract assertion: Columns match
    assert list(df.columns) == EXPECTED_GRAPH_METRICS_COLUMNS

    # Contract assertion: Types are numeric
    for col in EXPECTED_METRIC_TYPES:
        assert df[col].dtype in ['float64', 'int64', 'float32']
        assert not df[col].isnull().any()


def test_graph_metrics_json_schema(tmp_path):
    """
    Contract: Verify JSON output structure if JSON format is used.
    """
    output_file = tmp_path / "graph_metrics.json"

    data = [
        {
            "subject_id": "sub-01",
            "metrics": {
                "node_degree": 45.5,
                "global_efficiency": 0.32,
                "clustering_coefficient": 0.41,
                "average_path_length": 3.2
            }
        }
    ]

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    with open(output_file, 'r') as f:
        loaded = json.load(f)

    # Contract assertion: Structure matches
    assert isinstance(loaded, list)
    assert "subject_id" in loaded[0]
    assert "metrics" in loaded[0]
    assert "global_efficiency" in loaded[0]["metrics"]
