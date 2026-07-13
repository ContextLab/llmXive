"""
Unit tests for the extractor module.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from code.src.audit.extractor import (
    extract_single_float,
    extract_single_int,
    extract_field_from_html,
    extract_summary_from_html,
    extract_all,
    write_summaries_to_json,
)
from code.src.models.data_models import ABTestSummary
from bs4 import BeautifulSoup


class TestExtractSingleFloat:
    def test_valid_float(self):
        assert extract_single_float("0.05", "p_value") == 0.05

    def test_valid_float_with_whitespace(self):
        assert extract_single_float("  0.05  ", "p_value") == 0.05

    def test_percentage_format(self):
        assert extract_single_float("5%", "p_value") == 0.05

    def test_inequality_less_than(self):
        assert extract_single_float("<0.001", "p_value") < 0.001

    def test_inequality_greater_than(self):
        assert extract_single_float(">0.1", "p_value") > 0.1

    def test_null_input(self):
        assert extract_single_float(None, "p_value") is None

    def test_empty_string(self):
        assert extract_single_float("", "p_value") is None

    def test_invalid_text(self):
        assert extract_single_float("invalid", "p_value") is None

    def test_text_with_number(self):
        assert extract_single_float("p = 0.03", "p_value") == 0.03


class TestExtractSingleInt:
    def test_valid_int(self):
        assert extract_single_int("100", "sample_size") == 100

    def test_valid_int_with_commas(self):
        assert extract_single_int("1,000", "sample_size") == 1000

    def test_float_string(self):
        assert extract_single_int("100.0", "sample_size") == 100

    def test_null_input(self):
        assert extract_single_int(None, "sample_size") is None

    def test_empty_string(self):
        assert extract_single_int("", "sample_size") is None

    def test_invalid_text(self):
        assert extract_single_int("invalid", "sample_size") is None

    def test_text_with_number(self):
        assert extract_single_int("N=150", "sample_size") == 150


class TestExtractFieldFromHtml:
    def test_find_with_selector(self):
        html = '<div class="p-value">0.05</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.p-value'], 'p_value')
        assert result == "0.05"

    def test_multiple_selectors(self):
        html = '<div class="other">0.01</div><div class="p-value">0.05</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.p-value', '.other'], 'p_value')
        assert result == "0.05"

    def test_not_found(self):
        html = '<div class="other">0.01</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.p-value'], 'p_value')
        assert result is None

    def test_empty_element(self):
        html = '<div class="p-value"></div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, ['.p-value'], 'p_value')
        assert result is None


class TestExtractSummaryFromHtml:
    def setup_method(self):
        self.html_content = """
        <html>
        <body>
            <span class="baseline-rate">0.10</span>
            <span class="treatment-rate">0.12</span>
            <span class="control-n">1000</span>
            <span class="treatment-n">1000</span>
            <span class="p-value">0.03</span>
            <span class="effect-size">0.02</span>
            <meta name="domain" content="example.com">
            <meta name="year" content="2024">
        </body>
        </html>
        """

    def test_successful_extraction(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(self.html_content)
            temp_path = Path(f.name)

        try:
            summary = extract_summary_from_html(temp_path, "https://example.com/test")
            assert summary is not None
            assert summary.baseline_rate == 0.10
            assert summary.treatment_rate == 0.12
            assert summary.sample_size_control == 1000
            assert summary.sample_size_treatment == 1000
            assert summary.p_value == 0.03
            assert summary.effect_size == 0.02
            assert summary.domain == "example.com"
            assert summary.publication_year == 2024
        finally:
            temp_path.unlink()

    def test_missing_fields(self):
        html = "<html><body>No data here</body></html>"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = Path(f.name)

        try:
            summary = extract_summary_from_html(temp_path, "https://example.com/test")
            # Should still create a summary with None values
            assert summary is not None
            assert summary.url == "https://example.com/test"
        finally:
            temp_path.unlink()

    def test_invalid_html_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / "nonexistent.html"
            summary = extract_summary_from_html(fake_path, "https://example.com/test")
            assert summary is None


class TestExtractAll:
    def test_extract_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_path = input_dir / "summaries.json"

            # Create test HTML files
            html1 = """
            <html><body>
            <span class="baseline-rate">0.10</span>
            <span class="treatment-rate">0.12</span>
            <span class="control-n">1000</span>
            <span class="treatment-n">1000</span>
            <span class="p-value">0.03</span>
            </body></html>
            """
            (input_dir / "test1.html").write_text(html1)

            html2 = """
            <html><body>
            <span class="baseline-rate">0.20</span>
            <span class="treatment-rate">0.25</span>
            <span class="control-n">500</span>
            <span class="treatment-n">500</span>
            <span class="p-value">0.01</span>
            </body></html>
            """
            (input_dir / "test2.html").write_text(html2)

            summaries = extract_all(input_dir, output_path)

            assert len(summaries) == 2
            assert output_path.exists()

            # Verify JSON content
            with open(output_path) as f:
                data = json.load(f)
                assert len(data) == 2

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_path = input_dir / "summaries.json"

            summaries = extract_all(input_dir, output_path)
            assert len(summaries) == 0
            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)
                assert data == []


class TestWriteSummariesToJson:
    def test_write_summaries(self):
        summaries = [
            ABTestSummary(
                url="https://example.com/1",
                domain="example.com",
                baseline_rate=0.10,
                treatment_rate=0.12,
                sample_size_control=1000,
                sample_size_treatment=1000,
                p_value=0.03,
            ),
            ABTestSummary(
                url="https://example.com/2",
                domain="example.com",
                baseline_rate=0.20,
                treatment_rate=0.25,
                sample_size_control=500,
                sample_size_treatment=500,
                p_value=0.01,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summaries.json"
            write_summaries_to_json(summaries, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]['url'] == "https://example.com/1"
                assert data[1]['url'] == "https://example.com/2"