"""
Unit tests for the report generator (T025d).
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Mock the settings and logger if needed, or assume they work in test env
from code.analysis.report_generator import generate_report_summary, _generate_citations

def test_citations_content():
    """Test that the citation block contains required text."""
    citations = _generate_citations()
    assert "Constitution Principle VII" in citations
    assert "Spec FR-002" in citations
    assert "Repeated Measures ANOVA" in citations
    assert "N >= 30" in citations

def test_generate_report_summary_creates_file():
    """Test that the report generator creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create dummy input files
        metrics_csv = tmp_path / "metrics_summary.csv"
        pd.DataFrame({"Metric": ["Time"], "p_value": [0.01]}).to_csv(metrics_csv, index=False)
        
        power_md = tmp_path / "power_report.md"
        power_md.write_text("Power: 0.85")
        
        desc_csv = tmp_path / "desc_stats.csv"
        pd.DataFrame({"Metric": ["Engage"], "Mean": [10.5]}).to_csv(desc_csv, index=False)
        
        output_txt = tmp_path / "report_summary.txt"
        
        # Run generator
        generate_report_summary(metrics_csv, power_md, desc_csv, output_txt)
        
        # Verify output
        assert output_txt.exists()
        content = output_txt.read_text()
        assert "Constitution Principle VII" in content
        assert "Spec FR-002" in content
        assert "ANOVA" in content
        assert "Power: 0.85" in content

def test_generate_report_summary_missing_files():
    """Test behavior when input files are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        output_txt = tmp_path / "report_summary.txt"
        missing_metrics = tmp_path / "missing.csv"
        missing_power = tmp_path / "missing.md"
        missing_desc = tmp_path / "missing_desc.csv"
        
        # Should not crash, just log warnings
        generate_report_summary(missing_metrics, missing_power, missing_desc, output_txt)
        
        assert output_txt.exists()
        content = output_txt.read_text()
        assert "unavailable" in content.lower()
        assert "Constitution Principle VII" in content