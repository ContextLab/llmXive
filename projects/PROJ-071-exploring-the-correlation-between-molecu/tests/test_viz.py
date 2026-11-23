"""Tests for visualization module."""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import the module under test
from viz import (
    get_data_path,
    check_gate_status,
    check_statistical_gate,
    load_analysis_results,
    generate_correlation_scatter_plots,
    generate_placeholder_plot,
    generate_residual_diagnostic_plots
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    outputs_dir = data_dir / "outputs"
    processed_dir.mkdir(parents=True)
    outputs_dir.mkdir(parents=True)
    return data_dir


def test_get_data_path():
    """Test that get_data_path returns a Path object."""
    path = get_data_path()
    assert isinstance(path, Path)


def test_check_gate_status_missing_file(tmp_path, monkeypatch):
    """Test gate status check when file is missing."""
    # Monkeypatch the get_data_path to return our temp dir
    def mock_get_data_path():
        return tmp_path / "nonexistent"
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    is_pass, reason, n_count = check_gate_status()
    assert is_pass is False
    assert "not found" in reason.lower()
    assert n_count == 0


def test_check_gate_status_fail(tmp_path, monkeypatch):
    """Test gate status check when gate is failed."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    gate_file = data_dir / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "FAIL", "reason": "N < 30", "N": 10}))

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    is_pass, reason, n_count = check_gate_status()
    assert is_pass is False
    assert n_count == 10


def test_check_gate_status_pass(tmp_path, monkeypatch):
    """Test gate status check when gate is passed."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    gate_file = data_dir / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "PASS", "reason": "Sufficient data", "N": 100}))

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    is_pass, reason, n_count = check_gate_status()
    assert is_pass is True
    assert n_count == 100


def test_load_analysis_results_missing(tmp_path, monkeypatch):
    """Test loading analysis results when file is missing."""
    def mock_get_data_path():
        return tmp_path / "nonexistent"
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    results = load_analysis_results()
    assert results is None


def test_load_analysis_results_pass(tmp_path, monkeypatch):
    """Test loading analysis results when file exists."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir()
    results_file = processed_dir / "analysis_results.json"
    results_file.write_text(json.dumps({"status": "PASS", "R2": 0.85, "N": 100}))

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    results = load_analysis_results()
    assert results is not None
    assert results["status"] == "PASS"
    assert results["R2"] == 0.85


def test_generate_placeholder_plot(tmp_path, monkeypatch):
    """Test generating a placeholder plot."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    outputs_dir = data_dir / "outputs"
    outputs_dir.mkdir()

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    filename = "test_placeholder.png"
    generate_placeholder_plot(filename, "Test Message")

    output_file = outputs_dir / filename
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_generate_correlation_scatter_plots_gate_fail(tmp_path, monkeypatch):
    """Test correlation plots generation when gate fails."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    gate_file = data_dir / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "FAIL", "reason": "N < 30", "N": 10}))
    outputs_dir = data_dir / "outputs"
    outputs_dir.mkdir()

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    generate_correlation_scatter_plots()

    plot_file = outputs_dir / "scatter_tpsa_vs_half_life.png"
    assert plot_file.exists()
    assert plot_file.stat().st_size > 0


def test_generate_correlation_scatter_plots_gate_pass(tmp_path, monkeypatch):
    """Test correlation plots generation when gate passes and data exists."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir()
    outputs_dir = data_dir / "outputs"
    outputs_dir.mkdir()

    # Create gate status
    gate_file = data_dir / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "PASS", "N": 100}))

    # Create merged data
    merged_file = processed_dir / "merged_drugs.csv"
    n = 50
    data = {
        'TPSA': np.random.uniform(0, 200, n),
        'half_life': np.random.uniform(0, 50, n)
    }
    pd.DataFrame(data).to_csv(merged_file, index=False)

    # Create analysis results
    results_file = processed_dir / "analysis_results.json"
    results_file.write_text(json.dumps({"status": "PASS", "R2": 0.5, "N": 50}))

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    generate_correlation_scatter_plots()

    plot_file = outputs_dir / "scatter_tpsa_vs_half_life.png"
    assert plot_file.exists()
    assert plot_file.stat().st_size > 0


def test_generate_residual_diagnostic_plots_gate_fail(tmp_path, monkeypatch):
    """Test residual plots generation when gate fails."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    gate_file = data_dir / "gate_status.json"
    gate_file.write_text(json.dumps({"status": "FAIL", "N": 10}))
    outputs_dir = data_dir / "outputs"
    outputs_dir.mkdir()

    def mock_get_data_path():
        return data_dir
    monkeypatch.setattr("viz.get_data_path", mock_get_data_path)

    generate_residual_diagnostic_plots()

    assert (outputs_dir / "residuals.png").exists()
    assert (outputs_dir / "qq_plot.png").exists()
    assert (outputs_dir / "residuals_vs_fitted.png").exists()