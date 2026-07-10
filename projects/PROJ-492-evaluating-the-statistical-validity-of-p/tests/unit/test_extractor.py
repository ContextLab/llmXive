"""
Unit tests for the extractor module covering edge cases:
- Missing metrics
- Inequality p-values
- Malformed HTML
- Conflicting sample sizes
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.src.audit.extractor import (
    extract_single_float,
    extract_single_int,
    extract_field_from_html,
    extract_summary_from_html,
    extract_all,
    write_summaries_to_json
)
from code.src.models.data_models import ABSummary
from code.src.utils.logger import get_default_logger


class TestExtractSingleFloat:
    def test_valid_float(self):
        html = "<div>Conversion Rate: 0.05</div>"
        result = extract_single_float(html, "Conversion Rate")
        assert result == 0.05

    def test_missing_metric(self):
        html = "<div>No metrics here</div>"
        result = extract_single_float(html, "Conversion Rate")
        assert result is None

    def test_invalid_float_format(self):
        html = "<div>Conversion Rate: high</div>"
        result = extract_single_float(html, "Conversion Rate")
        assert result is None

    def test_inequality_p_value(self):
        # Test handling of inequality p-values like "< 0.05"
        html = "<div>P-value: < 0.05</div>"
        result = extract_single_float(html, "P-value")
        # Should return 0.05, stripping the inequality
        assert result == 0.05

        html = "<div>P-value: > 0.10</div>"
        result = extract_single_float(html, "P-value")
        # Should return 0.10, stripping the inequality
        assert result == 0.10


class TestExtractSingleInt:
    def test_valid_int(self):
        html = "<div>Sample Size: 1000</div>"
        result = extract_single_int(html, "Sample Size")
        assert result == 1000

    def test_missing_metric(self):
        html = "<div>No sample size</div>"
        result = extract_single_int(html, "Sample Size")
        assert result is None

    def test_invalid_int_format(self):
        html = "<div>Sample Size: large</div>"
        result = extract_single_int(html, "Sample Size")
        assert result is None


class TestExtractFieldFromHtml:
    def test_extract_text(self):
        html = "<div class='metric'>500</div>"
        result = extract_field_from_html(html, "div", "metric")
        assert result == "500"

    def test_missing_element(self):
        html = "<div>No metrics</div>"
        result = extract_field_from_html(html, "span", "metric")
        assert result is None

    def test_malformed_html(self):
        # Test with broken HTML
        html = "<div>Unclosed tag"
        result = extract_field_from_html(html, "div", "metric")
        # Should not crash, return None or partial result
        assert result is None


class TestExtractSummaryFromHtml:
    def test_complete_summary(self):
        html = """
        <html>
        <body>
            <div class="summary">
                <span class="baseline">0.05</span>
                <span class="variant">0.07</span>
                <span class="sample_size">1000</span>
                <span class="p_value">0.03</span>
            </div>
        </body>
        </html>
        """
        summary = extract_summary_from_html(html, "http://example.com")
        assert summary is not None
        assert summary.baseline_rate == 0.05
        assert summary.variant_rate == 0.07
        assert summary.sample_size == 1000
        assert summary.p_value == 0.03
        assert summary.url == "http://example.com"

    def test_missing_metrics(self):
        html = """
        <html>
        <body>
            <div class="summary">
                <span class="baseline">0.05</span>
            </div>
        </body>
        </html>
        """
        summary = extract_summary_from_html(html, "http://example.com")
        assert summary is not None
        assert summary.baseline_rate == 0.05
        assert summary.variant_rate is None
        assert summary.sample_size is None
        assert summary.p_value is None

    def test_inequality_p_value(self):
        html = """
        <html>
        <body>
            <div class="summary">
                <span class="baseline">0.05</span>
                <span class="variant">0.07</span>
                <span class="sample_size">1000</span>
                <span class="p_value">&lt; 0.05</span>
            </div>
        </body>
        </html>
        """
        summary = extract_summary_from_html(html, "http://example.com")
        assert summary is not None
        assert summary.p_value == 0.05  # Should parse "< 0.05" as 0.05

    def test_malformed_html(self):
        html = "<html><body><div class='summary' broken"
        summary = extract_summary_from_html(html, "http://example.com")
        # Should handle gracefully, return partial or None
        assert summary is not None  # At least a partial object

    def test_conflicting_sample_sizes(self):
        # Simulate HTML with multiple conflicting sample size indicators
        html = """
        <html>
        <body>
            <div class="summary">
                <span class="baseline">0.05</span>
                <span class="variant">0.07</span>
                <span class="sample_size">1000</span>
                <span class="p_value">0.03</span>
                <div class="details">Total sample: 2000</div>
            </div>
        </body>
        </html>
        """
        summary = extract_summary_from_html(html, "http://example.com")
        # The extractor should handle this - either take first, last, or flag
        # For now, we just verify it doesn't crash
        assert summary is not None
        assert summary.sample_size is not None


class TestExtractAll:
    def test_extract_all_success(self):
        htmls = [
            "<div class='summary'><span class='baseline'>0.05</span><span class='variant'>0.07</span><span class='sample_size'>1000</span><span class='p_value'>0.03</span></div>",
            "<div class='summary'><span class='baseline'>0.10</span><span class='variant'>0.12</span><span class='sample_size'>2000</span><span class='p_value'>0.01</span></div>"
        ]
        urls = ["http://example.com/1", "http://example.com/2"]
        
        summaries = extract_all(list(zip(urls, htmls)))
        
        assert len(summaries) == 2
        assert summaries[0].url == "http://example.com/1"
        assert summaries[1].url == "http://example.com/2"

    def test_extract_all_with_failures(self):
        htmls = [
            "<div class='summary'><span class='baseline'>0.05</span><span class='variant'>0.07</span><span class='sample_size'>1000</span><span class='p_value'>0.03</span></div>",
            "<div>Malformed</div>",
            "<div class='summary'><span class='baseline'>0.10</span><span class='variant'>0.12</span><span class='sample_size'>2000</span><span class='p_value'>0.01</span></div>"
        ]
        urls = ["http://example.com/1", "http://example.com/2", "http://example.com/3"]
        
        summaries = extract_all(list(zip(urls, htmls)))
        
        # Should extract successfully where possible, skip or log failures
        assert len(summaries) >= 2  # At least the successful ones

    def test_extract_all_malformed_html(self):
        htmls = [
            "<div class='summary' broken",
            "<div class='summary'><span class='baseline'>0.05</span></div>"
        ]
        urls = ["http://example.com/1", "http://example.com/2"]
        
        summaries = extract_all(list(zip(urls, htmls)))
        
        # Should handle malformed HTML gracefully
        assert len(summaries) >= 1


class TestWriteSummariesToJson:
    def test_write_summaries(self):
        summaries = [
            ABSummary(
                url="http://example.com/1",
                baseline_rate=0.05,
                variant_rate=0.07,
                sample_size=1000,
                p_value=0.03
            ),
            ABSummary(
                url="http://example.com/2",
                baseline_rate=0.10,
                variant_rate=0.12,
                sample_size=2000,
                p_value=0.01
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summaries.json"
            write_summaries_to_json(summaries, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['url'] == "http://example.com/1"
            assert data[1]['url'] == "http://example.com/2"

    def test_write_summaries_empty(self):
        summaries = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summaries.json"
            write_summaries_to_json(summaries, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 0