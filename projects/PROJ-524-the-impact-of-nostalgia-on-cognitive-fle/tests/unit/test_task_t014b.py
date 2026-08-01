"""
Unit tests for code/task_t014b_validity_metrics.py.
Tests validity metrics calculation.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t014b_validity_metrics import (
    load_exclusion_log,
    load_raw_count,
    calculate_validity_metrics
)


class TestCalculateValidityMetrics:
    def test_calculate_validity_metrics_basic(self):
        """Test basic validity metrics calculation."""
        raw_count = 100
        exclusion_data = {
            'ERR_MISSING_AGE_FIELD': 10,
            'ERR_MISSING_BIRTH_YEAR': 5,
            'ERR_MISSING_SCORE': 15
        }

        metrics = calculate_validity_metrics(raw_count, exclusion_data)

        assert 'total_raw_records' in metrics
        assert 'total_excluded' in metrics
        assert 'valid_records' in metrics
        assert 'validity_percentage' in metrics

        assert metrics['total_raw_records'] == 100
        assert metrics['total_excluded'] == 30
        assert metrics['valid_records'] == 70
        assert abs(metrics['validity_percentage'] - 70.0) < 0.01

    def test_calculate_validity_metrics_no_exclusions(self):
        """Test validity metrics with no exclusions."""
        raw_count = 100
        exclusion_data = {}

        metrics = calculate_validity_metrics(raw_count, exclusion_data)

        assert metrics['validity_percentage'] == 100.0
        assert metrics['valid_records'] == 100

    def test_calculate_validity_metrics_all_excluded(self):
        """Test validity metrics when all records are excluded."""
        raw_count = 100
        exclusion_data = {
            'ERR_MISSING_AGE_FIELD': 50,
            'ERR_MISSING_BIRTH_YEAR': 50
        }

        metrics = calculate_validity_metrics(raw_count, exclusion_data)

        assert metrics['validity_percentage'] == 0.0
        assert metrics['valid_records'] == 0

    def test_calculate_validity_metrics_breakdown(self):
        """Test validity metrics breakdown by exclusion type."""
        raw_count = 200
        exclusion_data = {
            'ERR_MISSING_AGE_FIELD': 20,
            'ERR_MISSING_BIRTH_YEAR': 10,
            'ERR_MISSING_SCORE': 30
        }

        metrics = calculate_validity_metrics(raw_count, exclusion_data)

        assert 'exclusion_breakdown' in metrics
        assert metrics['exclusion_breakdown']['ERR_MISSING_AGE_FIELD'] == 20
        assert metrics['exclusion_breakdown']['ERR_MISSING_BIRTH_YEAR'] == 10
        assert metrics['exclusion_breakdown']['ERR_MISSING_SCORE'] == 30
