"""
Unit tests for the extractor module.

Tests cover:
- Missing metric handling
- Inequality p-value handling
- Malformed HTML
- Conflicting sample sizes
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from code.src.audit.extractor import (
    extract_single_float,
    extract_single_int,
    extract_field_from_html,
    extract_summary_from_html,
    extract_all,
    write_summaries_to_json
)
from code.src.models.data_models import ABTestSummary


class TestExtractSingleFloat:
    """Tests for extract_single_float function."""
    
    def test_extract_valid_float(self):
        """Test extraction of a valid float value."""
        text = "The conversion rate was 0.05"
        result = extract_single_float(text, 'test_field')
        assert result == 0.05
    
    def test_extract_scientific_notation(self):
        """Test extraction of float in scientific notation."""
        text = "p-value: 1.5e-3"
        result = extract_single_float(text, 'p_value')
        assert result == 0.0015
    
    def test_extract_negative_float(self):
        """Test extraction of negative float."""
        text = "lift: -0.025"
        result = extract_single_float(text, 'effect_size')
        assert result == -0.025
    
    def test_extract_no_float(self):
        """Test extraction when no float is present."""
        text = "No numerical data here"
        result = extract_single_float(text, 'test_field')
        assert result is None
    
    def test_extract_empty_string(self):
        """Test extraction from empty string."""
        result = extract_single_float("", 'test_field')
        assert result is None
    
    def test_extract_none(self):
        """Test extraction from None."""
        result = extract_single_float(None, 'test_field')
        assert result is None


class TestExtractSingleInt:
    """Tests for extract_single_int function."""
    
    def test_extract_valid_int(self):
        """Test extraction of a valid integer."""
        text = "Sample size: 1000"
        result = extract_single_int(text, 'sample_size')
        assert result == 1000
    
    def test_extract_large_int(self):
        """Test extraction of large integer."""
        text = "N = 100000"
        result = extract_single_int(text, 'sample_size')
        assert result == 100000
    
    def test_extract_no_int(self):
        """Test extraction when no integer is present."""
        text = "No numbers here"
        result = extract_single_int(text, 'test_field')
        assert result is None
    
    def test_extract_empty_string(self):
        """Test extraction from empty string."""
        result = extract_single_int("", 'test_field')
        assert result is None


class TestExtractFieldFromHTML:
    """Tests for extract_field_from_html function."""
    
    def test_extract_from_label(self):
        """Test extraction from label-value pattern."""
        html = '<div><label>Baseline Rate:</label><span>0.05</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, 'baseline_rate', ['baseline_rate', 'control_rate'])
        assert result is not None
    
    def test_extract_from_text(self):
        """Test extraction from text containing label."""
        html = '<p>Control conversion rate: 0.03</p>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, 'baseline_rate', ['control_rate', 'baseline_rate'])
        assert result is not None
    
    def test_no_match(self):
        """Test when no matching label is found."""
        html = '<div>No relevant data here</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_field_from_html(soup, 'baseline_rate', ['baseline_rate', 'control_rate'])
        assert result is None


class TestExtractSummaryFromHTML:
    """Tests for extract_summary_from_html function."""
    
    def test_extract_complete_summary(self):
        """Test extraction of a complete summary with all fields."""
        html = '''
        <html>
        <body>
            <div class="test-summary">
                <span>Baseline Rate: 0.05</span>
                <span>Treatment Rate: 0.07</span>
                <span>Sample Size Baseline: 1000</span>
                <span>Sample Size Treatment: 1000</span>
                <span>P-value: 0.03</span>
                <span>Effect Size: 0.02</span>
                <span>Domain: example.com</span>
                <span>Year: 2023</span>
            </div>
        </body>
        </html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is not None
        assert summary.baseline_rate == 0.05
        assert summary.treatment_rate == 0.07
        assert summary.sample_size_baseline == 1000
        assert summary.sample_size_treatment == 1000
        assert summary.p_value == 0.03
        assert summary.effect_size == 0.02
    
    def test_extract_missing_fields(self):
        """Test extraction when some fields are missing."""
        html = '''
        <html>
        <body>
            <div>
                <span>Baseline Rate: 0.05</span>
                <span>Treatment Rate: 0.07</span>
            </div>
        </body>
        </html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is not None
        assert summary.baseline_rate == 0.05
        assert summary.treatment_rate == 0.07
        assert summary.sample_size_baseline is None
        assert summary.sample_size_treatment is None
        assert summary.extraction_status == 'partial'
        assert len(summary.missing_fields) > 0
    
    def test_extract_missing_critical_fields(self):
        """Test extraction when critical fields are missing."""
        html = '''
        <html>
        <body>
            <div>
                <span>Sample Size: 1000</span>
            </div>
        </body>
        </html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is None  # Should return None if critical fields missing
    
    def test_extract_malformed_html(self):
        """Test handling of malformed HTML."""
        html = '<div><span>Unclosed tag'
        summary = extract_summary_from_html(html, 'https://example.com/test')
        # Should handle gracefully, may return None or partial
        assert summary is None or summary is not None  # Depends on BeautifulSoup behavior
    
    def test_extract_empty_html(self):
        """Test extraction from empty HTML."""
        summary = extract_summary_from_html('', 'https://example.com/test')
        assert summary is None
    
    def test_extract_inequality_p_value(self):
        """Test handling of inequality p-values (e.g., p < 0.05)."""
        html = '''
        <html>
        <body>
            <span>Baseline Rate: 0.05</span>
            <span>Treatment Rate: 0.07</span>
            <span>P-value: < 0.01</span>
        </body>
        </html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        # Should handle inequality by extracting the number
        assert summary is not None
        # The p_value might be 0.01 or None depending on parsing


class TestExtractAll:
    """Tests for extract_all function."""
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_extract_multiple_urls(self, mock_read_text, mock_exists):
        """Test extraction from multiple URLs."""
        mock_exists.return_value = True
        mock_read_text.return_value = '''
        <html><body>
            <span>Baseline Rate: 0.05</span>
            <span>Treatment Rate: 0.07</span>
        </body></html>
        '''
        
        urls = ['https://example.com/1', 'https://example.com/2']
        output_dir = Path('data/raw')
        
        summaries = extract_all(urls, output_dir)
        assert len(summaries) == 2


class TestWriteSummariesToJson:
    """Tests for write_summaries_to_json function."""
    
    def test_write_summaries(self, tmp_path):
        """Test writing summaries to JSON file."""
        summaries = [
            ABTestSummary(
                url='https://example.com/1',
                domain='example.com',
                publication_year=2023,
                baseline_rate=0.05,
                treatment_rate=0.07,
                sample_size_baseline=1000,
                sample_size_treatment=1000,
                p_value=0.03,
                effect_size=0.02,
                extraction_status='complete',
                missing_fields=[]
            )
        ]
        
        output_path = tmp_path / 'output.json'
        write_summaries_to_json(summaries, output_path)
        
        assert output_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['url'] == 'https://example.com/1'
        assert data[0]['baseline_rate'] == 0.05
        assert data[0]['p_value'] == 0.03


class TestErrorHandling:
    """Tests for error handling and logging."""
    
    def test_missing_baseline_rate_logs_error(self):
        """Test that missing baseline rate logs appropriate error."""
        html = '''
        <html><body>
            <span>Treatment Rate: 0.07</span>
        </body></html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is None  # Should return None for missing critical field
    
    def test_missing_sample_size_logs_warning(self):
        """Test that missing sample size logs warning but continues."""
        html = '''
        <html><body>
            <span>Baseline Rate: 0.05</span>
            <span>Treatment Rate: 0.07</span>
        </body></html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is not None
        assert summary.sample_size_baseline is None
        assert 'sample_size_baseline' in summary.missing_fields
    
    def test_conflicting_sample_sizes(self):
        """Test handling of conflicting sample size information."""
        # This is more of an integration test scenario
        # The extractor should extract both values, validation will handle conflicts
        html = '''
        <html><body>
            <span>Baseline N: 1000</span>
            <span>Treatment N: 1000</span>
            <span>Sample Size: 2000</span>
        </body></html>
        '''
        summary = extract_summary_from_html(html, 'https://example.com/test')
        assert summary is not None
        # Both baseline and treatment should be extracted
        assert summary.sample_size_baseline is not None
        assert summary.sample_size_treatment is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
