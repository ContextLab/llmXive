"""
Unit tests for ingestion logging and data quality metrics.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.ingest import (
    log_exclusion_reason,
    calculate_data_quality_metrics,
    EXCLUSION_REASONS,
)

@pytest.fixture
def reset_exclusion_counts():
    """Fixture to reset exclusion counts before and after tests."""
    # Save original counts
    original = {k: v for k, v in EXCLUSION_REASONS.items()}
    yield
    # Restore original counts
    EXCLUSION_REASONS.update(original)

def test_log_exclusion_reason_valid(reset_exclusion_counts):
    """Test logging a valid exclusion reason."""
    initial_count = EXCLUSION_REASONS["INVALID_SMILES"]
    log_exclusion_reason("INVALID_SMILES", 5)
    assert EXCLUSION_REASONS["INVALID_SMILES"] == initial_count + 5

def test_log_exclusion_reason_unknown(reset_exclusion_counts):
    """Test logging an unknown exclusion reason doesn't crash."""
    # Should not raise an exception
    log_exclusion_reason("UNKNOWN_REASON", 1)
    # Count should remain unchanged
    assert EXCLUSION_REASONS["UNKNOWN_REASON"] == 0

def test_calculate_data_quality_metrics_basic():
    """Test basic quality metrics calculation."""
    raw_df = pd.DataFrame({
        "smiles": ["CCO", "CCO", "invalid", "CCO"],
        "yield": [80.0, 90.0, None, 70.0],
    })
    cleaned_df = pd.DataFrame({
        "smiles": ["CCO", "CCO", "CCO"],
        "yield": [80.0, 90.0, 70.0],
        "ecfp4": [[1] * 2048, [1] * 2048, [1] * 2048],
        "maccs": [[1] * 167, [1] * 167, [1] * 167],
    })
    exclusion_counts = {
        "INVALID_SMILES": 1,
        "MISSING_YIELD": 0,
        "INVALID_YIELD": 0,
        "SALT_REMOVAL_FAILED": 0,
        "FINGERPRINT_GENERATION_FAILED": 0,
        "EMPTY_REACTION": 0,
    }

    report = calculate_data_quality_metrics(
        raw_df, cleaned_df, exclusion_counts, 10.5
    )

    assert report["dataset_sizes"]["raw_records"] == 4
    assert report["dataset_sizes"]["cleaned_records"] == 3
    assert report["dataset_sizes"]["excluded_records"] == 1
    assert report["dataset_sizes"]["exclusion_rate_percent"] == 25.0
    assert report["processing_time_seconds"] == 10.5
    assert "yield_statistics" in report
    assert "fingerprint_statistics" in report
    assert "data_completeness" in report

def test_calculate_data_quality_metrics_empty_cleaned():
    """Test metrics when cleaned dataset is empty."""
    raw_df = pd.DataFrame({"smiles": ["invalid"], "yield": [None]})
    cleaned_df = pd.DataFrame(columns=["smiles", "yield", "ecfp4", "maccs"])
    exclusion_counts = {
        "INVALID_SMILES": 1,
        "MISSING_YIELD": 0,
        "INVALID_YIELD": 0,
        "SALT_REMOVAL_FAILED": 0,
        "FINGERPRINT_GENERATION_FAILED": 0,
        "EMPTY_REACTION": 0,
    }

    report = calculate_data_quality_metrics(
        raw_df, cleaned_df, exclusion_counts, 5.0
    )

    assert report["dataset_sizes"]["cleaned_records"] == 0
    assert report["dataset_sizes"]["exclusion_rate_percent"] == 100.0
    assert report["yield_statistics"] == {}

def test_calculate_data_quality_metrics_fingerprint_stats():
    """Test fingerprint dimension statistics."""
    raw_df = pd.DataFrame({"smiles": ["CCO"], "yield": [80.0]})
    cleaned_df = pd.DataFrame({
        "smiles": ["CCO"],
        "yield": [80.0],
        "ecfp4": [[1] * 2048],
        "maccs": [[1] * 167],
    })
    exclusion_counts = {
        "INVALID_SMILES": 0,
        "MISSING_YIELD": 0,
        "INVALID_YIELD": 0,
        "SALT_REMOVAL_FAILED": 0,
        "FINGERPRINT_GENERATION_FAILED": 0,
        "EMPTY_REACTION": 0,
    }

    report = calculate_data_quality_metrics(
        raw_df, cleaned_df, exclusion_counts, 1.0
    )

    assert report["fingerprint_statistics"]["ecfp4"]["dimension"] == 2048
    assert report["fingerprint_statistics"]["maccs"]["dimension"] == 167
