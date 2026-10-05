"""
Integration tests for the filtering module (T011).

These tests verify that the filtering logic correctly produces
the expected output file and content.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path if not already
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.data.filtering import filter_cohort, main
from code.src.utils.config import get_processed_data_dir


@pytest.fixture
def sample_mixed_cohort():
    """Create a sample dataset with mixed ages and missing values."""
    data = {
        'participant_id': [f'P{i:03d}' for i in range(10)],
        'age': [60, 65, 70, 75, 80, 64, 65, 70, 75, 80],
        'sex': ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F'],
        'bmi': [24.5, 26.0, 22.1, 28.3, 25.0, np.nan, 24.0, 27.0, 23.5, 26.5],
        'cognitive_flexibility_score': [85.0, 88.0, 90.0, 82.0, 87.0, 86.0, np.nan, 89.0, 84.0, 91.0],
        'shannon_diversity': [3.5, 3.8, 4.0, 3.2, 3.7, 3.6, 3.9, 3.4, 3.3, 4.1],
        'dietary_fiber_intake': [25.0, 30.0, 28.0, 22.0, 32.0, 27.0, 29.0, 26.0, 24.0, 31.0],
        'antibiotic_use_history': [False, True, False, True, False, True, False, True, False, True]
    }
    return pd.DataFrame(data)


def test_filter_cohort_integration(sample_mixed_cohort, tmp_path):
    """
    Test that filter_cohort correctly filters by age >= 65 and non-null metrics,
    and listwise deletes missing covariates.
    """
    # Arrange
    # Expected:
    # P001 (65), P002 (70), P003 (75), P004 (80) -> All valid initially
    # P005 (64) -> Dropped (age < 65)
    # P006 (65) -> Dropped (bmi null)
    # P007 (70) -> Dropped (cognitive null)
    # P008 (75) -> Valid
    # P009 (80) -> Valid
    # P000 (60) -> Dropped (age < 65)

    # Filter
    filtered_df, dropped_count = filter_cohort(sample_mixed_cohort, min_age=65)

    # Assert
    assert len(filtered_df) == 5, f"Expected 5 rows, got {len(filtered_df)}"
    assert dropped_count == 5, f"Expected 5 dropped rows, got {dropped_count}"

    # Check ages are all >= 65
    assert all(filtered_df['age'] >= 65), "Some rows have age < 65"

    # Check no nulls in required fields
    required_fields = ['age', 'sex', 'bmi', 'cognitive_flexibility_score', 'shannon_diversity', 'dietary_fiber_intake', 'antibiotic_use_history']
    for field in required_fields:
        assert not filtered_df[field].isnull().any(), f"Null values found in {field}"

    # Check specific IDs
    expected_ids = ['P001', 'P002', 'P003', 'P004', 'P008', 'P009'] # Wait, let's re-calculate
    # P000: 60 (drop)
    # P001: 65, bmi 26, cog 88, shan 3.8 -> Keep
    # P002: 70, bmi 22.1, cog 90, shan 4.0 -> Keep
    # P003: 75, bmi 28.3, cog 82, shan 3.2 -> Keep
    # P004: 80, bmi 25.0, cog 87, shan 3.7 -> Keep
    # P005: 64 (drop)
    # P006: 65, bmi nan -> Drop
    # P007: 70, cog nan -> Drop
    # P008: 75, bmi 27, cog 89, shan 3.4 -> Keep
    # P009: 80, bmi 26.5, cog 91, shan 4.1 -> Keep
    # Total keep: P001, P002, P003, P004, P008, P009 -> 6 rows?
    # Let's re-read the data:
    # P000: 60
    # P001: 65
    # P002: 70
    # P003: 75
    # P004: 80
    # P005: 64
    # P006: 65 (bmi nan)
    # P007: 70 (cog nan)
    # P008: 75
    # P009: 80
    # Total 10.
    # Drop age < 65: P000, P005 (2 rows). Remaining 8.
    # Drop null bmi: P006 (1 row). Remaining 7.
    # Drop null cog: P007 (1 row). Remaining 6.
    # So 6 rows should remain.

    assert len(filtered_df) == 6, f"Expected 6 rows after filtering, got {len(filtered_df)}"
    assert list(filtered_df['participant_id']) == ['P001', 'P002', 'P003', 'P004', 'P008', 'P009']


def test_main_writes_output_file(sample_mixed_cohort, tmp_path):
    """
    Test that the main() function writes the filtered cohort to the correct file path.
    """
    # Mock the config paths to use tmp_path
    from unittest.mock import patch, MagicMock
    from code.src.utils import config as config_module

    # Create a temporary directory structure
    raw_dir = tmp_path / 'data' / 'raw'
    proc_dir = tmp_path / 'data' / 'processed'
    logs_dir = tmp_path / 'logs'
    raw_dir.mkdir(parents=True)
    proc_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    # Save input data
    input_file = raw_dir / 'merged_cohort.csv'
    sample_mixed_cohort.to_csv(input_file, index=False)

    # Patch config functions
    with patch.object(config_module, 'get_project_root', return_value=tmp_path), \
         patch.object(config_module, 'get_processed_data_dir', return_value=proc_dir), \
         patch.object(config_module, 'get_logs_dir', return_value=logs_dir), \
         patch.object(config_module, 'ensure_directories'):

        # Run main
        result_df = main()

        # Assert output file exists
        output_file = proc_dir / 'filtered_cohort.csv'
        assert output_file.exists(), f"Output file {output_file} was not created."

        # Assert content matches
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == 6, f"Saved file has wrong number of rows: {len(saved_df)}"
        assert list(saved_df['participant_id']) == ['P001', 'P002', 'P003', 'P004', 'P008', 'P009']

        # Assert return value
        assert len(result_df) == 6