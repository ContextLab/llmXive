"""
Unit tests for the fMRIPrep runner.

These tests verify command construction and configuration loading.
Actual Docker execution is mocked to avoid resource consumption during unit tests.
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
    run_fmriprep,
    main
)
from src.config.env import EnvConfig


class TestGetFMRIPrepConfig:
    """Tests for configuration retrieval."""

    @patch('src.preprocessing.fmriprep_runner.get_config')
    def test_default_config_values(self, mock_get_config):
        """Test that default values are used when config is empty."""
        mock_get_config.return_value = {}
        
        config = get_fmriprep_config()
        
        assert config['thread_count'] == 4
        assert config['memory_gb'] == 8
        assert config['fmriprep_version'] == '23.1.0'
        assert config['nprocs'] == 4
        assert config['omp_nthreads'] == 4

    @patch('src.preprocessing.fmriprep_runner.get_config')
    def test_custom_config_values(self, mock_get_config):
        """Test that custom config values override defaults."""
        mock_get_config.return_value = {
            'preprocessing_params': {
                'thread_count': 8,
                'memory_gb': 16,
                'fmriprep_version': '20.2.0',
                'nprocs': 2,
                'omp_nthreads': 2
            }
        }
        
        config = get_fmriprep_config()
        
        assert config['thread_count'] == 8
        assert config['memory_gb'] == 16
        assert config['fmriprep_version'] == '20.2.0'
        assert config['nprocs'] == 2
        assert config['omp_nthreads'] == 2


class TestBuildFMRIPrepCommand:
    """Tests for command line construction."""

    def test_basic_command_structure(self):
        """Test that the command contains required docker flags."""
        dataset_path = Path('/data/raw/ds000001')
        output_dir = Path('/data/processed/ds000001')
        
        cmd = build_fmriprep_command(dataset_path, output_dir)
        
        assert 'docker' in cmd
        assert 'run' in cmd
        assert '--rm' in cmd
        assert 'nipreps/fmriprep' in str(cmd)
        assert str(dataset_path) in cmd
        assert 'participant' in cmd

    def test_memory_and_threads(self):
        """Test that memory and thread flags are correctly set."""
        dataset_path = Path('/data/raw/ds000001')
        output_dir = Path('/data/processed/ds000001')
        config = {
            'thread_count': 4,
            'memory_gb': 8,
            'omp_nthreads': 4,
            'nprocs': 4,
            'fmriprep_version': '23.1.0'
        }
        
        cmd = build_fmriprep_command(dataset_path, output_dir, config=config)
        
        cmd_str = ' '.join(cmd)
        assert '--mem' in cmd
        assert '8192MB' in cmd_str  # 8GB
        assert '--nprocs' in cmd
        assert '4' in cmd
        assert '--omp-nthreads' in cmd

    def test_participant_label(self):
        """Test that participant labels are added to the command."""
        dataset_path = Path('/data/raw/ds000001')
        output_dir = Path('/data/processed/ds000001')
        participants = ['01', '02']
        
        cmd = build_fmriprep_command(
            dataset_path, 
            output_dir, 
            participant_label=participants
        )
        
        # Check that --participant-label appears for each subject
        label_count = sum(1 for x in cmd if x == '--participant-label')
        assert label_count == len(participants)

    def test_output_spaces(self):
        """Test that MNI152 output space is requested."""
        dataset_path = Path('/data/raw/ds000001')
        output_dir = Path('/data/processed/ds000001')
        
        cmd = build_fmriprep_command(dataset_path, output_dir)
        
        cmd_str = ' '.join(cmd)
        assert '--output-spaces' in cmd_str
        assert 'MNI152NLin2009cAsym' in cmd_str


class TestRunFMRIPrep:
    """Tests for the execution logic."""

    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('src.preprocessing.fmriprep_runner.get_fmriprep_config')
    @patch('src.preprocessing.fmriprep_runner.build_fmriprep_command')
    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    def test_successful_run(self, mock_run, mock_build, mock_get_config, mock_get_data_dir):
        """Test a successful execution path."""
        mock_get_data_dir.return_value = '/tmp/data'
        mock_get_config.return_value = {
            'thread_count': 4,
            'memory_gb': 8,
            'fmriprep_version': '23.1.0',
            'nprocs': 4,
            'omp_nthreads': 4
        }
        mock_build.return_value = ['docker', 'run', 'cmd']
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Mock the dataset existence check
        with patch('pathlib.Path.exists', return_value=True):
            result = run_fmriprep('ds000001')
            
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('src.preprocessing.fmriprep_runner.get_fmriprep_config')
    @patch('src.preprocessing.fmriprep_runner.build_fmriprep_command')
    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    def test_failed_execution(self, mock_run, mock_build, mock_get_config, mock_get_data_dir):
        """Test that an error is raised when the process fails."""
        mock_get_data_dir.return_value = '/tmp/data'
        mock_get_config.return_value = {'thread_count': 4, 'memory_gb': 8, 'fmriprep_version': '23.1.0', 'nprocs': 4, 'omp_nthreads': 4}
        mock_build.return_value = ['docker', 'run', 'cmd']
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_result.stderr = "Error details"
        mock_run.return_value = mock_result
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(FMRIPrepRunnerError, match="fMRIPrep failed"):
                run_fmriprep('ds000001')

    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    def test_missing_dataset(self, mock_get_data_dir):
        """Test that an error is raised if the dataset path does not exist."""
        mock_get_data_dir.return_value = '/tmp/data'
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FMRIPrepRunnerError, match="Dataset path not found"):
                run_fmriprep('ds000001')

    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('src.preprocessing.fmriprep_runner.get_fmriprep_config')
    @patch('src.preprocessing.fmriprep_runner.build_fmriprep_command')
    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    def test_docker_not_found(self, mock_run, mock_build, mock_get_config, mock_get_data_dir):
        """Test handling of missing Docker executable."""
        mock_get_data_dir.return_value = '/tmp/data'
        mock_get_config.return_value = {'thread_count': 4, 'memory_gb': 8, 'fmriprep_version': '23.1.0', 'nprocs': 4, 'omp_nthreads': 4}
        mock_build.return_value = ['docker', 'run', 'cmd']
        mock_run.side_effect = FileNotFoundError("Docker not found")
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(FMRIPrepRunnerError, match="Docker executable not found"):
                run_fmriprep('ds000001')


class TestMain:
    """Tests for the CLI entry point."""

    @patch('sys.argv', ['fmriprep_runner', 'ds000001'])
    @patch('src.preprocessing.fmriprep_runner.run_fmriprep')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_run):
        """Test that main calls run_fmriprep with correct args."""
        mock_run.return_value = None
        
        # We need to mock sys.exit to prevent the script from terminating
        with patch('sys.exit'):
            main()
        
        mock_run.assert_called_once()
        mock_print.assert_called()
        assert 'Successfully processed' in str(mock_print.call_args)

    @patch('sys.argv', ['fmriprep_runner'])
    @patch('builtins.print')
    def test_main_no_args(self, mock_print):
        """Test usage message when no arguments provided."""
        with patch('sys.exit') as mock_exit:
            main()
            
        mock_print.assert_called()
        mock_exit.assert_called_with(1)
        assert 'Usage' in str(mock_print.call_args)