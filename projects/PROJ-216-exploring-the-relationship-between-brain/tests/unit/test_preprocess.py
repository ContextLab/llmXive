import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocess import preprocess_subject, calculate_motion_metrics, check_fsl_afni

class TestPreprocessSubject:
    """Unit tests for the preprocess_subject function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def mock_subject_data(self, temp_dir):
        """Create mock subject data structure."""
        subject_dir = temp_dir / 'sub-01'
        func_dir = subject_dir / 'func'
        func_dir.mkdir(parents=True)
        
        # Create a mock NIfTI file (we'll mock the actual file operations)
        # In reality, we'd create a real NIfTI, but for unit testing we mock
        mock_func = func_dir / 'sub-01_task-rest_bold.nii.gz'
        mock_func.touch()
        
        return subject_dir

    def test_preprocess_subject_function_exists(self):
        """Test that the preprocess_subject function exists and has correct signature."""
        import inspect
        sig = inspect.signature(preprocess_subject)
        params = list(sig.parameters.keys())
        assert 'subject_path' in params
        assert 'subject_id' in params
        assert 'output_dir' in params
        assert 'atlas_path' in params

    @patch('preprocess.run_command')
    @patch('preprocess.Path.glob')
    @patch('nibabel.load')
    def test_preprocess_subject_motion_correction_done(
        self, mock_load, mock_glob, mock_run_command, mock_subject_data, temp_dir
    ):
        """Test that motion correction step completes and logs 'Motion Correction: Done'."""
        # Setup mocks
        mock_glob.return_value = [mock_subject_data / 'func' / 'sub-01_task-rest_bold.nii.gz']
        mock_run_command.return_value = MagicMock(returncode=0)
        
        # Mock nibabel to return data with non-zero variance
        mock_img = MagicMock()
        mock_img.get_fdata.return_value = np.random.rand(10, 10, 10, 20)
        mock_load.return_value = mock_img

        # Run preprocessing
        results = preprocess_subject(
            subject_path=mock_subject_data,
            subject_id='sub-01',
            output_dir=temp_dir / 'output'
        )

        # Verify motion correction was attempted
        assert any('motion_correction' in step.get('step', '') for step in results['steps'])
        assert results['status'] == 'completed'
        assert 'Motion Correction: Done' in open('data/processed/preprocessing.log', 'r').read()

    @patch('preprocess.run_command')
    @patch('preprocess.Path.glob')
    @patch('nibabel.load')
    def test_preprocess_subject_output_variance_check(
        self, mock_load, mock_glob, mock_run_command, mock_subject_data, temp_dir
    ):
        """Test that output variance is checked and non-zero."""
        # Setup mocks
        mock_glob.return_value = [mock_subject_data / 'func' / 'sub-01_task-rest_bold.nii.gz']
        mock_run_command.return_value = MagicMock(returncode=0)
        
        # Mock data with non-zero variance
        mock_img = MagicMock()
        mock_img.get_fdata.return_value = np.random.rand(10, 10, 10, 20)
        mock_load.return_value = mock_img

        results = preprocess_subject(
            subject_path=mock_subject_data,
            subject_id='sub-01',
            output_dir=temp_dir / 'output'
        )

        assert 'output_variance' in results
        assert results['output_variance'] > 0

    @patch('preprocess.run_command')
    @patch('preprocess.Path.glob')
    @patch('nibabel.load')
    def test_preprocess_subject_zero_variance_fails(
        self, mock_load, mock_glob, mock_run_command, mock_subject_data, temp_dir
    ):
        """Test that zero variance output is detected and marked as failed."""
        # Setup mocks
        mock_glob.return_value = [mock_subject_data / 'func' / 'sub-01_task-rest_bold.nii.gz']
        mock_run_command.return_value = MagicMock(returncode=0)
        
        # Mock data with zero variance
        mock_img = MagicMock()
        mock_img.get_fdata.return_value = np.zeros((10, 10, 10, 20))
        mock_load.return_value = mock_img

        results = preprocess_subject(
            subject_path=mock_subject_data,
            subject_id='sub-01',
            output_dir=temp_dir / 'output'
        )

        assert results['status'] == 'failed'
        assert 'Zero variance' in results.get('error', '')

    def test_check_fsl_afni_exists(self):
        """Test that check_fsl_afni function exists."""
        assert callable(check_fsl_afni)

class TestCalculateMotionMetrics:
    """Unit tests for calculate_motion_metrics function."""

    def test_calculate_motion_metrics_returns_dict(self):
        """Test that calculate_motion_metrics returns a dictionary with expected keys."""
        mock_path = Path('dummy/path.nii.gz')
        result = calculate_motion_metrics(mock_path)
        
        assert isinstance(result, dict)
        assert 'translation_mm' in result
        assert 'rotation_mm' in result
        assert 'framewise_displacement' in result
        assert isinstance(result['translation_mm'], float)
        assert isinstance(result['rotation_mm'], float)
        assert isinstance(result['framewise_displacement'], float)
