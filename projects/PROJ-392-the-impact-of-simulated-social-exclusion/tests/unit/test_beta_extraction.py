"""
Unit tests for beta extraction functionality.

These tests verify the beta extraction logic without requiring
actual fMRI data, using mocked results.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.beta_extraction import (
    extract_beta_from_results,
    load_first_level_results,
    BetaExtractionError
)
from config.loader import get_config

def test_extract_beta_from_results_existing_contrast():
    """Test extraction when contrast exists in results."""
    mock_results = {
        'contrasts': {
            'reward_anticipation_vs_baseline_ventral_striatum': {
                'beta_estimate': 0.45,
                't_stat': 2.3,
                'p_value': 0.02
            }
        }
    }

    beta = extract_beta_from_results(
        mock_results,
        'reward_anticipation_vs_baseline_ventral_striatum',
        'reward_anticipation'
    )

    assert beta == 0.45

def test_extract_beta_from_results_alternative_format():
    """Test extraction when contrast uses alternative format."""
    mock_results = {
        'contrasts': {
            'reward_receipt_vs_baseline_oFC': {
                'estimate': 0.32,
                't_stat': 1.8,
                'p_value': 0.07
            }
        }
    }

    beta = extract_beta_from_results(
        mock_results,
        'reward_receipt_vs_baseline_oFC',
        'reward_receipt'
    )

    assert beta == 0.32

def test_extract_beta_from_results_missing_contrast():
    """Test extraction when contrast doesn't exist."""
    mock_results = {
        'contrasts': {
            'other_contrast': {
                'beta_estimate': 0.1
            }
        }
    }

    beta = extract_beta_from_results(
        mock_results,
        'nonexistent_contrast',
        'reward_anticipation'
    )

    assert beta is None

def test_extract_beta_from_results_no_contrasts():
    """Test extraction when no contrasts exist."""
    mock_results = {}

    beta = extract_beta_from_results(
        mock_results,
        'any_contrast',
        'reward_anticipation'
    )

    assert beta is None

def test_load_first_level_results_missing_file():
    """Test loading results when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a path that doesn't exist
        fake_path = Path(tmpdir) / 'nonexistent' / 'results_summary.json'

        # Mock the config to return our temp directory
        with patch('analysis.beta_extraction.get_path') as mock_get_path:
            mock_get_path.return_value = tmpdir

            result = load_first_level_results('sub-001', 'ds004738', {})
            assert result is None

def test_load_first_level_results_invalid_json():
    """Test loading results with invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        results_dir = Path(tmpdir) / 'ds004738' / 'first_level_results' / 'sub-001'
        results_dir.mkdir(parents=True)

        # Create invalid JSON file
        results_file = results_dir / 'results_summary.json'
        results_file.write_text('{ invalid json }')

        with patch('analysis.beta_extraction.get_path') as mock_get_path:
            mock_get_path.return_value = tmpdir

            try:
                result = load_first_level_results('sub-001', 'ds004738', {})
                assert False, "Should have raised BetaExtractionError"
            except BetaExtractionError:
                pass  # Expected

def test_extract_beta_from_results_parameter_fallback():
    """Test extraction using parameters fallback."""
    mock_results = {
        'contrasts': {
            'test_contrast': {
                'parameters': [0.75, 0.12, 0.05]
            }
        }
    }

    beta = extract_beta_from_results(
        mock_results,
        'test_contrast',
        'test_event'
    )

    assert beta == 0.75

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])