"""
Unit tests for T013b: session_validation_metrics.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from session_validation_metrics import calculate_pass_rate, write_metrics

class TestSessionValidationMetrics:
    def test_calculate_pass_rate_normal(self):
        valid = ["sub-01", "sub-02", "sub-03"]
        total = 5
        rate = calculate_pass_rate(valid, total)
        assert rate == 0.6

    def test_calculate_pass_rate_zero_total(self):
        valid = []
        total = 0
        rate = calculate_pass_rate(valid, total)
        assert rate == 0.0

    def test_calculate_pass_rate_all_valid(self):
        valid = ["sub-01", "sub-02"]
        total = 2
        rate = calculate_pass_rate(valid, total)
        assert rate == 1.0

    def test_write_metrics(self):
        metrics = {
            "pass_rate": 0.8,
            "total_subjects": 10,
            "valid_subjects": 8
        }
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)
        
        write_metrics(metrics, temp_path)
        
        assert temp_path.exists()
        with open(temp_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == metrics
        
        temp_path.unlink()