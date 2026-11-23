import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import nibabel as nib
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import process_qc_and_exclude, get_motion_file
from utils import calculate_frame_displacement, check_motion_threshold

class TestMotionQCExtraction:
    """
    Integration tests for motion QC extraction logic in preprocess.py.
    Tests parsing of fmriprep confounds and threshold flagging.
    """

    def setup_method(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "derivatives"
        self.sub_dir = self.output_dir / "sub-01" / "func"
        self.sub_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def _create_mock_confounds(self, displacement_values: list):
        """
        Create a mock fmriprep confounds TSV file.
        fmriprep confounds usually contain columns: trans_x, trans_y, trans_z, 
        rot_x, rot_y, rot_z, etc.
        """
        n_volumes = len(displacement_values)
        
        # Create mock data
        data = {
            'trans_x': displacement_values,
            'trans_y': [0.0] * n_volumes,
            'trans_z': [0.0] * n_volumes,
            'rot_x': [0.0] * n_volumes,
            'rot_y': [0.0] * n_volumes,
            'rot_z': [0.0] * n_volumes,
            'csf': [0.0] * n_volumes,
            'wm': [0.0] * n_volumes,
        }
        
        df = pd.DataFrame(data)
        confound_file = self.sub_dir / "sub-01_task-motor_desc-confounds_timeseries.tsv"
        df.to_csv(confound_file, sep='\t', index=False)
        return confound_file

    def test_motion_below_threshold(self):
        """Test that a subject with low motion passes QC."""
        # Create data with max displacement ~1.5mm (below 2.0mm threshold)
        displacements = [1.0, 1.2, 1.5, 0.5, 0.2]
        confound_file = self._create_mock_confounds(displacements)
        
        # Run QC check
        result = process_qc_and_exclude(
            subject_id="01",
            output_dir=self.output_dir,
            motion_threshold=2.0
        )
        
        assert result is True, "Subject with low motion should pass QC"

    def test_motion_above_threshold(self):
        """Test that a subject with high motion fails QC."""
        # Create data with max displacement ~2.5mm (above 2.0mm threshold)
        displacements = [1.0, 1.5, 2.5, 0.5, 0.2]
        confound_file = self._create_mock_confounds(displacements)
        
        # Run QC check
        result = process_qc_and_exclude(
            subject_id="01",
            output_dir=self.output_dir,
            motion_threshold=2.0
        )
        
        assert result is False, "Subject with high motion should fail QC"

    def test_motion_exactly_at_threshold(self):
        """Test behavior when motion is exactly at the threshold."""
        # Create data with max displacement exactly 2.0mm
        displacements = [1.0, 1.5, 2.0, 0.5, 0.2]
        confound_file = self._create_mock_confounds(displacements)
        
        # Run QC check
        # check_motion_threshold logic: displacement <= threshold -> True
        result = process_qc_and_exclude(
            subject_id="01",
            output_dir=self.output_dir,
            motion_threshold=2.0
        )
        
        # Should pass if <= threshold
        assert result is True, "Subject with motion exactly at threshold should pass"

    def test_missing_confounds_file(self):
        """Test behavior when confounds file is missing."""
        # Do not create confounds file
        result = process_qc_and_exclude(
            subject_id="01",
            output_dir=self.output_dir,
            motion_threshold=2.0
        )
        
        # Current implementation assumes pass if file missing (conservative)
        assert result is True, "Missing confounds file should not crash (assumes pass)"

    def test_frame_displacement_calculation(self):
        """Test the underlying frame displacement calculation."""
        displacements = [0.0, 1.0, 2.0, 0.5]
        self._create_mock_confounds(displacements)
        
        confound_file = self.sub_dir / "sub-01_task-motor_desc-confounds_timeseries.tsv"
        max_disp = calculate_frame_displacement(confound_file)
        
        # Verify calculation: max of [0, 1, 2, 0.5] is 2.0
        # Note: Actual calculation involves sqrt of sum of squares of translations + rotations
        # Since rotations are 0, it should be close to max translation
        assert max_disp is not None
        assert abs(max_disp - 2.0) < 0.01, f"Expected ~2.0, got {max_disp}"

    def test_check_motion_threshold_logic(self):
        """Test the threshold check logic directly."""
        assert check_motion_threshold(1.5, 2.0) is True
        assert check_motion_threshold(2.0, 2.0) is True
        assert check_motion_threshold(2.1, 2.0) is False
        assert check_motion_threshold(0.0, 2.0) is True