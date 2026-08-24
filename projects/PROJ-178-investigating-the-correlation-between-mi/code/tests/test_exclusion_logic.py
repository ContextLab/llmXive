import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.exclusion_logic import apply_exclusion_logic, write_exclusion_report

class TestExclusionLogic:
    """
    Tests for T019: Conditional exclusion logic.
    """

    def setup_method(self):
        """Create a temporary directory and mock dataset for testing."""
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock dataset with various missing scenarios
        self.mock_data = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            'age': [25.0, np.nan, 40.0, 50.0, np.nan, 30.0], # S2, S5 missing age
            'haplogroup': ['H1', 'J1', np.nan, 'U5', 'T2', ''], # S3 missing, S6 empty
            'burden': [0.01, 0.02, 0.015, 0.025, 0.03, 0.012]
        })

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_exclusion_missing_age_removal(self):
        """
        Verify that samples with missing age are removed from the full analysis set.
        """
        full_df, hg_df, stats = apply_exclusion_logic(self.mock_data)
        
        # S2 and S5 should be excluded
        assert len(full_df) == 4, f"Expected 4 rows, got {len(full_df)}"
        assert 'S2' not in full_df['sample_id'].values
        assert 'S5' not in full_df['sample_id'].values
        assert stats['excluded_missing_age'] == 2
        assert stats['retained_for_full_analysis'] == 4

    def test_exclusion_missing_haplogroup_removal(self):
        """
        Verify that samples with missing haplogroup are removed from the HG analysis set,
        but retained in the full analysis set (if age is present).
        """
        full_df, hg_df, stats = apply_exclusion_logic(self.mock_data)
        
        # Full set: S3 (missing HG) should be present
        assert 'S3' in full_df['sample_id'].values
        
        # HG set: S3 (missing HG) and S6 (empty HG) should be excluded
        assert 'S3' not in hg_df['sample_id'].values
        assert 'S6' not in hg_df['sample_id'].values
        assert len(hg_df) == 3, f"Expected 3 rows in HG set, got {len(hg_df)}"
        
        # Check stats
        # Total 6. Missing age 2. Missing HG (but valid age) 2 (S3, S6)
        assert stats['excluded_missing_hg_count'] == 2
        assert stats['retained_for_haplogroup_analysis'] == 3

    def test_write_exclusion_report(self):
        """
        Verify that the exclusion report file is created and contains expected content.
        """
        _, _, stats = apply_exclusion_logic(self.mock_data)
        report_path = Path(self.temp_dir) / 'exclusion_report.txt'
        
        write_exclusion_report(stats, report_path)
        
        assert report_path.exists(), "Exclusion report file was not created."
        
        content = report_path.read_text()
        assert "EXCLUSION REPORT" in content
        assert "Total Samples" in content
        assert "Excluded (Missing Age)" in content
        assert "Retained" in content

    def test_empty_dataframe(self):
        """
        Test behavior with an empty dataframe.
        """
        empty_df = pd.DataFrame(columns=['sample_id', 'age', 'haplogroup', 'burden'])
        full_df, hg_df, stats = apply_exclusion_logic(empty_df)
        
        assert len(full_df) == 0
        assert len(hg_df) == 0
        assert stats['total_samples_initial'] == 0
        assert stats['excluded_missing_age'] == 0

    def test_no_missing_values(self):
        """
        Test behavior when no values are missing.
        """
        clean_df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'age': [25.0, 30.0],
            'haplogroup': ['H1', 'J1'],
            'burden': [0.01, 0.02]
        })
        full_df, hg_df, stats = apply_exclusion_logic(clean_df)
        
        assert len(full_df) == 2
        assert len(hg_df) == 2
        assert stats['excluded_missing_age'] == 0
        assert stats['excluded_missing_hg_count'] == 0
        assert stats['retained_for_full_analysis'] == 2
        assert stats['retained_for_haplogroup_analysis'] == 2