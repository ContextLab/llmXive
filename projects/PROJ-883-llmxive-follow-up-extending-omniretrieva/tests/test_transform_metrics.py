"""Test the transform_metrics script.

The test creates a tiny synthetic CSV and ground‑truth latency CSV,
runs the transformation script via its ``main`` entry point and
checks that the resulting JSON‑Lines file exists and contains the
expected number of records with the required fields.
"""

import csv
import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the script's main function
from transform_metrics import main as transform_main


@pytest.fixture
def small_dataset(tmp_path: Path):
    """Create minimal CSV and ground‑truth latency files."""
    # execution_logs.csv
    csv_path = tmp_path / "execution_logs.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "source_type",
                "complexity_level",
                "latency_ms",
                "translation_error",
                "success_flag",
                "timeout_flag",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "query_id": "q_test_1",
                "source_type": "text",
                "complexity_level": "1",
                "latency_ms": "0.050",
                "translation_error": "False",
                "success_flag": "True",
                "timeout_flag": "False",
            }
        )
        writer.writerow(
            {
                "query_id": "q_test_2",
                "source_type": "graph",
                "complexity_level": "2",
                "latency_ms": "0.200",
                "translation_error": "True",
                "success_flag": "True",
                "timeout_flag": "False",
            }
        )

    # ground_truth_execution_logs.csv
    gt_path = tmp_path / "ground_truth_execution_logs.csv"
    with gt_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["query_id", "ground_truth_latency_ms"],
        )
        writer.writeheader()
        writer.writerow({"query_id": "q_test_1", "ground_truth_latency_ms": "0.040"})
        writer.writerow({"query_id": "q_test_2", "ground_truth_latency_ms": "0.150"})

    # generation_log.json (empty but required)
    genlog_path = tmp_path / "generation_log.json"
    genlog_path.write_text("[]", encoding="utf-8")

    return {
        "csv": csv_path,
        "gt": gt_path,
        "genlog": genlog_path,
        "output": tmp_path / "execution_metrics.jsonl",
    }


def test_transform_metrics_creates_output(small_dataset):
    """Run the transformation and verify output."""
    args = [
        "--input",
        str(small_dataset["csv"]),
        "--genlog",
        str(small_dataset["genlog"]),
        "--gtlatency",
        str(small_dataset["gt"]),
        "--output",
        str(small_dataset["output"]),
    ]
    # Simulate command‑line execution
    import sys

    sys.argv = ["transform_metrics.py"] + args
    transform_main()

    # Verify the JSON‑Lines file exists
    assert small_dataset["output"].is_file()

    # Load and inspect records
    with small_dataset["output"].open(encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 2
    # Check required keys are present
    required_keys = {
        "query_id",
        "latency_ms",
        "mismatch_flag",
        "delta_latency",
        "engine_version",
        "throttle_config",
    }
    for rec in lines:
        assert required_keys.issubset(rec.keys())

    # Spot‑check values
    rec1 = next(r for r in lines if r["query_id"] == "q_test_1")
    assert rec1["mismatch_flag"] is False
    assert rec1["delta_latency"] == pytest.approx(0.010)  # 0.050 - 0.040

    rec2 = next(r for r in lines if r["query_id"] == "q_test_2")
    assert rec2["mismatch_flag"] is True
    assert rec2["delta_latency"] == pytest.approx(0.050)  # 0.200 - 0.150