"""
Unit tests for the PDF report layout design (Task T035a).
These tests verify that the design document (docs/report_layout.md) 
correctly specifies the data mapping and structure required for 
code/report.py implementation.
"""
import json
import os
import pytest
from pathlib import Path

# Path to the design document
DESIGN_DOC_PATH = Path("docs/report_layout.md")

@pytest.fixture
def design_doc_content():
    """Load the design document content."""
    if not DESIGN_DOC_PATH.exists():
        pytest.skip("Design document docs/report_layout.md not found.")
    with open(DESIGN_DOC_PATH, "r") as f:
        return f.read()

def test_design_document_exists(design_doc_content):
    """Verify the design document exists and is not empty."""
    assert len(design_doc_content) > 100, "Design document is too short or empty."

def test_design_specifies_library(design_doc_content):
    """Verify the design specifies reportlab as the PDF library."""
    assert "reportlab" in design_doc_content.lower(), "Design must specify 'reportlab'."

def test_design_specifies_page_structure(design_doc_content):
    """Verify the design defines page structure (Title, Methods, Motifs, etc.)."""
    required_sections = [
        "Title Page",
        "Methods Overview",
        "Quality Control",
        "Motif Analysis",
        "Summary Table"
    ]
    for section in required_sections:
        assert section in design_doc_content, f"Design must include section: {section}"

def test_design_maps_correlation_results(design_doc_content):
    """Verify the design maps correlation_results.json to PDF elements."""
    assert "correlation_results.json" in design_doc_content, "Design must map correlation_results.json."
    assert "r_value" in design_doc_content, "Design must map r_value."
    assert "p_value_corrected" in design_doc_content, "Design must map p_value_corrected."

def test_design_maps_permutation_results(design_doc_content):
    """Verify the design maps permutation_results.json to PDF elements."""
    assert "permutation_results.json" in design_doc_content, "Design must map permutation_results.json."
    assert "empirical_p_value" in design_doc_content, "Design must map empirical_p_value."

def test_design_maps_power_analysis(design_doc_content):
    """Verify the design maps power_analysis.json to PDF elements."""
    assert "power_analysis.json" in design_doc_content, "Design must map power_analysis.json."
    assert "min_detectable_r" in design_doc_content, "Design must map min_detectable_r."

def test_design_includes_mandatory_disclaimer(design_doc_content):
    """Verify the design includes the mandatory disclaimer string."""
    disclaimer = "These findings are associational only and do not imply causation."
    assert disclaimer in design_doc_content, "Design must include the mandatory disclaimer string."

def test_design_specifies_plot_type(design_doc_content):
    """Verify the design specifies scatter plots for motif analysis."""
    assert "scatter plot" in design_doc_content.lower(), "Design must specify scatter plots."
    assert "matplotlib" in design_doc_content.lower(), "Design must specify matplotlib for plots."

def test_design_specifies_page_size(design_doc_content):
    """Verify the design specifies A4 page size."""
    assert "A4" in design_doc_content, "Design must specify A4 page size."

def test_design_specifies_output_path(design_doc_content):
    """Verify the design specifies the output path for the PDF."""
    assert "results/report.pdf" in design_doc_content, "Design must specify results/report.pdf as output."