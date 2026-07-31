"""
Integration test for the report generator (T041).

The test runs the ``code/models/report_generator.py`` script and checks that:
  * ``output/report.md`` is created,
  * the mandatory disclaimer string is present,
  * if a data limitation warning is indicated in ``output/data_status.json``,
    the report contains the corresponding section.
"""

import json
import os
from pathlib import Path

import pytest

# Import the module under test
from models.report_generator import main as generate_report, generate_report_content

@pytest.fixture(scope="module")
def output_path():
    """Path to the generated report."""
    return Path("output/report.md")

def test_report_is_generated(output_path):
    # Ensure any previous report is removed
    if output_path.is_file():
        output_path.unlink()
    # Run the generator
    generate_report()
    # Verify the file now exists
    assert output_path.is_file(), "Report file was not created"

def test_report_contains_disclaimer(output_path):
    # Load the report content
    content = output_path.read_text(encoding="utf-8")
    # The mandatory disclaimer string defined in utils.report_utils
    disclaimer = "Associational analysis only; no causal inference"
    assert disclaimer in content, "Mandatory disclaimer missing from report"

def test_conditional_data_warning(output_path):
    """
    If ``output/data_status.json`` indicates ``count_warning`` is true,
    the report must contain the warning section. Otherwise, the section
    should not be present.
    """
    data_status_path = Path("output/data_status.json")
    if not data_status_path.is_file():
        pytest.skip("data_status.json not available – cannot test conditional warning")
    data_status = json.loads(data_status_path.read_text(encoding="utf-8"))
    content = output_path.read_text(encoding="utf-8")
    warning_section_header = "## Data Limitation Warning"
    if data_status.get("count_warning"):
        assert warning_section_header in content, (
            "Data limitation warning expected but not found in report"
        )
    else:
        assert warning_section_header not in content, (
            "Data limitation warning found in report despite count_warning=False"
        )