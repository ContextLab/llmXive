"""
Unit test for the mock sweep runner.

The test verifies that the runner creates at least one CSV file in the
``data/raw`` directory and that the generated file contains the expected
columns.  It runs the runner in a temporary project directory so that the
real repository contents are untouched.
"""

import csv
from pathlib import Path

import pytest

# The sweep runner is a module; importing it executes no code.
from orchestrator.sweep_runner import run_sweep, _load_sweep_config

@pytest.fixture
def clean_raw_dir(tmp_path, monkeypatch):
    """
    Provide a temporary ``data/raw`` directory and point the toolkit's
    ``paths`` helper to it.
    """
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    # Monkey‑patch the ``paths`` helper used inside the runner.
    from llmxive_toolkit import paths as original_paths

    class DummyPaths:
        @staticmethod
        def data(*parts):
            return raw_dir.joinpath(*parts)

    monkeypatch.setattr("llmxive_toolkit.paths", DummyPaths, raising=False)
    return raw_dir

def test_sweep_generates_csv(clean_raw_dir, monkeypatch):
    """
    Run the sweep and assert that a ``run_000.csv`` file exists with the
    correct header and at least one data row.
    """
    # Ensure the runner sees the test configuration.
    cfg_path = Path("config") / "sweep_config.yaml"
    assert cfg_path.is_file(), "sweep_config.yaml must exist in the repository"

    # Execute the sweep (this will write into the temporary ``data/raw`` dir).
    run_sweep()

    # The first run should be ``run_000.csv``.
    csv_path = clean_raw_dir / "run_000.csv"
    assert csv_path.is_file(), f"Expected CSV file {csv_path} not found"

    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        # Verify the header contains all required columns.
        expected = [
            "run_id",
            "node_id",
            "ip_address",
            "granularity",
            "injected_latency_ms",
            "chunk_id",
            "wall_clock_time_sec",
            "ops_per_sec",
            "pi_estimate",
            "packet_count",
            "cpu_utilization_pct",
        ]
        for col in expected:
            assert col in header, f"Missing column {col} in CSV header"

        rows = list(reader)
        assert len(rows) > 0, "CSV file should contain at least one data row"

    # Verify that the runtime tracker was written.
    runtime_path = Path("data") / "runtime" / "pipeline_runtime.json"
    assert runtime_path.is_file(), "pipeline_runtime.json not created"

    # The test runner expects the script to exit with status 0; any exception
    # would cause pytest to fail, satisfying the quick‑start requirement.