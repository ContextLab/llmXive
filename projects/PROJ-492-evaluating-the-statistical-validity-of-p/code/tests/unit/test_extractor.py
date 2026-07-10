"""
Unit tests for the extractor module.
Tests missing metric handling, malformed HTML, conflicting sample sizes,
and error code logging.
"""
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from bs4 import BeautifulSoup

from code.src.audit.extractor import (
    extract_single_float,
    extract_single_int,
    extract_field_from_html,
    extract_summary_from_html,
    extract_all,
    write_summaries_to_json,
    ERROR_CODES
)
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_error_message


class TestExtractSingleFloat:
    def test_extract_valid_float(self):
        """Test extraction of valid float values."""
        assert extract_single_float("0.05", "ERR-XXX") == 0.05
        assert extract_single_float("5%", "ERR-XXX") == 5.0
        assert extract_single_float("0.05%", "ERR-XXX") == 0.05
        assert extract_single_float("  0.05  ", "ERR-XXX") == 0.05

    def test_extract_invalid_float(self):
        """Test extraction returns None for invalid values."""
        assert extract_single_float("invalid", "ERR-XXX") is None
        assert extract_single_float("", "ERR-XXX") is None
        assert extract_single_float(None, "ERR-XXX") is None

    def test_log_error_on_missing(self, caplog):
        """Test that error is logged when value is missing."""
        with caplog.at_level(logging.WARNING):
            result = extract_single_float("", "ERR-001")
            assert result is None
            assert "ERR-001" in caplog.text


class TestExtractSingleInt:
    def test_extract_valid_int(self):
        """Test extraction of valid int values."""
        assert extract_single_int("100", "ERR-XXX") == 100
        assert extract_single_int("1,000", "ERR-XXX") == 1000
        assert extract_single_int("100.0", "ERR-XXX") == 100

    def test_extract_invalid_int(self):
        """Test extraction returns None for invalid values."""
        assert extract_single_int("invalid", "ERR-XXX") is None
        assert extract_single_int("", "ERR-XXX") is None
        assert extract_single_int(None, "ERR-XXX") is None

    def test_log_error_on_missing(self, caplog):
        """Test that error is logged when value is missing."""
        with caplog.at_level(logging.WARNING):
            result = extract_single_int("", "ERR-003")
            assert result is None
            assert "ERR-003" in caplog.text


class TestExtractFieldFromHtml:
    def test_extract_with_selector(self):
        """Test extraction using CSS selector."""
        html = "<div class='title'>Test Title</div>"
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.title'], "ERR-001")
        assert result == "Test Title"

    def test_extract_with_multiple_selectors(self):
        """Test extraction with multiple fallback selectors."""
        html = "<h1>Primary Title</h1>"
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.title', 'h1'], "ERR-001")
        assert result == "Primary Title"

    def test_extract_not_found(self, caplog):
        """Test extraction returns None when not found."""
        html = "<div>No title here</div>"
        soup = BeautifulSoup(html, 'html.parser')
        with caplog.at_level(logging.WARNING):
            result = extract_field_from_html(soup, ['.title'], "ERR-002")
            assert result is None
            assert "ERR-002" in caplog.text


class TestExtractSummaryFromHtml:
    def test_extract_complete_summary(self):
        """Test extraction of a complete summary with all fields."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test A/B Test">
            <meta property="og:site_name" content="Example.com">
            <meta name="sample-size-control" content="1000">
            <meta name="sample-size-treatment" content="1000">
            <meta name="conversion-control" content="0.10">
            <meta name="conversion-treatment" content="0.12">
            <meta name="p-value" content="0.03">
            <meta name="effect-size" content="0.02">
            <meta name="test-type" content="z-test">
            <meta name="publication-year" content="2023">
            <meta name="outcome-type" content="binary">
        </head>
        <body>
            <h1>Test A/B Test</h1>
        </body>
        </html>
        """
        metadata = {
            'fetch_timestamp': '2023-01-01T00:00:00',
            'repository_id': 'test_repo'
        }
        summary = extract_summary_from_html(html, 'https://example.com/test', metadata)

        assert summary is not None
        assert summary.source_url == 'https://example.com/test'
        assert summary.domain == 'Example.com'
        assert summary.title == 'Test A/B Test'
        assert summary.sample_size_control == 1000
        assert summary.sample_size_treatment == 1000
        assert summary.conversion_rate_control == 0.10
        assert summary.conversion_rate_treatment == 0.12
        assert summary.p_value == 0.03
        assert summary.effect_size == 0.02
        assert summary.test_type == 'z-test'
        assert summary.publication_year == 2023
        assert summary.outcome_type == 'binary'

    def test_extract_missing_fields(self, caplog):
        """Test extraction with missing fields logs appropriate errors."""
        html = """
        <html>
        <body>
            <h1>Incomplete Test</h1>
        </body>
        </html>
        """
        metadata = {'fetch_timestamp': '2023-01-01', 'repository_id': 'test'}

        with caplog.at_level(logging.WARNING):
            summary = extract_summary_from_html(html, 'https://example.com/test', metadata)
            assert summary is not None
            # Should log errors for missing required fields
            assert "ERR-003" in caplog.text  # Missing sample_size_control
            assert "ERR-005" in caplog.text  # Missing conversion_rate_control

    def test_extract_malformed_html(self, caplog):
        """Test extraction handles malformed HTML gracefully."""
        html = "<html><body><div><p>Unclosed tags"
        metadata = {'fetch_timestamp': '2023-01-01', 'repository_id': 'test'}

        with caplog.at_level(logging.ERROR):
            summary = extract_summary_from_html(html, 'https://example.com/test', metadata)
            # Should still return a summary object even with malformed HTML
            assert summary is not None

    def test_extract_conflicting_sample_sizes(self, caplog):
        """Test extraction logs error when sample sizes differ."""
        html = """
        <html>
        <body>
            <p>Control: n=1000</p>
            <p>Treatment: n=1200</p>
        </body>
        </html>
        """
        metadata = {'fetch_timestamp': '2023-01-01', 'repository_id': 'test'}

        with caplog.at_level(logging.WARNING):
            summary = extract_summary_from_html(html, 'https://example.com/test', metadata)
            assert summary is not None
            # Should log error for mismatched sample sizes
            assert "ERR-016" in caplog.text

    def test_extract_invalid_p_value_range(self, caplog):
        """Test extraction logs error for out-of-range p-value."""
        html = """
        <html>
        <body>
            <p>p-value: 1.5</p>
        </body>
        </html>
        """
        metadata = {'fetch_timestamp': '2023-01-01', 'repository_id': 'test'}

        with caplog.at_level(logging.WARNING):
            summary = extract_summary_from_html(html, 'https://example.com/test', metadata)
            assert summary is not None
            assert "ERR-018" in caplog.text

    def test_extract_invalid_conversion_rate(self, caplog):
        """Test extraction logs error for out-of-range conversion rate."""
        html = """
        <html>
        <body>
            <p>Control rate: 150%</p>
        </body>
        </html>
        """
        metadata = {'fetch_timestamp': '2023-01-01', 'repository_id': 'test'}

        with caplog.at_level(logging.WARNING):
            summary = extract_summary_from_html(html, 'https://example.com/test', metadata)
            assert summary is not None
            assert "ERR-017" in caplog.text


class TestExtractAll:
    def test_extract_multiple_files(self):
        """Test extraction from multiple HTML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test HTML files
            html1 = """
            <html><head><meta property="og:title" content="Test 1"></head>
            <body><p>n=1000</p><p>rate=0.10</p><p>p=0.05</p><p>es=0.01</p><p>z-test</p><p>2023</p><p>binary</p></body></html>
            """
            html2 = """
            <html><head><meta property="og:title" content="Test 2"></head>
            <body><p>n=1000</p><p>rate=0.12</p><p>p=0.03</p><p>es=0.02</p><p>z-test</p><p>2023</p><p>binary</p></body></html>
            """

            file1 = tmpdir_path / 'test1.html'
            file2 = tmpdir_path / 'test2.html'
            file1.write_text(html1)
            file2.write_text(html2)

            urls = ['https://example.com/1', 'https://example.com/2']
            metadata_list = [
                {'fetch_timestamp': '2023-01-01', 'repository_id': 'repo1'},
                {'fetch_timestamp': '2023-01-02', 'repository_id': 'repo2'}
            ]

            summaries = extract_all([file1, file2], urls, metadata_list)

            assert len(summaries) == 2
            assert summaries[0].source_url == 'https://example.com/1'
            assert summaries[1].source_url == 'https://example.com/2'


class TestWriteSummariesToJson:
    def test_write_summaries(self):
        """Test writing summaries to JSON file."""
        summaries = [
            ABTestSummary(
                source_url='https://example.com/1',
                domain='example.com',
                title='Test 1',
                sample_size_control=1000,
                sample_size_treatment=1000,
                conversion_rate_control=0.10,
                conversion_rate_treatment=0.12,
                p_value=0.03,
                effect_size=0.02,
                test_type='z-test',
                publication_year=2023,
                confidence_interval=None,
                outcome_type='binary',
                fetch_timestamp='2023-01-01',
                repository_id='repo1'
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'output.json'
            write_summaries_to_json(summaries, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]['source_url'] == 'https://example.com/1'
            assert data[0]['title'] == 'Test 1'
