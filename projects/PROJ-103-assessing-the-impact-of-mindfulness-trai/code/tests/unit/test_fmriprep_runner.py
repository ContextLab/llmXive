"""
Unit tests for the fMRIPrep Docker Runner.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.preprocessing.fmriprep_runner import (
    FMRIPrepRunnerError,
    get_fmriprep_config,
    build_fmriprep_command,
    run_fmriprep
)
from src.config.settings import get_config


class TestGetFMRIPrepConfig:
    def test_default_config_values(self):
        """Test that default config values are returned when not overridden."""
        with patch('src.preprocessing.fmriprep_runner.get_config') as mock_get_config:
            mock_get_config.return_value = {}
            config = get_fmriprep_config()
            
            assert config['docker_image'] == 'nipreps/fmriprep:23.1.3'
            assert config['nthreads'] == 4
            assert config['mem_mb'] == 8000
            assert config['omp_nthreads'] == 4
            assert config['skull_strip_mode'] == 'slap'

    def test_custom_config_values(self):
        """Test that custom config values from settings are used."""
        custom_config = {
            'fmriprep': {
                'docker_image': 'custom/fmriprep:latest',
                'resources': {
                    'nthreads': 8,
                    'mem_mb': 16000,
                    'omp_nthreads': 8
                },
                'ignore': ['slicetiming'],
                'skull_strip_mode': 'auto'
            }
        }
        with patch('src.preprocessing.fmriprep_runner.get_config', return_value=custom_config):
            config = get_fmriprep_config()
            
            assert config['docker_image'] == 'custom/fmriprep:latest'
            assert config['nthreads'] == 8
            assert config['mem_mb'] == 16000
            assert config['ignore'] == ['slicetiming']
            assert config['skull_strip_mode'] == 'auto'


class TestBuildFMRIPrepCommand:
    def test_command_structure(self):
        """Test that the command list has the correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bids_root = Path(tmpdir) / "bids"
            bids_root.mkdir()
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            config = get_fmriprep_config()
            cmd = build_fmriprep_command(bids_root, output_dir, "sub-01", config)
            
            assert cmd[0] == "docker"
            assert cmd[1] == "run"
            assert "--rm" in cmd
            assert f"{bids_root}:/data:ro" in cmd
            assert f"{output_dir}:/out" in cmd
            assert "sub-01" in cmd
            assert config['docker_image'] in cmd
            assert "participant" in cmd

    def test_mount_paths(self):
        """Test that mount paths are correctly formatted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bids_root = Path(tmpdir) / "bids"
            bids_root.mkdir()
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            config = get_fmriprep_config()
            cmd = build_fmriprep_command(bids_root, output_dir, "sub-01", config)
            
            # Check for -v flags
            v_indices = [i for i, x in enumerate(cmd) if x == "-v"]
            assert len(v_indices) >= 2
            
            # Check read-only mount for bids
            assert f"{bids_root}:/data:ro" in cmd
            # Check output mount
            assert f"{output_dir}:/out" in cmd

    def test_nonexistent_subject_dir(self):
        """Test that an error is raised if the subject directory doesn't exist."""
        bids_root = Path("/nonexistent/path")
        output_dir = Path("/tmp/output")
        config = get_fmriprep_config()
        
        with pytest.raises(FMRIPrepRunnerError, match="does not exist"):
            build_fmriprep_command(bids_root, output_dir, "sub-01", config)


class TestRunFMRIPrep:
    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.mkdir')
    def test_successful_run(self, mock_mkdir, mock_get_data_dir, mock_run):
        """Test a successful fMRIPrep run."""
        mock_get_data_dir.return_value = Path("/data")
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock the existence check
        with patch('pathlib.Path.exists', return_value=True):
            result = run_fmriprep("sub-01")
            
            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert "check=True" in str(call_args)

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    def test_docker_not_found(self, mock_get_data_dir, mock_run):
        """Test handling of Docker not found error."""
        mock_get_data_dir.return_value = Path("/data")
        mock_run.side_effect = FileNotFoundError("Docker not found")
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(FMRIPrepRunnerError, match="Docker command not found"):
                run_fmriprep("sub-01")

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    def test_preprocessing_failure(self, mock_get_data_dir, mock_run):
        """Test handling of fMRIPrep process failure."""
        mock_get_data_dir.return_value = Path("/data")
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", output="Error log")
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(FMRIPrepRunnerError, match="execution failed"):
                run_fmriprep("sub-01")

    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    def test_bids_root_not_found(self, mock_get_data_dir):
        """Test handling of missing BIDS root."""
        mock_get_data_dir.return_value = Path("/data")
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FMRIPrepRunnerError, match="does not exist"):
                run_fmriprep("sub-01")


class TestMain:
    @patch('src.preprocessing.fmriprep_runner.run_fmriprep')
    @patch('src.preprocessing.fmriprep_runner.sys.exit')
    def test_main_success(self, mock_exit, mock_run):
        """Test main function on success."""
        mock_run.return_value = True
        
        with patch('sys.argv', ['fmriprep_runner.py', '--subject', 'sub-01']):
            from src.preprocessing.fmriprep_runner import main
            main()
            
            mock_exit.assert_called_once_with(0)

    @patch('src.preprocessing.fmriprep_runner.run_fmriprep')
    @patch('src.preprocessing.fmriprep_runner.sys.exit')
    def test_main_failure(self, mock_exit, mock_run):
        """Test main function on failure."""
        mock_run.side_effect = FMRIPrepRunnerError("Test error")
        
        with patch('sys.argv', ['fmriprep_runner.py', '--subject', 'sub-01']):
            from src.preprocessing.fmriprep_runner import main
            main()
            
            mock_exit.assert_called_once_with(1)