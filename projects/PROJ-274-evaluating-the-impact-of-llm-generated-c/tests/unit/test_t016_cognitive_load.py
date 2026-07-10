import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data_collection import (
    calculate_cognitive_load_proxy,
    log_help_request,
    process_help_requests,
    HELP_KEYWORDS
)

def test_calculate_cognitive_load_proxy_empty():
    """Test with no help requests."""
    result = calculate_cognitive_load_proxy([])
    assert result['total_help_requests'] == 0
    assert result['average_time_per_request_seconds'] == 0.0
    assert result['composite_cognitive_load_proxy'] == 0.0

def test_calculate_cognitive_load_proxy_single_request():
    """Test with a single request (no delta possible)."""
    requests = [
        {'participant_id': 'P001', 'timestamp': '2023-01-01T10:00:00', 'content': 'How do I run this?'}
    ]
    result = calculate_cognitive_load_proxy(requests)
    assert result['total_help_requests'] == 1
    assert result['average_time_per_request_seconds'] == 0.0
    # Composite = Count * AvgTime = 1 * 0 = 0
    assert result['composite_cognitive_load_proxy'] == 0.0

def test_calculate_cognitive_load_proxy_multiple_requests():
    """Test with multiple requests from one participant."""
    # P001: 10:00, 10:05 (5 min), 10:15 (10 min) -> Avg delta = 7.5 min = 450s
    # P002: 11:00, 11:30 (30 min) -> Avg delta = 30 min = 1800s
    requests = [
        {'participant_id': 'P001', 'timestamp': '2023-01-01T10:00:00', 'content': 'What is this?'},
        {'participant_id': 'P001', 'timestamp': '2023-01-01T10:05:00', 'content': 'How to install?'},
        {'participant_id': 'P001', 'timestamp': '2023-01-01T10:15:00', 'content': 'Explain this'},
        {'participant_id': 'P002', 'timestamp': '2023-01-01T11:00:00', 'content': 'Why does it fail?'},
        {'participant_id': 'P002', 'timestamp': '2023-01-01T11:30:00', 'content': 'Help needed'}
    ]
    
    result = calculate_cognitive_load_proxy(requests)
    
    assert result['total_help_requests'] == 5
    # P001 deltas: 300s, 600s -> avg 450s
    # P002 deltas: 1800s -> avg 1800s
    # Overall avg time: (450 + 1800) / 2 = 1125s
    expected_avg_time = 1125.0
    assert abs(result['average_time_per_request_seconds'] - expected_avg_time) < 0.01
    
    # Composite = 5 * 1125 = 5625
    expected_composite = 5 * expected_avg_time
    assert abs(result['composite_cognitive_load_proxy'] - expected_composite) < 0.01

def test_log_help_request():
    """Test logging a help request."""
    req = log_help_request([], 'P001', 'How do I do this?')
    assert req['participant_id'] == 'P001'
    assert 'how' in req['content'].lower()
    assert req['type'] == 'help_request'
    assert 'timestamp' in req

def test_keyword_filtering_logic():
    """Verify the keywords used for filtering."""
    expected_keywords = ['how', 'why', 'what', 'explain']
    assert HELP_KEYWORDS == expected_keywords