"""
Tests for the reporting module (code/report.py).
"""
import json
import tempfile
from pathlib import Path

import pytest

from report import (
    generate_forest_plot,
    generate_report_text,
    write_pdf_report,
)


def test_forest_plot_generation():
    """Test that forest plot is generated without error."""
    # Mock analysis results
    results = {
        "iteration_count": {"coef": 0.5, "se": 0.1, "pval": 0.001, "ci": [0.3, 0.7]},
        "avg_comment_length": {"coef": -0.2, "se": 0.05, "pval": 0.01, "ci": [-0.3, -0.1]},
    }

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        plot_path = f.name

    try:
        generate_forest_plot(results, plot_path)
        assert Path(plot_path).exists()
        assert Path(plot_path).stat().st_size > 0
    finally:
        Path(plot_path).unlink(missing_ok=True)


def test_report_text_generation():
    """Test that report text includes required sections."""
    results = {"iteration_count": {"coef": 0.5, "pval": 0.001}}
    text = generate_report_text(results)

    # Check for required sections per spec (T005/FR-009)
    assert "Theoretical Grounding" in text
    assert "Data Gap" in text
    assert "NASA-TLX" in text
    assert "Note: This study uses proxy metrics" in text
    assert "associational" in text.lower()


def test_pdf_report_creation():
    """Test that PDF report is created."""
    results = {"test": {"coef": 1.0, "pval": 0.05}}

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name

    try:
        write_pdf_report(results, pdf_path)
        assert Path(pdf_path).exists()
        assert Path(pdf_path).stat().st_size > 0
    finally:
        Path(pdf_path).unlink(missing_ok=True)