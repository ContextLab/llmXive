import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import (
    run_command, 
    check_fsl_afni, 
    calculate_motion_metrics, 
    preprocess_subject,
    load_motion_exclusion_log,
    main
)
from utils import ResourceMonitor

class TestPreprocess:
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            (tmpdir / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
            (tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func').mkdir(parents=True, exist_ok=True)
            yield tmpdir

    def test_run_command_success(self):
        """Test run_command with a successful command."""
        result = run_command(['echo', 'hello'], "Test echo")
        assert result is True

    def test_run_command_failure(self):
        """Test run_command with a failing command."""
        result = run_command(['false'], "Test false")
        assert result is False

    def test_run_command_not_found(self):
        """Test run_command with a non-existent command."""
        result = run_command(['non_existent_command_12345'], "Test not found")
        assert result is False

    def test_check_fsl_afni(self):
        """Test check_fsl_afni function."""
        # This will likely return False in test environment without FSL/AFNI
        result = check_fsl_afni()
        # We just verify it runs without error
        assert isinstance(result, bool)

    def test_calculate_motion_metrics_no_file(self):
        """Test calculate_motion_metrics when file doesn't exist."""
        from pathlib import Path
        func_file = Path('/non/existent/file.nii.gz')
        motion_file = Path('/non/existent/motion.txt')
        
        metrics = calculate_motion_metrics(func_file, motion_file)
        
        assert metrics['translation_mm'] == 0.0
        assert metrics['rotation_mm'] == 0.0

    def test_calculate_motion_metrics_with_file(self, temp_dirs):
        """Test calculate_motion_metrics with a valid motion file."""
        tmpdir = temp_dirs
        func_file = tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func' / 'sub-01_task-rest_bold.nii.gz'
        motion_file = tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func' / 'sub-01_mc.txt'
        
        # Create a dummy motion file
        motion_content = """
        0.0 0.0 0.0 0.0 0.0 0.0
        0.1 0.0 0.0 0.0 0.0 0.0
        0.0 0.2 0.0 0.0 0.0 0.0
        """
        with open(motion_file, 'w') as f:
            f.write(motion_content)
        
        metrics = calculate_motion_metrics(func_file, motion_file)
        
        # Should detect motion
        assert metrics['translation_mm'] > 0.0 or metrics['rotation_mm'] > 0.0

    def test_load_motion_exclusion_log_empty(self, temp_dirs):
        """Test load_motion_exclusion_log when file doesn't exist."""
        tmpdir = temp_dirs
        # Change to temp dir to avoid reading real file
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            excluded = load_motion_exclusion_log()
            assert excluded == []
        finally:
            os.chdir(original_cwd)

    def test_load_motion_exclusion_log_with_data(self, temp_dirs):
        """Test load_motion_exclusion_log with valid CSV data."""
        tmpdir = temp_dirs
        exclusion_log = tmpdir / 'data' / 'processed' / 'motion_exclusion_log.csv'
        
        csv_content = """subject_id,translation_mm,rotation_mm,excluded
        sub-01,5.0,2.0,true
        sub-02,1.0,0.5,false
        sub-03,4.0,1.5,true
        """
        with open(exclusion_log, 'w') as f:
            f.write(csv_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            excluded = load_motion_exclusion_log()
            assert 'sub-01' in excluded
            assert 'sub-03' in excluded
            assert 'sub-02' not in excluded
            assert len(excluded) == 2
        finally:
            os.chdir(original_cwd)

    @patch('preprocess.check_fsl_afni')
    @patch('preprocess.run_command')
    def test_preprocess_subject_success(self, mock_run, mock_check, temp_dirs):
        """Test preprocess_subject with mocked dependencies."""
        tmpdir = temp_dirs
        input_func = tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func' / 'sub-01_task-rest_bold.nii.gz'
        output_dir = tmpdir / 'data' / 'processed' / 'preprocessed'
        
        # Create dummy input file
        input_func.parent.mkdir(parents=True, exist_ok=True)
        input_func.touch()
        
        # Mock dependencies
        mock_check.return_value = True
        mock_run.return_value = True
        
        resource_monitor = ResourceMonitor()
        status = preprocess_subject('sub-01', input_func, output_dir, resource_monitor)
        
        assert status['status'] == 'success'
        assert 'subject_id' in status
        assert 'steps_completed' in status
        assert 'motion_metrics' in status

    @patch('preprocess.check_fsl_afni')
    @patch('preprocess.run_command')
    def test_preprocess_subject_failure(self, mock_run, mock_check, temp_dirs):
        """Test preprocess_subject when commands fail."""
        tmpdir = temp_dirs
        input_func = tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func' / 'sub-01_task-rest_bold.nii.gz'
        output_dir = tmpdir / 'data' / 'processed' / 'preprocessed'
        
        # Create dummy input file
        input_func.parent.mkdir(parents=True, exist_ok=True)
        input_func.touch()
        
        # Mock dependencies to fail
        mock_check.return_value = True
        mock_run.return_value = False
        
        resource_monitor = ResourceMonitor()
        status = preprocess_subject('sub-01', input_func, output_dir, resource_monitor)
        
        assert status['status'] == 'failed'
        assert len(status['errors']) > 0

    def test_main_integration(self, temp_dirs, monkeypatch):
        """Test main function with mocked data."""
        tmpdir = temp_dirs
        monkeypatch.chdir(tmpdir)
        
        # Create required directories and files
        (tmpdir / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
        (tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func').mkdir(parents=True, exist_ok=True)
        
        # Create valid_subjects.json
        valid_subjects = {
            'subjects': [
                {'id': 'sub-01', 'score': 0.5}
            ],
            'count': 1
        }
        with open(tmpdir / 'data' / 'processed' / 'valid_subjects.json', 'w') as f:
            json.dump(valid_subjects, f)
        
        # Create input file
        input_func = tmpdir / 'data' / 'raw' / 'ds000224' / 'sub-01' / 'func' / 'sub-01_task-rest_bold.nii.gz'
        input_func.touch()
        
        # Mock functions to avoid actual preprocessing
        with patch('preprocess.check_fsl_afni', return_value=False):
            with patch('preprocess.run_command', return_value=True):
                with patch('preprocess.ResourceMonitor'):
                    result = main()
                    
        # Verify stats file was created
        stats_path = tmpdir / 'data' / 'processed' / 'preprocessing_stats.json'
        assert stats_path.exists()
        
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        assert 'total_subjects' in stats
        assert 'successful_subjects' in stats
        assert 'success_rate_percentage' in stats