import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path to allow imports if run from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.exclusion_logic import apply_exclusion_logic, write_exclusion_report

class TestExclusionLogic:
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe with various edge cases."""
        data = {
            'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'],
            'age': [45.0, 60.0, np.nan, 30.0, 55.0, np.nan, 70.0],
            'haplogroup': ['H1', 'J2', 'UNK', 'T2', np.nan, 'H5', 'U5'],
            'burden': [0.01, 0.02, 0.015, 0.005, 0.03, 0.01, 0.025],
            'sex': ['M', 'F', 'M', 'F', 'M', 'F', 'M']
        }
        return pd.DataFrame(data)

    def test_missing_age_exclusion(self, sample_df):
        """Test that samples with missing age are excluded from ALL analysis."""
        full_df, haplo_df, stats = apply_exclusion_logic(sample_df)
        
        # Check that S3 and S6 (missing age) are NOT in full_df
        assert 'S3' not in full_df['sample_id'].values
        assert 'S6' not in full_df['sample_id'].values
        
        # Check counts
        assert stats['missing_age_count'] == 2
        assert stats['total_samples'] == 7
        assert stats['full_analysis_count'] == 5  # 7 - 2 missing age

    def test_failed_haplogroup_exclusion(self, sample_df):
        """Test that samples with failed haplogroup are excluded from haplo-specific analysis only."""
        full_df, haplo_df, stats = apply_exclusion_logic(sample_df)
        
        # S3 has missing age -> excluded from both (checked above)
        # S4 has age (30.0) but failed haplogroup (UNK)
        # S5 has age (55.0) but failed haplogroup (NaN)
        
        # S4 and S5 should be in full_df
        assert 'S4' in full_df['sample_id'].values
        assert 'S5' in full_df['sample_id'].values
        
        # S4 and S5 should NOT be in haplo_df
        assert 'S4' not in haplo_df['sample_id'].values
        assert 'S5' not in haplo_df['sample_id'].values
        
        # Check counts
        assert stats['failed_haplogroup_count'] == 2
        # Total with age: 5 (S1, S2, S4, S5, S7)
        # Failed haplo among those with age: 2 (S4, S5)
        # Haplo count should be 5 - 2 = 3
        assert stats['haplogroup_analysis_count'] == 3

    def test_retention_logic(self, sample_df):
        """Test that samples are correctly retained for burden-only analysis."""
        full_df, haplo_df, stats = apply_exclusion_logic(sample_df)
        
        # Retained for burden-only = full_df count - haplo_df count
        expected_retained = stats['full_analysis_count'] - stats['haplogroup_analysis_count']
        assert stats['retained_for_burden_only'] == expected_retained
        
        # Specifically, S4 and S5 are retained in full but not haplo
        assert expected_retained == 2

    def test_write_exclusion_report(self, sample_df, tmp_path):
        """Test that the exclusion report is written correctly."""
        full_df, haplo_df, stats = apply_exclusion_logic(sample_df)
        
        report_path = tmp_path / 'exclusion_report.txt'
        write_exclusion_report(stats, report_path)
        
        assert report_path.exists()
        
        content = report_path.read_text()
        
        # Verify key content
        assert 'Total Samples Input' in content
        assert 'Missing Age' in content
        assert 'Failed Haplogroup Assignment' in content
        assert 'Full Analysis' in content
        assert 'Haplogroup-Specific Analysis' in content
        assert str(stats['missing_age_count']) in content
        assert str(stats['failed_haplogroup_count']) in content

    def test_empty_dataframe(self):
        """Test behavior with an empty dataframe."""
        df = pd.DataFrame(columns=['sample_id', 'age', 'haplogroup', 'burden', 'sex'])
        
        full_df, haplo_df, stats = apply_exclusion_logic(df)
        
        assert len(full_df) == 0
        assert len(haplo_df) == 0
        assert stats['total_samples'] == 0
        assert stats['missing_age_count'] == 0
        assert stats['failed_haplogroup_count'] == 0

    def test_all_missing_age(self):
        """Test behavior when all samples have missing age."""
        data = {
            'sample_id': ['S1', 'S2'],
            'age': [np.nan, np.nan],
            'haplogroup': ['H1', 'J2'],
            'burden': [0.01, 0.02],
            'sex': ['M', 'F']
        }
        df = pd.DataFrame(data)
        
        full_df, haplo_df, stats = apply_exclusion_logic(df)
        
        assert len(full_df) == 0
        assert len(haplo_df) == 0
        assert stats['missing_age_count'] == 2
        assert stats['failed_haplogroup_count'] == 0 # No failed haplo among those with age (since none have age)

    def test_all_failed_haplogroup(self):
        """Test behavior when all samples have failed haplogroup but valid age."""
        data = {
            'sample_id': ['S1', 'S2'],
            'age': [45.0, 60.0],
            'haplogroup': ['UNK', np.nan],
            'burden': [0.01, 0.02],
            'sex': ['M', 'F']
        }
        df = pd.DataFrame(data)
        
        full_df, haplo_df, stats = apply_exclusion_logic(df)
        
        assert len(full_df) == 2
        assert len(haplo_df) == 0
        assert stats['missing_age_count'] == 0
        assert stats['failed_haplogroup_count'] == 2
        assert stats['retained_for_burden_only'] == 2