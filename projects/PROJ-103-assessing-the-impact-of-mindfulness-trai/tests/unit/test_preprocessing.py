"""
Unit tests for the preprocessing pipeline components.

This module tests the core preprocessing logic including:
- Motion parameter extraction
- Motion filtering/exclusion logic
- Nilearn fallback preprocessing
- QC parsing logic

These tests are designed to fail before implementation (TDD approach).
"""

import os
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import modules under test (will fail if not implemented yet)
from src.preprocessing.extract_motion import extract_motion_parameters
from src.preprocessing.motion_filter import filter_by_motion_threshold
from src.preprocessing.nilearn_fallback import nilearn_preprocess_fallback
from src.preprocessing.qc_parser import parse_fmriprep_qc


class TestMotionParameterExtraction:
    """Tests for motion parameter extraction from fMRIPrep outputs."""

    def test_extract_motion_from_confounds(self):
        """Test extraction of 6 motion parameters from confounds TSV."""
        # Create a mock confounds file
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "sub-01_task-rest_desc-confounds_timeseries.tsv"
            
            # Create minimal confounds data with required columns
            data = {
                'trans_x': [0.1, 0.2, 0.3],
                'trans_y': [0.1, 0.2, 0.3],
                'trans_z': [0.1, 0.2, 0.3],
                'rot_x': [0.01, 0.02, 0.03],
                'rot_y': [0.01, 0.02, 0.03],
                'rot_z': [0.01, 0.02, 0.03],
            }
            df = pd.DataFrame(data)
            df.to_csv(confounds_path, sep='\t', index=False)
            
            # Run extraction
            result = extract_motion_parameters(confounds_path, "sub-01")
            
            # Verify output
            assert isinstance(result, pd.DataFrame)
            assert 'subject_id' in result.columns
            assert 'translation_x' in result.columns
            assert 'translation_y' in result.columns
            assert 'translation_z' in result.columns
            assert 'rotation_x' in result.columns
            assert 'rotation_y' in result.columns
            assert 'rotation_z' in result.columns
            assert len(result) == 3
            assert result['subject_id'].iloc[0] == "sub-01"

    def test_extract_motion_missing_file(self):
        """Test handling of missing confounds file."""
        with pytest.raises(FileNotFoundError):
            extract_motion_parameters("/nonexistent/path.tsv", "sub-01")

    def test_extract_motion_missing_columns(self):
        """Test handling of confounds file missing required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "sub-01_desc-confounds.tsv"
            # Missing required motion columns
            data = {'trans_x': [0.1, 0.2]}
            pd.DataFrame(data).to_csv(confounds_path, sep='\t', index=False)
            
            with pytest.raises(ValueError, match="Missing required motion columns"):
                extract_motion_parameters(confounds_path, "sub-01")


class TestMotionFilter:
    """Tests for motion-based subject exclusion."""

    def test_filter_within_threshold(self):
        """Test that subjects with motion below threshold are kept."""
        motion_data = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'translation_x': [1.0, 2.0],
            'translation_y': [1.0, 2.0],
            'translation_z': [1.0, 2.0],
            'rotation_x': [0.1, 0.2],
            'rotation_y': [0.1, 0.2],
            'rotation_z': [0.1, 0.2],
        })
        
        # Max translation: sub-02 has 2.0mm (sqrt(2^2+2^2+2^2) ≈ 3.46mm)
        # Max rotation: sub-02 has 0.2° (sqrt(0.2^2+0.2^2+0.2^2) ≈ 0.35°)
        # With 3mm/3° threshold, both should be kept
        result = filter_by_motion_threshold(
            motion_data, 
            translation_threshold_mm=3.0, 
            rotation_threshold_deg=3.0
        )
        
        assert len(result) == 2
        assert set(result['subject_id']) == {'sub-01', 'sub-02'}

    def test_filter_exceeds_translation_threshold(self):
        """Test that subjects exceeding translation threshold are excluded."""
        motion_data = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'translation_x': [1.0, 5.0],  # sub-02 exceeds 3mm
            'translation_y': [1.0, 0.0],
            'translation_z': [1.0, 0.0],
            'rotation_x': [0.1, 0.1],
            'rotation_y': [0.1, 0.1],
            'rotation_z': [0.1, 0.1],
        })
        
        result = filter_by_motion_threshold(
            motion_data, 
            translation_threshold_mm=3.0, 
            rotation_threshold_deg=3.0
        )
        
        assert len(result) == 1
        assert result['subject_id'].iloc[0] == 'sub-01'

    def test_filter_exceeds_rotation_threshold(self):
        """Test that subjects exceeding rotation threshold are excluded."""
        motion_data = pd.DataFrame({
            'subject_id': ['sub-01', 'sub-02'],
            'translation_x': [1.0, 1.0],
            'translation_y': [1.0, 1.0],
            'translation_z': [1.0, 1.0],
            'rotation_x': [0.1, 2.0],  # sub-02 exceeds 3° when combined
            'rotation_y': [0.1, 2.0],
            'rotation_z': [0.1, 2.0],
        })
        
        # sqrt(2^2+2^2+2^2) ≈ 3.46° > 3°
        result = filter_by_motion_threshold(
            motion_data, 
            translation_threshold_mm=3.0, 
            rotation_threshold_deg=3.0
        )
        
        assert len(result) == 1
        assert result['subject_id'].iloc[0] == 'sub-01'

    def test_filter_empty_dataframe(self):
        """Test handling of empty motion data."""
        empty_df = pd.DataFrame(columns=['subject_id', 'translation_x', 'rotation_x'])
        result = filter_by_motion_threshold(empty_df, 3.0, 3.0)
        assert len(result) == 0


class TestNilearnFallbackPreprocessing:
    """Tests for the Nilearn-based preprocessing fallback."""

    def test_preprocess_creates_output(self):
        """Test that preprocessing creates expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal 4D NIfTI-like file (using numpy for testing)
            # In real usage, this would be an actual NIfTI file
            nifti_path = Path(tmpdir) / "sub-01_task-rest_bold.nii.gz"
            
            # Create a dummy 4D array (2x2x2 voxels, 10 timepoints)
            dummy_data = np.random.randn(2, 2, 2, 10).astype(np.float32)
            
            # Save as NIfTI using nilearn
            from nilearn.image import new_img_like, load_img
            from nifti1 import Nifti1Header
            import nibabel as nib
            
            # Create a simple NIfTI image
            img = nib.Nifti1Image(dummy_data, np.eye(4))
            nib.save(img, str(nifti_path))
            
            # Create mask file
            mask_path = Path(tmpdir) / "mask.nii.gz"
            mask_data = np.ones((2, 2, 2), dtype=np.int8)
            mask_img = nib.Nifti1Image(mask_data, np.eye(4))
            nib.save(mask_img, str(mask_path))
            
            # Run preprocessing
            output_path = Path(tmpdir) / "preprocessed.nii.gz"
            result = nilearn_preprocess_fallback(
                bold_path=str(nifti_path),
                mask_path=str(mask_path),
                output_path=str(output_path),
                smoothing_mm=6,
                bandpass_low=0.01,
                bandpass_high=0.1
            )
            
            # Verify output exists
            assert result is not None
            assert output_path.exists()

    def test_preprocess_invalid_input(self):
        """Test handling of invalid input paths."""
        with pytest.raises(FileNotFoundError):
            nilearn_preprocess_fallback(
                bold_path="/nonexistent/bold.nii.gz",
                mask_path="/nonexistent/mask.nii.gz",
                output_path="/tmp/out.nii.gz"
            )

    def test_preprocess_invalid_mask(self):
        """Test handling of invalid mask file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bold_path = Path(tmpdir) / "bold.nii.gz"
            mask_path = Path(tmpdir) / "mask.nii.gz"
            output_path = Path(tmpdir) / "out.nii.gz"
            
            # Create valid bold
            dummy_data = np.random.randn(2, 2, 2, 10).astype(np.float32)
            img = nib.Nifti1Image(dummy_data, np.eye(4))
            nib.save(img, str(bold_path))
            
            # Create invalid mask (wrong dimensions)
            invalid_mask = np.ones((5, 5, 5), dtype=np.int8)
            mask_img = nib.Nifti1Image(invalid_mask, np.eye(4))
            nib.save(mask_img, str(mask_path))
            
            with pytest.raises(ValueError, match="Mask dimensions"):
                nilearn_preprocess_fallback(
                    bold_path=str(bold_path),
                    mask_path=str(mask_path),
                    output_path=str(output_path)
                )


class TestQCParser:
    """Tests for fMRIPrep QC report parsing."""

    def test_parse_qc_from_json(self):
        """Test parsing QC metrics from JSON report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            qc_json_path = Path(tmpdir) / "qc_summary.json"
            
            # Create mock QC data
            qc_data = {
                "subject_id": "sub-01",
                "motion_summary": {
                    "mean_trans_x": 0.1,
                    "mean_trans_y": 0.1,
                    "mean_trans_z": 0.1,
                    "mean_rot_x": 0.01,
                    "mean_rot_y": 0.01,
                    "mean_rot_z": 0.01,
                    "max_trans": 0.5,
                    "max_rot": 0.05
                },
                "snr": 150.5,
                "temporal_snr": 85.2,
                "report_path": "reports/sub-01_report.html"
            }
            
            with open(qc_json_path, 'w') as f:
                import json
                json.dump(qc_data, f)
            
            result = parse_fmriprep_qc(str(qc_json_path))
            
            assert result is not None
            assert result['subject_id'] == "sub-01"
            assert result['snr'] == 150.5
            assert result['temporal_snr'] == 85.2
            assert 'max_trans' in result['motion_summary']

    def test_parse_qc_missing_file(self):
        """Test handling of missing QC JSON file."""
        with pytest.raises(FileNotFoundError):
            parse_fmriprep_qc("/nonexistent/qc.json")

    def test_parse_qc_invalid_format(self):
        """Test handling of malformed QC JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            qc_json_path = Path(tmpdir) / "qc.json"
            
            # Create invalid JSON
            with open(qc_json_path, 'w') as f:
                f.write("{ invalid json }")
            
            with pytest.raises((ValueError, json.JSONDecodeError)):
                parse_fmriprep_qc(str(qc_json_path))