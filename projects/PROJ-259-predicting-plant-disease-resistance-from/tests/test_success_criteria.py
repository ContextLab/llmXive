"""
Unit tests for success_criteria_check module (T028b)

Tests verify:
1. Loading selection frequency data
2. Identifying significant features at thresholds
3. Computing intersection across thresholds
4. Categorizing features into SNPs and metabolites
5. Success criteria evaluation (>=10 each)
6. Report generation
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from analysis.success_criteria_check import (
    load_selection_frequency,
    get_significant_features,
    categorize_features,
    check_success_criteria,
    write_success_report
)


@pytest.fixture
def sample_selection_df():
    """Create a sample selection frequency DataFrame for testing."""
    # Create data with features at 3 thresholds
    data = {
        'feature_id': [
            # Features selected at all 3 thresholds (intersection)
            'snp_001', 'snp_002', 'snp_003', 'snp_004', 'snp_005',
            'snp_006', 'snp_007', 'snp_008', 'snp_009', 'snp_010',
            'snp_011', 'snp_012',
            'met_001', 'met_002', 'met_003', 'met_004', 'met_005',
            'met_006', 'met_007', 'met_008', 'met_009', 'met_010',
            'met_011', 'met_012',
            # Features selected at only some thresholds (not in intersection)
            'snp_013', 'snp_014',
            'met_013', 'met_014',
        ],
        'threshold': [
            # All intersection features at threshold 0.01
            0.01, 0.01, 0.01, 0.01, 0.01,
            0.01, 0.01, 0.01, 0.01, 0.01,
            0.01, 0.01,
            0.01, 0.01, 0.01, 0.01, 0.01,
            0.01, 0.01, 0.01, 0.01, 0.01,
            0.01, 0.01,
            0.01, 0.01,
            # ... at 0.05
            0.05, 0.05,
            0.05, 0.05,
            # ... at 0.1
            0.1, 0.1,
            0.1, 0.1,
        ] * 2,  # Duplicate to simulate frequency > 0
        'frequency': [
            1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
        ]
    }
    return pd.DataFrame(data)


def test_get_significant_features(sample_selection_df):
    """Test extraction of significant features at a threshold."""
    # At threshold 0.01, we expect all 28 features (12 snps + 12 mets + 4 partial)
    sig_features = get_significant_features(sample_selection_df, 0.01)
    assert len(sig_features) == 28
    assert 'snp_001' in sig_features
    assert 'met_001' in sig_features
    assert 'snp_013' in sig_features  # Only at 0.01

    # At threshold 0.05, only the partial features should be there
    sig_features_05 = get_significant_features(sample_selection_df, 0.05)
    assert len(sig_features_05) == 4
    assert 'snp_013' in sig_features_05
    assert 'snp_001' not in sig_features_05  # Not at 0.05


def test_categorize_features():
    """Test categorization of features into SNPs and metabolites."""
    features = {
        'snp_001', 'snp_002', 'snp_003',
        'met_001', 'met_002',
        'unknown_001'  # Should be logged but not fail
    }

    snps, metabolites = categorize_features(features)

    assert snps == {'snp_001', 'snp_002', 'snp_003'}
    assert metabolites == {'met_001', 'met_002'}
    assert 'unknown_001' not in snps
    assert 'unknown_001' not in metabolites


def test_check_success_criteria_pass():
    """Test success criteria when counts meet requirement."""
    is_success, msg = check_success_criteria(snp_count=12, metabolite_count=12)
    assert is_success is True
    assert 'PASSED' in msg


def test_check_success_criteria_fail_snp():
    """Test success criteria when SNP count is insufficient."""
    is_success, msg = check_success_criteria(snp_count=5, metabolite_count=12)
    assert is_success is False
    assert 'FAILED' in msg


def test_check_success_criteria_fail_both():
    """Test success criteria when both counts are insufficient."""
    is_success, msg = check_success_criteria(snp_count=5, metabolite_count=5)
    assert is_success is False
    assert 'FAILED' in msg


def test_write_success_report(tmp_path):
    """Test writing the success criteria report."""
    output_file = tmp_path / "test_success.json"

    write_success_report(
        is_success=True,
        status_message="Test message",
        snp_count=12,
        metabolite_count=12,
        total_intersection=24,
        output_path=str(output_file)
    )

    assert output_file.exists()

    with open(output_file, 'r') as f:
        report = json.load(f)

    assert report['success_status'] == 'PASSED'
    assert report['criteria'] == 'SC-002'
    assert report['details']['snp_count'] == 12
    assert report['details']['metabolite_count'] == 12
    assert report['details']['total_intersection'] == 24
    assert 'timestamp' in report