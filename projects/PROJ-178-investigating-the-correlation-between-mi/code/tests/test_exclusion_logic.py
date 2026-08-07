import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import logging

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from analysis.exclusion_logic import apply_exclusion_logic, write_exclusion_report

class TestExclusionLogic:
    """Test suite for T019 conditional exclusion logic."""

    @pytest.fixture
    def sample_dataset_with_missing_age(self):
        """Create a sample dataset with missing age values."""
        data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [45.0, 62.0, np.nan, 78.0, 55.0],
            'haplogroup': ['H1', 'T2', 'K1', 'Unknown', 'J1'],
            'burden': [0.012, 0.015, 0.008, 0.020, 0.011],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS', 'EUR', 'SAS']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_dataset_with_failed_haplogroup(self):
        """Create a sample dataset with failed haplogroup assignments."""
        data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [45.0, 62.0, 78.0, 55.0, 33.0],
            'haplogroup': ['H1', 'T2', None, 'Unknown', ''],
            'burden': [0.012, 0.015, 0.008, 0.020, 0.011],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS', 'EUR', 'SAS']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_dataset_complete(self):
        """Create a complete sample dataset with no missing values."""
        data = {
            'sample_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
            'age': [45.0, 62.0, 78.0, 55.0, 33.0],
            'haplogroup': ['H1', 'T2', 'K1', 'J1', 'U5'],
            'burden': [0.012, 0.015, 0.008, 0.020, 0.011],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS', 'EUR', 'SAS']
        }
        return pd.DataFrame(data)

    def test_exclude_missing_age_from_all(self, sample_dataset_with_missing_age):
        """Test that samples with missing age are excluded from ALL analysis."""
        df_age_clean, df_haplogroup_specific, report = apply_exclusion_logic(sample_dataset_with_missing_age)
        
        # Check that sample S003 (missing age) is excluded
        assert 'S003' not in df_age_clean['sample_id'].values
        assert 'S003' not in df_haplogroup_specific['sample_id'].values
        
        # Check counts
        assert report['samples_with_missing_age'] == 1
        assert report['samples_after_age_exclusion'] == 4
        assert report['samples_after_haplogroup_exclusion'] == 4  # No haplogroup failures in this test

    def test_exclude_failed_haplogroup_only_from_specific(self, sample_dataset_with_failed_haplogroup):
        """Test that samples with failed haplogroup are excluded from haplogroup-specific only."""
        df_age_clean, df_haplogroup_specific, report = apply_exclusion_logic(sample_dataset_with_failed_haplogroup)
        
        # All samples with age should be in burden-only dataset
        assert len(df_age_clean) == 5  # All have age
        
        # Samples with failed haplogroup (S003, S004, S005) should be excluded from haplogroup-specific
        assert 'S003' not in df_haplogroup_specific['sample_id'].values
        assert 'S004' not in df_haplogroup_specific['sample_id'].values
        assert 'S005' not in df_haplogroup_specific['sample_id'].values
        
        # Valid haplogroup samples should remain
        assert 'S001' in df_haplogroup_specific['sample_id'].values
        assert 'S002' in df_haplogroup_specific['sample_id'].values
        
        # Check counts
        assert report['samples_with_failed_haplogroup'] == 3
        assert report['samples_after_haplogroup_exclusion'] == 2
        assert report['samples_retained_for_burden_only'] == 3

    def test_complete_dataset_no_exclusions(self, sample_dataset_complete):
        """Test that a complete dataset has no exclusions."""
        df_age_clean, df_haplogroup_specific, report = apply_exclusion_logic(sample_dataset_complete)
        
        assert len(df_age_clean) == 5
        assert len(df_haplogroup_specific) == 5
        assert report['samples_with_missing_age'] == 0
        assert report['samples_with_failed_haplogroup'] == 0

    def test_exclusion_report_format(self, sample_dataset_with_missing_age):
        """Test that exclusion report contains required fields."""
        _, _, report = apply_exclusion_logic(sample_dataset_with_missing_age)
        
        required_fields = [
            'initial_samples',
            'samples_with_missing_age',
            'samples_after_age_exclusion',
            'samples_with_failed_haplogroup',
            'samples_after_haplogroup_exclusion',
            'samples_retained_for_burden_only',
            'exclusion_reasons'
        ]
        
        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

    def test_write_exclusion_report(self, sample_dataset_with_missing_age, tmp_path):
        """Test that exclusion report is written correctly to file."""
        df_age_clean, df_haplogroup_specific, report = apply_exclusion_logic(sample_dataset_with_missing_age)
        
        output_path = tmp_path / "exclusion_report.txt"
        write_exclusion_report(report, str(output_path))
        
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "EXCLUSION STATISTICS" in content
        assert "EXCLUSION RULES APPLIED" in content
        assert "missing age" in content.lower()
        assert "failed haplogroup" in content.lower()