"""
Unit tests for first-level GLM analysis module.

These tests verify the core functionality of the first-level GLM pipeline
without requiring actual fMRI data files.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
import pytest

from analysis.first_level_glm import (
    FirstLevelGLMError,
    load_events,
    create_design_matrix,
    fit_first_level_glm,
    process_subject_first_level,
    run_first_level_glm_pipeline,
    save_results_summary
)


class TestLoadEvents:
    """Tests for the load_events function."""

    def test_load_events_success(self, tmp_path):
        """Test successful loading of events file."""
        events_data = """onset\tduration\ttrial_type
        10\t2\treward
        20\t2\tneutral
        30\t2\treward"""

        events_file = tmp_path / "events.tsv"
        events_file.write_text(events_data)

        result = load_events(events_file)

        assert len(result) == 3
        assert 'onset' in result.columns
        assert 'duration' in result.columns
        assert 'trial_type' in result.columns
        assert result['trial_type'].tolist() == ['reward', 'neutral', 'reward']

    def test_load_events_missing_file(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FirstLevelGLMError):
            load_events(tmp_path / "nonexistent.tsv")

    def test_load_events_missing_columns(self, tmp_path):
        """Test error handling for missing required columns."""
        events_data = """onset\tduration
        10\t2
        20\t2"""

        events_file = tmp_path / "events.tsv"
        events_file.write_text(events_data)

        with pytest.raises(FirstLevelGLMError):
            load_events(events_file)


class TestCreateDesignMatrix:
    """Tests for the create_design_matrix function."""

    def test_design_matrix_creation(self):
        """Test basic design matrix creation."""
        events = pd.DataFrame({
            'onset': [10, 20, 30],
            'duration': [2, 2, 2],
            'trial_type': ['reward', 'neutral', 'reward']
        })

        frame_times = np.arange(0, 100, 2)

        design = create_design_matrix(events, frame_times)

        assert len(design) == len(frame_times)
        assert 'reward' in design.columns or any('reward' in col for col in design.columns)


class TestProcessSubjectFirstLevel:
    """Tests for the process_subject_first_level function."""

    @patch('analysis.first_level_glm.load_events')
    @patch('analysis.first_level_glm.create_design_matrix')
    @patch('analysis.first_level_glm.fit_first_level_glm')
    @patch('analysis.first_level_glm.compute_contrasts')
    @patch('analysis.first_level_glm.generate_provenance_record')
    @patch('analysis.first_level_glm.write_provenance_sidecar')
    def test_process_subject_success(
        self,
        mock_write_provenance,
        mock_generate_provenance,
        mock_compute_contrasts,
        mock_fit_glm,
        mock_create_design,
        mock_load_events,
        tmp_path
    ):
        """Test successful processing of a subject."""
        # Mock the dependencies
        mock_events = pd.DataFrame({
            'onset': [10, 20],
            'duration': [2, 2],
            'trial_type': ['reward', 'neutral']
        })
        mock_load_events.return_value = mock_events

        mock_design = pd.DataFrame(np.random.rand(100, 5), columns=['col1', 'col2', 'col3', 'col4', 'col5'])
        mock_create_design.return_value = mock_design

        mock_model = MagicMock()
        mock_fit_glm.return_value = mock_model

        mock_z_map = MagicMock()
        mock_effect_map = MagicMock()
        mock_model.compute_contrast.side_effect = [mock_z_map, mock_effect_map]

        mock_compute_contrasts.return_value = {'reward_vs_neutral': tmp_path / "zmap.nii.gz"}

        mock_provenance = {'task': 'first_level_glm', 'status': 'success'}
        mock_generate_provenance.return_value = mock_provenance

        # Mock config
        config = {
            'analysis_params': {
                'noise_model': 'ar1',
                'hrf_model': 'spm',
                'contrast_definitions': {'reward_vs_neutral': 'reward - neutral'}
            }
        }

        # Create a mock BOLD path
        bold_path = tmp_path / "bold.nii.gz"
        bold_path.touch()

        events_path = tmp_path / "events.tsv"
        events_path.write_text("onset\tduration\ttrial_type\n10\t2\treward")

        result = process_subject_first_level(
            subject_id='01',
            run_id='1',
            bold_path=bold_path,
            events_path=events_path,
            tr=2.0,
            config=config
        )

        assert result['status'] == 'success'
        assert result['subject_id'] == '01'
        assert result['run_id'] == '1'
        assert 'reward_vs_neutral' in result['contrast_files']


class TestSaveResultsSummary:
    """Tests for the save_results_summary function."""

    def test_save_results_summary(self, tmp_path):
        """Test saving results summary to JSON."""
        results = [
            {'subject_id': '01', 'status': 'success'},
            {'subject_id': '02', 'status': 'failed'},
            {'subject_id': '03', 'status': 'skipped'}
        ]

        output_path = tmp_path / "summary.json"
        save_results_summary(results, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            summary = json.load(f)

        assert summary['total_subjects'] == 3
        assert summary['successful'] == 1
        assert summary['failed'] == 1
        assert summary['skipped'] == 1


class TestIntegration:
    """Integration tests that mock external dependencies."""

    @patch('analysis.first_level_glm.get_path')
    @patch('analysis.first_level_glm.get_data')
    @patch('analysis.first_level_glm.load_events')
    @patch('analysis.first_level_glm.create_design_matrix')
    @patch('analysis.first_level_glm.fit_first_level_glm')
    @patch('analysis.first_level_glm.compute_contrasts')
    def test_full_pipeline_with_mocked_data(
        self,
        mock_compute_contrasts,
        mock_fit_glm,
        mock_create_design,
        mock_load_events,
        mock_get_data,
        mock_get_path,
        tmp_path
    ):
        """Test the full pipeline with mocked data and dependencies."""
        # Setup mocks
        mock_get_path.side_effect = lambda x: tmp_path / x

        mock_events = pd.DataFrame({
            'onset': [10, 20, 30],
            'duration': [2, 2, 2],
            'trial_type': ['reward', 'neutral', 'reward']
        })
        mock_load_events.return_value = mock_events

        mock_design = pd.DataFrame(np.random.rand(100, 5), columns=['col1', 'col2', 'col3', 'col4', 'col5'])
        mock_create_design.return_value = mock_design

        mock_model = MagicMock()
        mock_fit_glm.return_value = mock_model

        mock_z_map = MagicMock()
        mock_effect_map = MagicMock()
        mock_model.compute_contrast.side_effect = [mock_z_map, mock_effect_map]

        mock_compute_contrasts.return_value = {'reward_vs_neutral': tmp_path / "zmap.nii.gz"}

        mock_get_data.return_value = np.zeros((10, 10, 10, 100))

        config = {
            'analysis_params': {
                'noise_model': 'ar1',
                'hrf_model': 'spm',
                'tr': 2.0,
                'contrast_definitions': {'reward_vs_neutral': 'reward - neutral'}
            }
        }

        # Create mock file paths
        bold_path = tmp_path / "processed_fmri" / "sub-01" / "func" / "sub-01_task-reward_run-1_space-MNI_desc-preproc_bold.nii.gz"
        bold_path.parent.mkdir(parents=True, exist_ok=True)
        bold_path.touch()

        events_path = tmp_path / "raw_fmri" / "sub-01" / "func" / "sub-01_task-reward_run-1_events.tsv"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text("onset\tduration\ttrial_type\n10\t2\treward")

        # Run pipeline
        results = run_first_level_glm_pipeline(
            subjects=['01'],
            runs=['1'],
            config=config
        )

        assert len(results) == 1
        assert results[0]['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
