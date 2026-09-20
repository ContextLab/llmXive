"""
Unit tests for T035a: P/N Availability Rate calculation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in os.sys.path:
    os.sys.path.insert(0, str(code_dir))

from pn_availability_calculator import calculate_pn_availability_rate, load_json_file, save_json_file


@pytest.fixture
def mock_config(tmp_path):
    """Create a temporary directory structure for config."""
    artifacts_dir = tmp_path / "artifacts"
    reports_dir = artifacts_dir / "reports"
    reports_dir.mkdir(parents=True)
    
    # Create mock sc_amendments.json
    amendments = {
        "AM-001": {
            "id": "AM-001",
            "description": "Redefinition of SC-001 due to ISRIC exclusion"
        }
    }
    with open(artifacts_dir / "sc_amendments.json", 'w') as f:
        json.dump(amendments, f)

    # Create mock species_counts.json (T015e output)
    counts = {
        "total_species_input": 50,
        "excluded_species_count": 10,
        "excluded_species_list": ["Species A", "Species B"],
        "rows_excluded_by_source": 100,
        "rows_excluded_by_missing_nutrients": 50,
        "rows_excluded_by_sample_size": 20
    }
    with open(reports_dir / "species_counts.json", 'w') as f:
        json.dump(counts, f)

    return {
        "ARTIFACTS_DIR": str(artifacts_dir)
    }


@pytest.fixture
def mock_processed_data():
    """Mock a DataFrame with 100 rows (all having P/N)."""
    mock_df = MagicMock()
    mock_df.__len__ = lambda self: 100
    return mock_df


def test_calculate_pn_availability_rate(mock_config, mock_processed_data):
    """Test the calculation logic."""
    logger = MagicMock()
    
    # Mock the load_processed_data function
    with patch('pn_availability_calculator.load_processed_data', return_value=mock_processed_data):
        with patch('pn_availability_calculator.get_config', return_value=mock_config):
            result = calculate_pn_availability_rate(logger)
    
    # Numerator = 100
    # Exclusions = 100 + 50 + 20 = 170
    # Denominator = 100 + 170 = 270
    # Rate = 100 / 270
    expected_rate = 100 / 270
    
    assert 'pn_availability_rate' in result
    assert abs(result['pn_availability_rate'] - expected_rate) < 1e-6
    assert result['original_sc001_metric'] == "merge_success_rate (unavailable due to scope deviation)"
    assert result['amendment_reference'] == "AM-001"
    
    # Verify logger calls
    logger.info.assert_called()