import json
import tempfile
from pathlib import Path
import pytest

from src.analysis.report_generator import (
    generate_final_report,
    generate_stats_report,
    generate_model_report,
    ASSOCIATIVE_DISCLAIMER
)

def test_disclaimer_constant_exists():
    """Verify FR-007 disclaimer constant is defined and non-empty."""
    assert isinstance(ASSOCIATIVE_DISCLAIMER, str)
    assert len(ASSOCIATIVE_DISCLAIMER) > 50
    assert "associative, not causal" in ASSOCIATIVE_DISCLAIMER.lower()
    assert "causal" in ASSOCIATIVE_DISCLAIMER.lower()

def test_final_report_includes_disclaimer():
    """Test that the final report includes the FR-007 disclaimer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stats_data = {"t_test_p_value": 0.01}
        model_data = {"auc_mean": 0.85}

        report_path = generate_final_report(
            results_path=tmpdir,
            stats_results=stats_data,
            model_results=model_data
        )

        assert report_path.exists()

        with open(report_path, "r") as f:
            data = json.load(f)

        assert "compliance" in data
        assert "fr_007_associative_disclaimer" in data["compliance"]
        assert data["compliance"]["fr_007_associative_disclaimer"] == ASSOCIATIVE_DISCLAIMER

def test_final_report_without_disclaimer():
    """Test that the disclaimer can be excluded if requested."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stats_data = {"t_test_p_value": 0.01}
        model_data = {"auc_mean": 0.85}

        report_path = generate_final_report(
            results_path=tmpdir,
            stats_results=stats_data,
            model_results=model_data,
            include_disclaimer=False
        )

        assert report_path.exists()

        with open(report_path, "r") as f:
            data = json.load(f)

        assert "compliance" not in data or "fr_007_associative_disclaimer" not in data.get("compliance", {})

def test_stats_report_includes_disclaimer():
    """Test that the stats report includes the FR-007 disclaimer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stats_data = {"t_test_p_value": 0.01, "cohen_d": 0.5}

        report_path = generate_stats_report(
            stats_results=stats_data,
            output_path=tmpdir
        )

        assert report_path.exists()

        with open(report_path, "r") as f:
            data = json.load(f)

        assert "disclaimer" in data
        assert data["disclaimer"] == ASSOCIATIVE_DISCLAIMER

def test_model_report_includes_disclaimer():
    """Test that the model report includes the FR-007 disclaimer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_data = {"auc_mean": 0.85, "tss_mean": 0.60}

        report_path = generate_model_report(
            model_results=model_data,
            output_path=tmpdir
        )

        assert report_path.exists()

        with open(report_path, "r") as f:
            data = json.load(f)

        assert "disclaimer" in data
        assert data["disclaimer"] == ASSOCIATIVE_DISCLAIMER
