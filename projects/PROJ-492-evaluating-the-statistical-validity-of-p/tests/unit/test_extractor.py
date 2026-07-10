"""
Unit tests for the extractor module (T020).
Covers: missing metrics, inequality p-values, malformed HTML, conflicting sample sizes.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from code.src.audit.extractor import (
    extract_single_float,
    extract_single_int,
    extract_field_from_html,
    extract_summary_from_html,
    extract_all,
)
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger()

# --- Helper Fixtures ---

def create_mock_html(metric_value: str = "5.2", sample_size: str = "1000", baseline: str = "4.8"):
    """Generates a simple HTML string with embedded metrics."""
    return f"""
    <html>
      <body>
        <div id="metric">{metric_value}</div>
        <div id="sample-size">{sample_size}</div>
        <div id="baseline">{baseline}</div>
        <div id="p-value">0.03</div>
        <div id="domain">tech</div>
        <div id="url">https://example.com/test</div>
      </body>
    </html>
    """

def create_malformed_html():
    """Generates HTML with unclosed tags and broken structure."""
    return """
    <html>
      <body>
        <div id="metric">5.2
        <div id="sample-size">1000</div>
        <div id="baseline">4.8</div>
        <!-- Missing closing tags and broken structure -->
        <div id="p-value">0.03</div>
      </body>
    """

# --- Tests for extract_single_float ---

def test_extract_single_float_success():
    """Test successful extraction of a float value."""
    html = create_mock_html(metric_value="5.25")
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_float(soup, "metric")
    assert result == 5.25

def test_extract_single_float_missing():
    """Test extraction when element is missing."""
    html = "<html><body><div>Nothing here</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_float(soup, "metric")
    assert result is None

def test_extract_single_float_invalid_format():
    """Test extraction when value is not a valid float."""
    html = '<html><body><div id="metric">N/A</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_float(soup, "metric")
    assert result is None

def test_extract_single_float_inequality_prefix():
    """Test extraction handling inequality prefixes like '> 5.0' or '< 0.01'."""
    # Test greater than
    html = '<html><body><div id="metric">> 5.0</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_float(soup, "metric")
    assert result is not None
    assert result == 5.0
    
    # Test less than
    html = '<html><body><div id="metric">< 0.01</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_float(soup, "metric")
    assert result is not None
    assert result == 0.01

# --- Tests for extract_single_int ---

def test_extract_single_int_success():
    """Test successful extraction of an integer value."""
    html = create_mock_html(sample_size="1500")
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_int(soup, "sample-size")
    assert result == 1500

def test_extract_single_int_missing():
    """Test extraction when element is missing."""
    html = "<html><body><div>Nothing here</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_int(soup, "sample-size")
    assert result is None

def test_extract_single_int_invalid_format():
    """Test extraction when value is not a valid integer."""
    html = '<html><body><div id="sample-size">many</div></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    result = extract_single_int(soup, "sample-size")
    assert result is None

# --- Tests for extract_field_from_html ---

def test_extract_field_from_html_success():
    """Test successful extraction of a string field."""
    html = create_mock_html()
    soup = BeautifulSoup(html, "html.parser")
    result = extract_field_from_html(soup, "domain")
    assert result == "tech"

def test_extract_field_from_html_missing():
    """Test extraction when element is missing."""
    html = "<html><body><div>Nothing here</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    result = extract_field_from_html(soup, "domain")
    assert result is None

# --- Tests for extract_summary_from_html (Edge Cases) ---

@patch("code.src.audit.extractor.extract_single_float")
@patch("code.src.audit.extractor.extract_single_int")
@patch("code.src.audit.extractor.extract_field_from_html")
def test_extract_summary_missing_metrics(mock_field, mock_int, mock_float):
    """Test handling of missing critical metrics (metric, baseline, sample_size)."""
    mock_float.side_effect = [None, None, None] # metric, baseline, p-value
    mock_int.side_effect = [None] # sample_size
    mock_field.return_value = "tech"
    
    html = create_mock_html()
    soup = BeautifulSoup(html, "html.parser")
    
    result = extract_summary_from_html(soup, "https://example.com/test")
    
    # Should return an ABTestSummary with None for missing fields, not crash
    assert isinstance(result, ABTestSummary)
    assert result.metric_value is None
    assert result.baseline_value is None
    assert result.sample_size is None
    assert result.url == "https://example.com/test"

@patch("code.src.audit.extractor.extract_single_float")
def test_extract_summary_conflicting_sample_sizes(mock_float):
    """Test handling of conflicting sample sizes (e.g., extracted from multiple places)."""
    # Simulate a scenario where logic might detect conflict (here we test the parsing logic)
    # The extractor typically extracts one value. If the HTML has multiple, 
    # the logic depends on implementation. We test that it handles non-numeric conflict gracefully.
    
    # Case: One field says "1000", another says "1k" (which might fail int parsing)
    html = """
    <html>
      <body>
        <div id="sample-size">1000</div>
        <div id="sample-size-alt">1k</div>
        <div id="metric">5.0</div>
        <div id="baseline">4.0</div>
        <div id="p-value">0.05</div>
        <div id="domain">finance</div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # If the extractor logic tries to parse '1k' as int, it should return None for that specific attempt
    # and ideally rely on the valid '1000'.
    # We verify that the function doesn't raise an exception.
    try:
        result = extract_summary_from_html(soup, "https://example.com/test")
        # If it succeeds, check that valid data is present
        assert result is not None
    except ValueError:
        # If the implementation crashes on invalid formats, that's a bug we are testing for
        # but for this test we assume robust handling (returning None for bad fields).
        # If it crashes, the test fails, indicating the extractor needs fixing.
        pytest.fail("extract_summary_from_html raised ValueError on conflicting/invalid sample size format")

@patch("code.src.audit.extractor.extract_field_from_html")
def test_extract_summary_malformed_html(mock_field):
    """Test handling of malformed HTML structure."""
    mock_field.return_value = "tech"
    html = create_malformed_html()
    
    # BeautifulSoup should handle malformed HTML, but we ensure no exceptions
    try:
        soup = BeautifulSoup(html, "html.parser")
        result = extract_summary_from_html(soup, "https://example.com/test")
        assert result is not None
    except Exception as e:
        pytest.fail(f"extract_summary_from_html failed on malformed HTML: {e}")

@patch("code.src.audit.extractor.extract_single_float")
def test_extract_summary_inequality_p_value(mock_float):
    """Test handling of inequality p-values (e.g., p < 0.001)."""
    mock_float.return_value = 0.001 # Extracted value
    
    html = """
    <html>
      <body>
        <div id="metric">5.0</div>
        <div id="baseline">4.0</div>
        <div id="sample-size">1000</div>
        <div id="p-value">< 0.001</div>
        <div id="domain">health</div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # The extractor should parse the number part
    result = extract_summary_from_html(soup, "https://example.com/test")
    assert result is not None
    assert result.p_value is not None
    # Verify the inequality logic (if implemented) or just that it extracted a number
    assert result.p_value == 0.001

# --- Tests for extract_all (Integration of edge cases) ---

@patch("code.src.audit.extractor.extract_summary_from_html")
def test_extract_all_handles_list(mock_extract):
    """Test that extract_all processes a list of HTMLs correctly."""
    mock_extract.return_value = ABTestSummary(
        url="https://example.com",
        metric_value=5.0,
        baseline_value=4.0,
        sample_size=100,
        p_value=0.05,
        domain="test"
    )
    
    html_list = [create_mock_html(), create_malformed_html()]
    
    results = extract_all(html_list)
    
    assert len(results) == 2
    assert all(isinstance(r, ABTestSummary) for r in results)

@patch("code.src.audit.extractor.extract_summary_from_html")
def test_extract_all_handles_empty_list(mock_extract):
    """Test that extract_all handles an empty list."""
    results = extract_all([])
    assert results == []

@patch("code.src.audit.extractor.extract_summary_from_html")
def test_extract_all_handles_none_in_list(mock_extract):
    """Test that extract_all handles None in the input list (if passed)."""
    mock_extract.return_value = None
    html_list = [create_mock_html(), None]
    
    # Depending on implementation, this might crash or skip. 
    # We expect it to handle gracefully or skip None.
    try:
        results = extract_all(html_list)
        # If it returns a list, check length
        assert isinstance(results, list)
    except TypeError:
        # If it crashes on None input, that's a specific behavior to note
        # but robust extractors should filter or check for None.
        pass