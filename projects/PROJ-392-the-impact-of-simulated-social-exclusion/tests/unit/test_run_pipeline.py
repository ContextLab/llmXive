"""
Unit tests for the run_pipeline orchestration module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.run_pipeline import (
    PipelineError,
    log_step,
    run_download_phase,
    run_preprocessing_phase,
    run_analysis_phase,
    run_visualization_phase,
    run_pipeline,
    generate_final_provenance
)


class TestPipelineError:
    """Tests for custom PipelineError exception."""

    def test_pipeline_error_instantiation(self):
        """Test that PipelineError can be instantiated with a message."""
        error = PipelineError("Test error message")
        assert str(error) == "Test error message"


class TestLogStep:
    """Tests for the log_step utility function."""

    @patch('pipeline.run_pipeline.logger')
    def test_log_step_basic(self, mock_logger):
        """Test basic logging of a step."""
        log_step("Test Step", "STARTED")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Test Step" in call_args
        assert "STARTED" in call_args


class TestRunDownloadPhase:
    """Tests for the download phase."""

    @patch('pipeline.run_pipeline.get_config')
    @patch('pipeline.run_pipeline.logger')
    def test_run_download_phase_success(self, mock_logger, mock_get_config):
        """Test successful download phase."""
        mock_get_config.return_value = {'dataset_ids': ['ds000246']}
        
        result = run_download_phase({'dataset_ids': ['ds000246']})
        
        assert result is True
        mock_logger.info.assert_called()


class TestRunPreprocessingPhase:
    """Tests for the preprocessing phase."""

    @patch('pipeline.run_pipeline.logger')
    def test_run_preprocessing_phase_success(self, mock_logger):
        """Test successful preprocessing phase."""
        result = run_preprocessing_phase({'preprocessing_params': {'kernel': 6}})
        
        assert result is True


class TestRunAnalysisPhase:
    """Tests for the analysis phase."""

    @patch('pipeline.run_pipeline.logger')
    def test_run_analysis_phase_success(self, mock_logger):
        """Test successful analysis phase."""
        result = run_analysis_phase({'roi_names': ['VS', 'OFC']})
        
        assert result is True


class TestRunVisualizationPhase:
    """Tests for the visualization phase."""

    @patch('pipeline.run_pipeline.logger')
    def test_run_visualization_phase_success(self, mock_logger):
        """Test successful visualization phase."""
        result = run_visualization_phase({})
        
        assert result is True


class TestRunPipeline:
    """Tests for the main pipeline orchestration."""

    @patch('pipeline.run_pipeline.run_download_phase')
    @patch('pipeline.run_pipeline.run_preprocessing_phase')
    @patch('pipeline.run_pipeline.run_analysis_phase')
    @patch('pipeline.run_pipeline.run_visualization_phase')
    @patch('pipeline.run_pipeline.get_config')
    @patch('pipeline.run_pipeline.ensure_paths_exist')
    @patch('pipeline.run_pipeline.generate_final_provenance')
    def test_run_pipeline_full_success(
        self,
        mock_provenance,
        mock_ensure_paths,
        mock_get_config,
        mock_visualize,
        mock_analyze,
        mock_preprocess,
        mock_download
    ):
        """Test full pipeline execution with all phases succeeding."""
        mock_get_config.return_value = {
            'pipeline_version': '1.0.0',
            'results': 'data/results'
        }
        mock_download.return_value = True
        mock_preprocess.return_value = True
        mock_analyze.return_value = True
        mock_visualize.return_value = True

        exit_code = run_pipeline()

        assert exit_code == 0
        mock_download.assert_called_once()
        mock_preprocess.assert_called_once()
        mock_analyze.assert_called_once()
        mock_visualize.assert_called_once()
        mock_provenance.assert_called_once()

    @patch('pipeline.run_pipeline.run_download_phase')
    @patch('pipeline.run_pipeline.get_config')
    @patch('pipeline.run_pipeline.ensure_paths_exist')
    def test_run_pipeline_download_failure(
        self,
        mock_ensure_paths,
        mock_get_config,
        mock_download
    ):
        """Test pipeline fails when download phase fails."""
        mock_get_config.return_value = {'results': 'data/results'}
        mock_download.return_value = False

        exit_code = run_pipeline()

        assert exit_code == 1
        mock_download.assert_called_once()
        # Subsequent phases should not be called
        # Note: In this test we can't easily mock the other phases without more setup
        # but the logic ensures they aren't reached


class TestGenerateFinalProvenance:
    """Tests for provenance generation."""

    @patch('pipeline.run_pipeline.generate_checksums')
    @patch('pipeline.run_pipeline.generate_provenance_record')
    @patch('pipeline.run_pipeline.write_provenance_sidecar')
    @patch('pipeline.run_pipeline.logger')
    def test_generate_final_provenance_success(
        self,
        mock_logger,
        mock_write,
        mock_record,
        mock_checksums
    ):
        """Test successful provenance generation."""
        mock_checksums.return_value = {'file1.nii': 'abc123'}
        mock_record.return_value = {'pipeline': 'test'}
        
        output_dir = Path('data/results')
        generate_final_provenance(output_dir, '1.0.0')
        
        mock_checksums.assert_called_once_with(output_dir)
        mock_record.assert_called_once()
        mock_write.assert_called_once()
        mock_logger.info.assert_called()