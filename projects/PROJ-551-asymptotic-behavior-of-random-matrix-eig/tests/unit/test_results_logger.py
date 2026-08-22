"""
Unit tests for the results logging functionality (T015).
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from utils.results_logger import record_simulation_result, append_to_aggregated_results


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_record_simulation_result_schema(temp_output_dir):
    """Test that record_simulation_result writes correct JSON schema."""
    output_path = temp_output_dir / "test_results.json"

    result = record_simulation_result(
        run_id="test_run_001",
        N=1000,
        theta=2.5,
        seed=42,
        eigenvalues=[2.51, 1.99, 1.98, 1.95, 1.92],
        outlier_flag=True,
        output_path=output_path
    )

    assert result == output_path
    assert result.exists()

    with open(result, 'r') as f:
        data = json.load(f)

    assert data["run_id"] == "test_run_001"
    assert data["N"] == 1000
    assert data["theta"] == 2.5
    assert data["seed"] == 42
    assert data["eigenvalues"] == [2.51, 1.99, 1.98, 1.95, 1.92]
    assert data["outlier_flag"] is True
    assert "timestamp" in data

    # Verify timestamp format (ISO 8601)
    timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
    assert timestamp.tzinfo is not None


def test_append_to_aggregated_results(temp_output_dir):
    """Test appending multiple results to an aggregated file."""
    output_path = temp_output_dir / "aggregated.json"

    results = [
        {
            "run_id": "run_1",
            "N": 500,
            "theta": 2.0,
            "seed": 1,
            "eigenvalues": [2.01, 1.99],
            "outlier_flag": False
        },
        {
            "run_id": "run_2",
            "N": 500,
            "theta": 2.5,
            "seed": 2,
            "eigenvalues": [2.52, 1.98],
            "outlier_flag": True
        }
    ]

    result = append_to_aggregated_results(results, output_path=output_path)

    assert result == output_path
    assert result.exists()

    with open(result, 'r') as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["run_id"] == "run_1"
    assert data[1]["run_id"] == "run_2"


def test_record_simulation_result_creates_directories(temp_output_dir):
    """Test that record_simulation_result creates parent directories if needed."""
    nested_path = temp_output_dir / "subdir" / "nested" / "results.json"

    result = record_simulation_result(
        run_id="nested_run",
        N=100,
        theta=1.0,
        seed=123,
        eigenvalues=[1.5],
        outlier_flag=False,
        output_path=nested_path
    )

    assert result.exists()
    assert result.parent == temp_output_dir / "subdir" / "nested"