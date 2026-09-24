"""
Unit Tests for Task T013: Alignment
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the functions to test
# We assume the code is in code/alignment.py relative to project root
# Since we are running tests, we need to ensure the path is correct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from alignment import align_and_filter_data, save_aligned_data, save_exclusions_log, load_raw_data

class TestAlignment:
    def setup_method(self):
        """Setup test data"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = Path(self.temp_dir) / "raw_data.parquet"
        
        # Create a mock dataframe
        data = {
            "image_path": ["img1", "img2", "img3", "img4", "img5"],
            "species_id": [1, 2, 3, 4, 5],
            "teacher_scores": [
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
                [0.9, 0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6, 0.7],
                [0.8, 0.9, 0.1, 0.2]
            ],
            "student_scalar": [0.2, np.nan, 0.4, 0.5, 0.6], # img2 missing
            "human_annotations": [
                [0.15, 0.25, 0.35, 0.45],
                [0.55, 0.65, 0.75, 0.85],
                [0.95, 0.15, 0.25, 0.35],
                [0.45, 0.55, 0.65, 0.75],
                [0.85, 0.95, 0.15, 0.25]
            ]
        }
        self.df = pd.DataFrame(data)
        self.df.to_parquet(self.test_data_path)

    def teardown_method(self):
        """Cleanup temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_align_removes_missing_student_scalar(self):
        """Test that samples missing student_scalar are excluded"""
        # Mock a logger object
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass

        logger = MockLogger()
        
        aligned_df, exclusions = align_and_filter_data(self.df, logger)
        
        # Should have 4 valid samples (img2 excluded)
        assert len(aligned_df) == 4
        assert len(exclusions) == 1
        
        # Check the excluded sample
        assert exclusions[0]["excluded_reason"] == "missing_student_scalar"
        assert "img2" in exclusions[0]["sample_id"]
        
        # Check that img2 is not in the aligned dataframe
        assert "img2" not in aligned_df["image_path"].values

    def test_align_keeps_valid_samples(self):
        """Test that valid samples are kept"""
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass

        logger = MockLogger()
        
        aligned_df, exclusions = align_and_filter_data(self.df, logger)
        
        # Check that valid samples are present
        assert "img1" in aligned_df["image_path"].values
        assert "img3" in aligned_df["image_path"].values
        assert "img4" in aligned_df["image_path"].values
        assert "img5" in aligned_df["image_path"].values

    def test_align_missing_teacher_scores(self):
        """Test exclusion when teacher_scores are missing"""
        # Modify dataframe to have missing teacher_scores
        df_missing = self.df.copy()
        df_missing.loc[df_missing["image_path"] == "img3", "teacher_scores"] = np.nan
        
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass

        logger = MockLogger()
        
        aligned_df, exclusions = align_and_filter_data(df_missing, logger)
        
        # img2 (missing student_scalar) and img3 (missing teacher_scores) should be excluded
        assert len(exclusions) == 2
        reasons = [e["excluded_reason"] for e in exclusions]
        assert "missing_student_scalar" in reasons
        assert "missing_teacher_scores" in reasons

    def test_align_missing_human_annotations(self):
        """Test exclusion when human_annotations are missing"""
        df_missing = self.df.copy()
        df_missing.loc[df_missing["image_path"] == "img4", "human_annotations"] = np.nan
        
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass

        logger = MockLogger()
        
        aligned_df, exclusions = align_and_filter_data(df_missing, logger)
        
        assert len(exclusions) == 2
        reasons = [e["excluded_reason"] for e in exclusions]
        assert "missing_student_scalar" in reasons
        assert "missing_human_annotations" in reasons

    def test_save_exclusions_log_creates_file(self):
        """Test that exclusions log is written correctly"""
        exclusions = [
            {"sample_id": "img2", "excluded_reason": "missing_student_scalar", "index": 1}
        ]
        output_path = Path(self.temp_dir) / "exclusions.json"
        
        class MockLogger:
            def info(self, msg): pass
            def error(self, msg): pass
            def warning(self, msg): pass

        logger = MockLogger()
        save_exclusions_log(exclusions, output_path, logger)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["sample_id"] == "img2"
        assert data[0]["excluded_reason"] == "missing_student_scalar"
