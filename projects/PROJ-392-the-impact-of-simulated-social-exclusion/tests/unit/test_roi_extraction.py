"""
Unit tests for ROI extraction module.

These tests verify the correct loading of ROI masks and basic extraction logic.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

import pytest

# Import the module under test
from code.analysis.roi_extraction import (
    load_roi_masks,
    extract_roi_betas,
    process_subject_roi_extraction,
    run_roi_extraction,
    ROIPreprocessingError
)


class TestLoadROIMasks:
    """Tests for load_roi_masks function."""

    def test_load_roi_masks_returns_dict(self):
        """Verify that load_roi_masks returns a dictionary with expected keys."""
        with patch('code.analysis.roi_extraction.fetch_atlas_aal') as mock_aal, \
             patch('code.analysis.roi_extraction.fetch_atlas_harvard_oxford') as mock_ho:
            # Mock AAL atlas
            mock_aal_data = MagicMock()
            mock_aal_data.maps = MagicMock()
            mock_aal_data.maps.get_fdata.return_value = np.ones((10, 10, 10, 100)) * 5
            mock_aal_data.labels = ['Index 0', 'Ventral Striatum', 'Other']
            mock_aal.return_value = mock_aal_data

            # Mock Harvard-Oxford atlas
            mock_ho_data = MagicMock()
            mock_ho_data.maps = MagicMock()
            mock_ho_data.maps.get_fdata.return_value = np.ones((10, 10, 10, 100)) * 0.5
            mock_ho_data.labels = ['Index 0', 'Frontal Orbital', 'Other']
            mock_ho.return_value = mock_ho_data

            # Mock image functions
            with patch('code.analysis.roi_extraction.image.new_img_like') as mock_new_img:
                mock_new_img.return_value = MagicMock()

                result = load_roi_masks(vs_threshold=0.2, ofc_threshold=0.2)

                assert isinstance(result, dict)
                assert 'vs_mask_img' in result
                assert 'ofc_mask_img' in result
                assert 'vs_coords' in result
                assert 'ofc_coords' in result

    def test_load_roi_masks_invalid_vs_label(self):
        """Test that ROIPreprocessingError is raised when VS label is not found."""
        with patch('code.analysis.roi_extraction.fetch_atlas_aal') as mock_aal:
            mock_aal_data = MagicMock()
            mock_aal_data.labels = ['Index 0', 'Other Label', 'Another']
            mock_aal.return_value = mock_aal_data

            with pytest.raises(ROIPreprocessingError, match="Ventral Striatum label"):
                load_roi_masks(vs_threshold=0.2)


class TestExtractROIBetas:
    """Tests for extract_roi_betas function."""

    def test_extract_roi_betas_calculates_mean(self):
        """Verify that extract_roi_betas calculates the mean of masked values."""
        with patch('code.analysis.roi_extraction.masking.apply_mask') as mock_apply_mask:
            mock_apply_mask.return_value = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

            mock_img = MagicMock()
            mock_mask = MagicMock()

            result = extract_roi_betas(mock_img, mock_mask, 'test_event')

            assert result == 3.0  # Mean of [1, 2, 3, 4, 5]

    def test_extract_roi_betas_empty_mask(self):
        """Test handling of empty mask (no voxels)."""
        with patch('code.analysis.roi_extraction.masking.apply_mask') as mock_apply_mask:
            mock_apply_mask.return_value = np.array([])

            mock_img = MagicMock()
            mock_mask = MagicMock()

            result = extract_roi_betas(mock_img, mock_mask, 'test_event')

            assert np.isnan(result)


class TestProcessSubjectROIExtraction:
    """Tests for process_subject_roi_extraction function."""

    def test_process_subject_returns_list(self):
        """Verify that process_subject_roi_extraction returns a list of results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            preprocessed_dir = Path(tmpdir)
            subject_dir = preprocessed_dir / 'sub-01'
            subject_dir.mkdir()

            # Create a dummy contrast file
            contrast_file = subject_dir / 'contrast_reward_anticipation.nii.gz'
            contrast_file.touch()

            mock_roi_masks = {
                'vs_mask_img': MagicMock(),
                'ofc_mask_img': MagicMock()
            }

            with patch('code.analysis.roi_extraction.image.load_img') as mock_load_img, \
                 patch('code.analysis.roi_extraction.extract_roi_betas') as mock_extract:

                mock_load_img.return_value = MagicMock()
                mock_extract.side_effect = [1.5, 2.0]  # VS and OFC values

                results = process_subject_roi_extraction(
                    subject_id='sub-01',
                    dataset_id='ds000246',
                    preprocessed_dir=preprocessed_dir,
                    roi_masks=mock_roi_masks,
                    event_types=['reward_anticipation'],
                    group_label='excluded'
                )

                assert isinstance(results, list)
                assert len(results) == 2  # VS and OFC for one event
                assert results[0]['roi'] in ['VentralStriatum', 'OFC']
                assert results[0]['event_type'] == 'reward_anticipation'


class TestRunROIExtraction:
    """Tests for run_roi_extraction function."""

    def test_run_roi_extraction_creates_output(self):
        """Verify that run_roi_extraction creates the output CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Mock metadata file
            metadata_file = Path(tmpdir) / 'unified_metadata.csv'
            metadata_df = pd.DataFrame({
                'participant_id': ['sub-01', 'sub-02'],
                'dataset_id': ['ds000246', 'ds000246'],
                'group': ['excluded', 'included']
            })
            metadata_df.to_csv(metadata_file, index=False)

            # Create preprocessed directory structure
            preprocessed_dir = Path(tmpdir) / 'processed-fmri'
            for subj in ['sub-01', 'sub-02']:
                subj_dir = preprocessed_dir / subj
                subj_dir.mkdir()
                # Create dummy contrast files
                (subj_dir / 'contrast_reward_anticipation.nii.gz').touch()
                (subj_dir / 'contrast_reward_receipt.nii.gz').touch()

            with patch('code.analysis.roi_extraction.get_config') as mock_config, \
                 patch('code.analysis.roi_extraction.load_roi_masks') as mock_load_masks, \
                 patch('code.analysis.roi_extraction.image.load_img') as mock_load_img, \
                 patch('code.analysis.roi_extraction.extract_roi_betas') as mock_extract:

                mock_config.return_value = {
                    'paths': {
                        'processed_fmri': str(preprocessed_dir),
                        'unified_metadata': str(metadata_file)
                    }
                }
                mock_load_masks.return_value = {
                    'vs_mask_img': MagicMock(),
                    'ofc_mask_img': MagicMock()
                }
                mock_load_img.return_value = MagicMock()
                mock_extract.return_value = 1.0

                result_path = run_roi_extraction(
                    output_dir=output_dir,
                    event_types=['reward_anticipation']
                )

                assert result_path.exists()
                assert result_path.name == 'beta_estimates.csv'

                # Verify CSV content
                df = pd.read_csv(result_path)
                assert 'participant_id' in df.columns
                assert 'beta_value' in df.columns

    def test_run_roi_extraction_handles_missing_metadata(self):
        """Test that FileNotFoundError is raised when metadata is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            with patch('code.analysis.roi_extraction.get_config') as mock_config:
                mock_config.return_value = {
                    'paths': {
                        'processed_fmri': str(Path(tmpdir) / 'processed'),
                        'unified_metadata': str(Path(tmpdir) / 'missing.csv')
                    }
                }

                with pytest.raises(FileNotFoundError, match="Unified metadata file not found"):
                    run_roi_extraction(output_dir=output_dir)
