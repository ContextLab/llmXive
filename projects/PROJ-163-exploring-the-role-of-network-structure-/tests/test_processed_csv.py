"""
Unit tests for the performance‑metrics CSV generation script.
"""
import os
import csv
import math
from pathlib import Path

from code.generate_calibration_csv import generate_performance_csv

def test_performance_csv_created(tmp_path):
    """
    Verify that the CSV file is created and contains the expected header.
    """
    # Use a temporary raw directory with a minimal valid JSON snapshot.
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    # Minimal but realistic snapshot (only the fields needed for metrics)
    snapshot = {
        "backend_name": "ibmq_testdevice",
        "last_update_date": "2024-01-01T00:00:00Z",
        "qubits": [
            [{"name": "T1", "value": 100.0}, {"name": "T2", "value": 200.0}],
            [{"name": "T1", "value": 110.0}, {"name": "T2", "value": 210.0}]
        ],
        "gates": [
            {
                "gate": "cx",
                "parameters": [
                    {"name": "gate_error", "value": 0.01},
                    {"name": "readout_error", "value": 0.02}
                ]
            },
            {
                "gate": "cx",
                "parameters": [
                    {"name": "gate_error", "value": 0.015},
                    {"name": "readout_error", "value": 0.025}
                ]
            }
        ]
    }
    json_path = raw_dir / "snapshot.json"
    json_path.write_text(json.dumps(snapshot), encoding="utf-8")

    # Generate the CSV in a temporary processed directory
    output_path = tmp_path / "processed" / "performance_metrics.csv"
    generate_performance_csv(raw_dir=raw_dir, output_path=output_path)

    # Verify file exists
    assert output_path.is_file()

    # Verify header and at least one data row
    with output_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert reader.fieldnames == [
            "device_id",
            "timestamp",
            "t1_mean",
            "t2_mean",
            "cx_error_mean",
            "readout_error_mean",
            "chip_family",
        ]
        assert len(rows) == 1
        row = rows[0]
        # Basic numeric sanity checks – no NaN/Inf
        for col in ["t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean"]:
            val = float(row[col])
            assert not math.isnan(val)
            assert math.isfinite(val)
