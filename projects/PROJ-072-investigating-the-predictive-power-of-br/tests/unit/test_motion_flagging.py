"""
Unit tests for the motion flagging module.
"""
import os
import sys
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from preprocessing.motion_flagging import (
    calculate_max_displacement,
    flag_subject_motion,
    MOTION_THRESHOLD_MM,
    DATA_RAW_DIR,
    DATA_METADATA_DIR
)


class TestCalculateMaxDisplacement:
    def test_no_motion(self):
        """Test with zero motion parameters."""
        params = np.zeros((10, 6))
        assert calculate_max_displacement(params) == 0.0

    def test_small_motion(self):
        """Test with motion below threshold."""
        # 1.5mm max translation
        params = np.zeros((10, 6))
        params[0, 0] = 1.5
        assert calculate_max_displacement(params) == 1.5

    def test_large_motion(self):
        """Test with motion above threshold."""
        # 2.5mm max translation
        params = np.zeros((10, 6))
        params[5, 1] = -2.5
        assert calculate_max_displacement(params) == 2.5

    def test_rotation_ignored(self):
        """Test that rotation values do not affect translation displacement."""
        params = np.zeros((10, 6))
        # High rotation but low translation
        params[0, 3] = 10.0 # rad
        assert calculate_max_displacement(params) == 0.0


class TestFlagSubjectMotion:
    @pytest.fixture(autouse=True)
    def setup_test_env(self, tmp_path):
        """Setup temporary directory structure mimicking project layout."""
        self.tmp_raw = tmp_path / "data" / "raw" / "ds000030"
        self.tmp_raw.mkdir(parents=True)
        self.tmp_meta = tmp_path / "data" / "metadata"
        self.tmp_meta.mkdir(parents=True)

        # Mock the global paths
        import preprocessing.motion_flagging as mf_module
        self.original_raw = mf_module.DATA_RAW_DIR
        self.original_meta = mf_module.DATA_METADATA_DIR
        mf_module.DATA_RAW_DIR = self.tmp_raw
        mf_module.DATA_METADATA_DIR = self.tmp_meta

        yield

        # Restore
        mf_module.DATA_RAW_DIR = self.original_raw
        mf_module.DATA_METADATA_DIR = self.original_meta

    def create_motion_file(self, subject_id: str, params: np.ndarray):
        """Helper to create a mock motion file."""
        sub_dir = self.tmp_raw / subject_id
        sub_dir.mkdir(exist_ok=True)
        file_path = sub_dir / f"{subject_id}_motion_params.tsv"
        pd.DataFrame(params).to_csv(file_path, sep='\t', header=False)
        return file_path

    def test_subject_included(self, setup_test_env):
        """Test a subject with motion below threshold is included."""
        sub_id = "sub-01"
        params = np.random.rand(100, 6) * 1.0 # Max ~1mm
        self.create_motion_file(sub_id, params)

        result = flag_subject_motion(sub_id)
        assert result['excluded'] is False
        assert result['reason'] == ""
        assert result['max_displacement'] <= MOTION_THRESHOLD_MM

    def test_subject_excluded(self, setup_test_env):
        """Test a subject with motion above threshold is excluded."""
        sub_id = "sub-02"
        params = np.zeros((100, 6))
        params[50, 0] = 3.0 # 3mm translation
        self.create_motion_file(sub_id, params)

        result = flag_subject_motion(sub_id)
        assert result['excluded'] is True
        assert "excessive_motion" in result['reason']
        assert result['max_displacement'] == 3.0

    def test_missing_motion_file(self, setup_test_env):
        """Test behavior when motion file is missing."""
        sub_id = "sub-03"
        # Do not create file
        result = flag_subject_motion(sub_id)
        assert result['excluded'] is True
        assert result['reason'] == 'missing_motion_data'
        assert np.isnan(result['max_displacement'])
