"""
Tests for the CLI module (code/cli.py).
"""

import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from cli import (
    load_delta_grid,
    parse_args,
    run_workflow,
    log_metadata,
)
from config import ConfigError

# Test fixtures
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def delta_grid_csv(temp_dir):
    """Create a temporary delta_grid.csv file."""
    grid_path = temp_dir / "delta_grid.csv"
    with open(grid_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["delta"])
        writer.writeheader()
        writer.writerow({"delta": 0.1})
        writer.writerow({"delta": 0.2})
        writer.writerow({"delta": 0.3})
    return str(grid_path)

@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration to avoid actual TEBD runs."""
    # Mock ground state computation to return a simple state
    def mock_compute_ground_state(*args, **kwargs):
        return np.zeros(2**4), True  # Simple mock state

    # Mock entropy computation
    def mock_compute_entanglement_entropy_batch(*args, **kwargs):
        return np.array([1, 2, 3]), np.array([0.5, 1.0, 1.5])

    # Mock model selection
    def mock_select_model_aic(*args, **kwargs):
        from analysis import ModelSelectionResult
        return ModelSelectionResult(
            model_type="logarithmic",
            aic=10.0,
            r_squared=0.95,
            slope=0.33,
        )

    # Mock bootstrap
    def mock_bootstrap_resample(*args, **kwargs):
        return np.random.normal(0.33, 0.01, 100)

    def mock_compute_bootstrap_statistics(*args, **kwargs):
        return {
            "mean": 0.33,
            "std_error": 0.01,
            "ci_lower": 0.31,
            "ci_upper": 0.35,
            "p_value": 0.001,
        }

    def mock_compute_scaling_exponent(*args, **kwargs):
        return 0.33, {"r_squared": 0.95}

    def mock_generate_entropy_vs_l_plot(*args, **kwargs):
        pass  # Skip plot generation in tests

    monkeypatch.setattr(
        "cli.compute_ground_state", mock_compute_ground_state
    )
    monkeypatch.setattr(
        "cli.compute_entanglement_entropy_batch", mock_compute_entanglement_entropy_batch
    )
    monkeypatch.setattr("cli.select_model_aic", mock_select_model_aic)
    monkeypatch.setattr("cli.bootstrap_resample", mock_bootstrap_resample)
    monkeypatch.setattr(
        "cli.compute_bootstrap_statistics", mock_compute_bootstrap_statistics
    )
    monkeypatch.setattr(
        "cli.compute_scaling_exponent", mock_compute_scaling_exponent
    )
    monkeypatch.setattr(
        "cli.generate_entropy_vs_l_plot", mock_generate_entropy_vs_l_plot
    )

def test_parse_args_defaults():
    """Test that parse_args returns default values."""
    with patch("sys.argv", ["cli.py"]):
        args = parse_args()
        assert args.L == 30
        assert args.delta == 0.2
        assert args.N_real == 100
        assert args.seed == 42
        assert args.delta_grid is None
        assert args.output_dir is None
        assert args.timeout == 21600

def test_parse_args_custom():
    """Test that parse_args respects custom arguments."""
    with patch(
        "sys.argv",
        [
            "cli.py",
            "--L",
            "25",
            "--delta",
            "0.5",
            "--N_real",
            "50",
            "--seed",
            "123",
            "--delta_grid",
            "grid.csv",
            "--output_dir",
            "custom_output",
            "--timeout",
            "3600",
        ],
    ):
        args = parse_args()
        assert args.L == 25
        assert args.delta == 0.5
        assert args.N_real == 50
        assert args.seed == 123
        assert args.delta_grid == "grid.csv"
        assert args.output_dir == "custom_output"
        assert args.timeout == 3600

def test_load_delta_grid(delta_grid_csv):
    """Test loading delta values from CSV."""
    deltas = load_delta_grid(delta_grid_csv)
    assert deltas == [0.1, 0.2, 0.3]

def test_load_delta_grid_invalid(temp_dir):
    """Test loading invalid delta values from CSV."""
    grid_path = temp_dir / "invalid_grid.csv"
    with open(grid_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["delta"])
        writer.writeheader()
        writer.writerow({"delta": "invalid"})
        writer.writerow({"delta": 0.2})

    deltas = load_delta_grid(str(grid_path))
    assert deltas == [0.2]

def test_load_delta_grid_empty(temp_dir):
    """Test loading empty delta grid."""
    grid_path = temp_dir / "empty_grid.csv"
    with open(grid_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["delta"])
        writer.writeheader()

    with pytest.raises(ValueError, match="No valid delta values found"):
        load_delta_grid(str(grid_path))

def test_log_metadata(temp_dir):
    """Test logging metadata to JSON file."""
    metadata_file = temp_dir / "metadata.json"

    # First log
    metadata1 = {"param": "value1", "delta": 0.1}
    with patch("cli.METADATA_FILE", metadata_file):
        log_metadata(metadata1)

    assert metadata_file.exists()
    with open(metadata_file, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["param"] == "value1"

    # Second log
    metadata2 = {"param": "value2", "delta": 0.2}
    with patch("cli.METADATA_FILE", metadata_file):
        log_metadata(metadata2)

    with open(metadata_file, "r") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[1]["param"] == "value2"

def test_cli_run(mock_config, temp_dir):
    """Test full CLI workflow for a single parameter set."""
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Run workflow
    result = run_workflow(
        L=10,
        delta=0.2,
        N_real=5,
        seed=42,
        output_dir=output_dir,
        timeout=3600,
    )

    # Verify outputs
    assert "entropy_data" in result
    assert "model_result" in result
    assert "bootstrap_stats" in result
    assert "scaling_exponent" in result
    assert "metadata" in result

    # Verify files were created
    assert (output_dir / "entropy_data_delta_0.20.csv").exists()
    assert (output_dir / "scaling_fit_delta_0.20.txt").exists()
    assert (output_dir / "bootstrap_summary_delta_0.20.txt").exists()
    assert (output_dir / "entropy_vs_l_delta_0.20.png").exists()

    # Verify CSV content
    with open(output_dir / "entropy_data_delta_0.20.csv", "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0
        assert "l" in rows[0]
        assert "entropy" in rows[0]
        assert "unresolved" in rows[0]

    # Verify fit file content
    with open(output_dir / "scaling_fit_delta_0.20.txt", "r") as f:
        content = f.read()
        assert "delta" in content
        assert "Scaling exponent" in content
        assert "Bootstrap mean" in content
        assert "P-value" in content
        assert "Significance" in content

def test_cli_grid_run(mock_config, delta_grid_csv, temp_dir):
    """Test CLI workflow for a grid scan."""
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Simulate CLI arguments for grid scan
    deltas = load_delta_grid(delta_grid_csv)

    results = []
    for delta in deltas:
        result = run_workflow(
            L=10,
            delta=delta,
            N_real=5,
            seed=42,
            output_dir=output_dir,
            timeout=3600,
        )
        results.append(
            {
                "delta": delta,
                "alpha": result["scaling_exponent"],
                "ci_lower": result["bootstrap_stats"]["ci_lower"],
                "ci_upper": result["bootstrap_stats"]["ci_upper"],
                "ci_width": result["bootstrap_stats"]["ci_upper"]
                - result["bootstrap_stats"]["ci_lower"],
                "p_value": result["bootstrap_stats"]["p_value"],
            }
        )

    # Verify grid output file
    grid_output_path = output_dir / "delta_vs_exponent.csv"
    assert grid_output_path.exists()

    with open(grid_output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(deltas)
        for row in rows:
            assert "delta" in row
            assert "alpha" in row
            assert "ci_lower" in row
            assert "ci_upper" in row
            assert "ci_width" in row
            assert "p_value" in row

def test_timeout_handling(mock_config, temp_dir):
    """Test that workflow respects timeout."""
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Mock a slow workflow
    def slow_workflow(*args, **kwargs):
        import time
        time.sleep(10)  # Sleep longer than timeout
        return {}

    with patch("cli.run_workflow", slow_workflow):
        with pytest.raises(TimeoutError):
            run_workflow(
                L=10,
                delta=0.2,
                N_real=5,
                seed=42,
                output_dir=output_dir,
                timeout=1,  # 1 second timeout
            )