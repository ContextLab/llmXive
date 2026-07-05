"""
Unit tests for the field coverage calculation logic used in T036.
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the functions to test
from tests.integration.test_extractor_accuracy import (
    calculate_field_coverage,
    REQUIRED_FIELDS
)

class TestFieldCoverageCalculation:
    """Test cases for calculate_field_coverage function."""

    def test_empty_summaries(self):
        """Test with empty list."""
        coverage, total, complete = calculate_field_coverage([])
        assert coverage == 0.0
        assert total == 0
        assert complete == 0

    def test_all_fields_present(self):
        """Test when all required fields are present."""
        summaries = [
            {
                "url": "http://example.com/test1",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            },
            {
                "url": "http://example.com/test2",
                "domain": "example.com",
                "outcome_type": "continuous",
                "sample_size_control": 500,
                "sample_size_treatment": 500,
                "metric_control": 10.5,
                "metric_treatment": 12.3,
                "p_value": 0.01
            }
        ]
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 2
        assert complete == 2
        assert coverage == 100.0

    def test_missing_one_field(self):
        """Test when one required field is missing."""
        summaries = [
            {
                "url": "http://example.com/test1",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                # p_value missing
            }
        ]
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 1
        assert complete == 0
        assert coverage == 0.0

    def test_missing_null_field(self):
        """Test when a required field is null."""
        summaries = [
            {
                "url": "http://example.com/test1",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": None
            }
        ]
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 1
        assert complete == 0
        assert coverage == 0.0

    def test_missing_empty_string_field(self):
        """Test when a required field is empty string."""
        summaries = [
            {
                "url": "http://example.com/test1",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": ""
            }
        ]
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 1
        assert complete == 0
        assert coverage == 0.0

    def test_invalid_page_skipped(self):
        """Test that pages without URL or domain are skipped."""
        summaries = [
            {
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            },
            {
                "url": "http://example.com/test2",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            }
        ]
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 1  # Only the second one is valid
        assert complete == 1
        assert coverage == 100.0

    def test_95_percent_threshold(self):
        """Test calculation at exactly 95% and above threshold."""
        # Create 20 records: 19 complete, 1 incomplete = 95%
        summaries = []
        for i in range(19):
            summaries.append({
                "url": f"http://example.com/test{i}",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            })
        # One incomplete
        summaries.append({
            "url": "http://example.com/test19",
            "domain": "example.com",
            "outcome_type": "binary",
            "sample_size_control": 1000,
            "sample_size_treatment": 1000,
            "metric_control": 0.05,
            # metric_treatment missing
            "p_value": 0.03
        })
        
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 20
        assert complete == 19
        assert abs(coverage - 95.0) < 0.01

    def test_above_95_percent(self):
        """Test calculation above 95% threshold."""
        # Create 20 records: 20 complete = 100%
        summaries = []
        for i in range(20):
            summaries.append({
                "url": f"http://example.com/test{i}",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            })
        
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 20
        assert complete == 20
        assert coverage == 100.0
        assert coverage > 95.0

    def test_below_95_percent(self):
        """Test calculation below 95% threshold."""
        # Create 20 records: 18 complete, 2 incomplete = 90%
        summaries = []
        for i in range(18):
            summaries.append({
                "url": f"http://example.com/test{i}",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                "metric_treatment": 0.07,
                "p_value": 0.03
            })
        # Two incomplete
        for i in range(2):
            summaries.append({
                "url": f"http://example.com/test{18+i}",
                "domain": "example.com",
                "outcome_type": "binary",
                "sample_size_control": 1000,
                "sample_size_treatment": 1000,
                "metric_control": 0.05,
                # metric_treatment missing
                "p_value": 0.03
            })
        
        coverage, total, complete = calculate_field_coverage(summaries)
        assert total == 20
        assert complete == 18
        assert abs(coverage - 90.0) < 0.01
        assert coverage < 95.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])