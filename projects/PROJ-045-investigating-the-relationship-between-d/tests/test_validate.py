"""
Tests for the validate.py module.

These tests verify that the validation logic correctly identifies
missing required variables and generates accurate completeness reports.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate import (
    validate_defect_data_completeness,
    validate_dataset_completeness,
    generate_completeness_report,
    REQUIRED_VARIABLES
)

@pytest.fixture
def complete_sample_data():
    """Sample data with all required variables present."""
    return {
        "composition_id": "Li123",
        "vacancy": {"count": 2, "type": "Li_vacancy"},
        "interstitial": {"count": 1, "type": "Li_interstitial"},
        "antisite": {"count": 0, "type": None},
        "migration_barrier": 0.45,
        "conductivity": 1.2e-3
    }

@pytest.fixture
def incomplete_sample_data():
    """Sample data with some required variables missing."""
    return {
        "composition_id": "Li456",
        "vacancy": {"count": 1, "type": "Li_vacancy"},
        # interstitial missing
        "antisite": {"count": 0, "type": None},
        # migration_barrier missing
        "conductivity": 0.8e-3
    }

@pytest.fixture
def empty_sample_data():
    """Sample data with no required variables."""
    return {
        "composition_id": "Li789",
        "other_field": "some_value"
    }

@pytest.fixture
def dataset_mixed():
    """Dataset with mixed completeness."""
    return [
        {
            "composition_id": "comp_1",
            "vacancy": {"count": 1},
            "interstitial": {"count": 0},
            "antisite": {"count": 0},
            "migration_barrier": 0.5,
            "conductivity": 1.0e-3
        },
        {
            "composition_id": "comp_2",
            "vacancy": {"count": 2},
            # missing interstitial, migration_barrier
            "conductivity": 0.5e-3
        },
        {
            "composition_id": "comp_3",
            "vacancy": {"count": 1},
            "interstitial": {"count": 1},
            "antisite": {"count": 0},
            "migration_barrier": 0.3,
            "conductivity": 1.5e-3
        }
    ]

def test_validate_complete_data(complete_sample_data):
    """Test validation with all required variables present."""
    result = validate_defect_data_completeness(complete_sample_data)
    
    assert result["is_complete"] is True
    assert len(result["missing_variables"]) == 0
    assert len(result["present_variables"]) == len(REQUIRED_VARIABLES)
    assert set(result["present_variables"]) == set(REQUIRED_VARIABLES)

def test_validate_incomplete_data(incomplete_sample_data):
    """Test validation with missing variables."""
    result = validate_defect_data_completeness(incomplete_sample_data)
    
    assert result["is_complete"] is False
    assert "interstitial" in result["missing_variables"]
    assert "migration_barrier" in result["missing_variables"]
    assert len(result["missing_variables"]) == 2
    assert len(result["present_variables"]) == 3

def test_validate_empty_data(empty_sample_data):
    """Test validation with no required variables."""
    result = validate_defect_data_completeness(empty_sample_data)
    
    assert result["is_complete"] is False
    assert len(result["missing_variables"]) == len(REQUIRED_VARIABLES)
    assert set(result["missing_variables"]) == set(REQUIRED_VARIABLES)

def test_validate_dataset_complete():
    """Test dataset validation with all complete samples."""
    dataset = [
        {
            "composition_id": "c1",
            "vacancy": {}, "interstitial": {}, "antisite": {},
            "migration_barrier": 0.5, "conductivity": 1e-3
        },
        {
            "composition_id": "c2",
            "vacancy": {}, "interstitial": {}, "antisite": {},
            "migration_barrier": 0.6, "conductivity": 2e-3
        }
    ]
    
    result = validate_dataset_completeness(dataset)
    
    assert result["total_compositions"] == 2
    assert result["complete_count"] == 2
    assert result["incomplete_count"] == 0
    assert result["completeness_rate"] == 100.0

def test_validate_dataset_mixed(dataset_mixed):
    """Test dataset validation with mixed completeness."""
    result = validate_dataset_completeness(dataset_mixed)
    
    assert result["total_compositions"] == 3
    assert result["complete_count"] == 2  # comp_1 and comp_3
    assert result["incomplete_count"] == 1  # comp_2
    assert abs(result["completeness_rate"] - 66.67) < 0.1
    
    # Check missing variable summary
    assert result["missing_variable_summary"]["interstitial"] == 1
    assert result["missing_variable_summary"]["migration_barrier"] == 1
    assert result["missing_variable_summary"]["vacancy"] == 0

def test_generate_completeness_report(tmp_path, dataset_mixed):
    """Test completeness report generation."""
    output_file = tmp_path / "test_report.json"
    
    result_path = generate_completeness_report(dataset_mixed, output_file)
    
    assert result_path.exists()
    assert result_path == output_file
    
    # Verify report contents
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    assert report["report_type"] == "dataset_completeness"
    assert report["total_compositions"] == 3
    assert report["complete_count"] == 2
    assert report["incomplete_count"] == 1
    assert "per_composition_results" in report
    assert "missing_variable_summary" in report

def test_required_variables_constant():
    """Test that REQUIRED_VARIABLES contains the expected variables."""
    expected = ["vacancy", "interstitial", "antisite", "migration_barrier", "conductivity"]
    assert REQUIRED_VARIABLES == expected
    assert len(REQUIRED_VARIABLES) == 5