"""
Unit tests for the data quality logging module (code/log_data_quality.py).
"""

import os
import sys
import json
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from log_data_quality import (
    load_aligned_events,
    calculate_missing_counts,
    calculate_alignment_success_rate,
    log_data_quality_metrics
)


@pytest.fixture
def sample_events():
    """Fixture providing a list of sample event dictionaries."""
    return [
        {
            'flare_id': 'FL001',
            'cme_id': 'CME001',
            'cme_speed_kms': '750',
            'cme_width_deg': '60',
            'flare_flux_w_m2': '1.2e-4',
            'flare_class': 'M1.0',
            'dst_min': '-50'
        },
        {
            'flare_id': 'FL002',
            'cme_id': '',  # Missing CME
            'cme_speed_kms': '',  # Missing speed
            'cme_width_deg': '45',
            'flare_flux_w_m2': '5.0e-5',
            'flare_class': 'C5.0',
            'dst_min': '-30'
        },
        {
            'flare_id': '',  # Missing Flare ID
            'cme_id': 'CME003',
            'cme_speed_kms': '1200',
            'cme_width_deg': '',  # Missing width
            'flare_flux_w_m2': '',  # Missing flux
            'flare_class': '',  # Missing class
            'dst_min': '-80'
        },
        {
            'flare_id': 'FL004',
            'cme_id': 'CME004',
            'cme_speed_kms': 'NaN',  # Explicit NaN string
            'cme_width_deg': '120',
            'flare_flux_w_m2': '2.0e-3',
            'flare_class': 'X1.0',
            'dst_min': '-100'
        }
    ]


@pytest.fixture
def temp_csv_file(sample_events):
    """Fixture creating a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
        if sample_events:
            fieldnames = list(sample_events[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_events)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_load_aligned_events_valid(temp_csv_file):
    """Test loading a valid CSV file."""
    events = load_aligned_events(Path(temp_csv_file))
    assert len(events) == 4
    assert events[0]['flare_id'] == 'FL001'


def test_load_aligned_events_missing_file():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_aligned_events(Path('/nonexistent/path/file.csv'))


def test_calculate_missing_counts(sample_events):
    """Test missing count calculation logic."""
    missing_counts, total = calculate_missing_counts(sample_events)
    
    assert total == 4
    # cme_speed_kms: 1 empty, 1 NaN -> 2 missing
    assert missing_counts['cme_speed_kms'] == 2
    # cme_width_deg: 1 empty -> 1 missing
    assert missing_counts['cme_width_deg'] == 1
    # flare_flux_w_m2: 1 empty -> 1 missing
    assert missing_counts['flare_flux_w_m2'] == 1
    # flare_class: 1 empty -> 1 missing
    assert missing_counts['flare_class'] == 1
    # dst_min: 0 missing
    assert missing_counts['dst_min'] == 0


def test_calculate_alignment_success_rate(sample_events):
    """Test alignment success rate calculation."""
    stats = calculate_alignment_success_rate(sample_events)
    
    # Total 4
    # Row 1: Has both -> Matched
    # Row 2: Has flare, no cme -> Matched (has at least one)
    # Row 3: No flare, has cme -> Matched (has at least one)
    # Row 4: Has both -> Matched
    # All 4 should be matched based on logic (has flare_id OR cme_id)
    
    assert stats['total_storms'] == 4
    assert stats['matched_storms'] == 4
    assert stats['unmatched_storms'] == 0
    assert stats['match_rate'] == 1.0


def test_calculate_alignment_success_rate_empty():
    """Test alignment rate with empty list."""
    stats = calculate_alignment_success_rate([])
    assert stats['total_storms'] == 0
    assert stats['match_rate'] == 0.0


def test_log_data_quality_metrics_creates_file(sample_events, tmp_path):
    """Test that the metrics function creates the output JSON file."""
    output_path = tmp_path / "metrics.json"
    
    metrics = log_data_quality_metrics(sample_events, output_path)
    
    assert output_path.exists()
    assert 'total_records' in metrics
    assert 'missing_value_counts' in metrics
    assert 'alignment_statistics' in metrics
    assert metrics['total_records'] == 4

    # Verify JSON content is valid
    with open(output_path, 'r') as f:
        loaded_data = json.load(f)
        assert loaded_data['total_records'] == 4