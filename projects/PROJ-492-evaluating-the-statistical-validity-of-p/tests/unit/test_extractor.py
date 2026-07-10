"""
Unit tests for the extractor module.
Tests missing metric handling, inequality p-values, malformed HTML, and conflicting sample sizes.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.audit.extractor import (
    extract_summary_from_html,
    extract_all,
    write_summaries_to_json,
    extract_single_float,
    extract_single_int,
)
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import AuditLogger, get_error_message

@pytest.fixture
def sample_html():
    return """
    <html>
    <body>
        <h1>A/B Test Results</h1>
        <p>Control group (n=1000): 5% conversion rate</p>
        <p>Treatment group (n=1200): 6% conversion rate</p>
        <p>P-value: 0.03</p>
        <p>Effect size: 1% lift</p>
    </body>
    </html>
    """

@pytest.fixture
def sample_metadata():
    return [
        {
            'url': 'http://example.com/test1',
            'fetch_timestamp': '2024-01-01T00:00:00Z',
            'source_id': 'test-source'
        }
    ]

def test_extract_summary_from_html_all_fields_present(sample_html):
    """Test extraction when all fields are present."""
    summary = extract_summary_from_html(
        sample_html,
        'http://example.com/test1',
        '2024-01-01T00:00:00Z',
        'test-source'
    )
    
    assert summary.url == 'http://example.com/test1'
    assert summary.source_id == 'test-source'
    assert summary.fetch_timestamp == '2024-01-01T00:00:00Z'
    assert summary.p_value == pytest.approx(0.03, abs=0.001)
    assert summary.effect_size == pytest.approx(1.0, abs=0.1)
    assert summary.n_control == 1000
    assert summary.n_treatment == 1200
    assert summary.baseline_rate == pytest.approx(5.0, abs=0.1)
    assert summary.treatment_rate == pytest.approx(6.0, abs=0.1)
    assert summary.domain == 'example.com'

def test_extract_summary_from_html_missing_p_value():
    """Test extraction when p-value is missing."""
    html = """
    <html>
    <body>
        <p>Control: 5%, n=1000</p>
        <p>Treatment: 6%, n=1200</p>
        <p>Effect: 1% lift</p>
    </body>
    </html>
    """
    
    summary = extract_summary_from_html(
        html,
        'http://example.com/test2',
        '2024-01-01T00:00:00Z',
        'test-source'
    )
    
    assert summary.p_value is None
    # Verify error was logged
    # Note: In a real test, we'd check the log, but for now we verify the field is None

def test_extract_summary_from_html_inequality_p_value():
    """Test extraction when p-value is an inequality (e.g., p < 0.05)."""
    html = """
    <html>
    <body>
        <p>Control: 5%, n=1000</p>
        <p>Treatment: 6%, n=1200</p>
        <p>p < 0.05</p>
        <p>Effect: 1% lift</p>
    </body>
    </html>
    """
    
    summary = extract_summary_from_html(
        html,
        'http://example.com/test3',
        '2024-01-01T00:00:00Z',
        'test-source'
    )
    
    assert summary.p_value is not None
    assert summary.p_value == pytest.approx(0.05, abs=0.001)

def test_extract_summary_from_html_malformed_html():
    """Test extraction with malformed or empty HTML."""
    html = "<html><body></body></html>"
    
    summary = extract_summary_from_html(
        html,
        'http://example.com/test4',
        '2024-01-01T00:00:00Z',
        'test-source'
    )
    
    assert summary.p_value is None
    assert summary.effect_size is None
    assert summary.n_control is None
    assert summary.n_treatment is None
    assert summary.baseline_rate is None
    assert summary.treatment_rate is None

def test_extract_single_float():
    """Test float extraction helper."""
    text = "p-value is 0.032"
    from code.src.audit.extractor import PATTERNS
    result = extract_single_float(text, PATTERNS['p_value'])
    assert result == pytest.approx(0.032, abs=0.001)

def test_extract_single_int():
    """Test int extraction helper."""
    text = "n = 1500"
    from code.src.audit.extractor import PATTERNS
    result = extract_single_int(text, PATTERNS['sample_size_control'])
    assert result == 1500

def test_write_summaries_to_json():
    """Test writing summaries to JSON file."""
    summaries = [
        ABTestSummary(
            url='http://example.com/test1',
            source_id='test-source',
            fetch_timestamp='2024-01-01T00:00:00Z',
            p_value=0.03,
            effect_size=1.0,
            n_control=1000,
            n_treatment=1200,
            baseline_rate=5.0,
            treatment_rate=6.0,
            domain='example.com'
        )
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_output.json'
        write_summaries_to_json(summaries, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['url'] == 'http://example.com/test1'
        assert data[0]['p_value'] == 0.03

def test_extract_all_with_mixed_files(sample_metadata):
    """Test extraction from multiple HTML files with mixed validity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir)
        
        # Create valid HTML file
        valid_html = """
        <html>
        <body>
            <p>Control: 5%, n=1000</p>
            <p>Treatment: 6%, n=1200</p>
            <p>p-value: 0.03</p>
            <p>Effect: 1% lift</p>
        </body>
        </html>
        """
        valid_path = input_dir / "http___example_com_test1.html"
        with open(valid_path, 'w') as f:
            f.write(valid_html)
        
        # Create invalid HTML file
        invalid_html = "<html><body></body></html>"
        invalid_path = input_dir / "http___example_com_test2.html"
        with open(invalid_path, 'w') as f:
            f.write(invalid_html)
        
        # Update metadata
        sample_metadata.append({
            'url': 'http://example.com/test2',
            'fetch_timestamp': '2024-01-01T00:00:01Z',
            'source_id': 'test-source'
        })
        
        # Create metadata file
        metadata_path = Path(tmpdir) / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(sample_metadata, f)
        
        # Build html_files list
        html_files = [
            {
                'url': sample_metadata[0]['url'],
                'fetch_timestamp': sample_metadata[0]['fetch_timestamp'],
                'source_id': sample_metadata[0]['source_id'],
                'html_path': str(valid_path)
            },
            {
                'url': sample_metadata[1]['url'],
                'fetch_timestamp': sample_metadata[1]['fetch_timestamp'],
                'source_id': sample_metadata[1]['source_id'],
                'html_path': str(invalid_path)
            }
        ]
        
        summaries = extract_all(html_files)
        
        assert len(summaries) == 2
        assert summaries[0].p_value is not None
        assert summaries[1].p_value is None

def test_extract_summary_from_html_conflicting_sample_sizes():
    """Test extraction when sample sizes are conflicting or inconsistent."""
    html = """
    <html>
    <body>
        <p>Control group: n=1000</p>
        <p>Treatment group: n=1000</p>
        <p>Wait, actually treatment n=5000</p>
        <p>p-value: 0.03</p>
        <p>Effect: 1% lift</p>
    </body>
    </html>
    """
    
    # Note: Current implementation takes the first match
    # In a more advanced version, we might detect conflicts
    summary = extract_summary_from_html(
        html,
        'http://example.com/test5',
        '2024-01-01T00:00:00Z',
        'test-source'
    )
    
    # Should extract the first occurrence
    assert summary.n_control == 1000
    assert summary.n_treatment == 1000  # First match