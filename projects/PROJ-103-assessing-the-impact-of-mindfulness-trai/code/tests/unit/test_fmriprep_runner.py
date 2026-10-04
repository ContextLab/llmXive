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
from src.config.env import get_data_dir

class TestGetFMRIPrepConfig:
    def test_default_config_values(self):
        """Test that default resource constraints are returned when not specified."""
        with patch('src.preprocessing.fmriprep_runner.get_config') as mock_get_config:
            mock_get_config.return_value = {
                'preprocessing_params': {}
            }
            
            config = get_fmriprep_config()
            
            assert config['omp_num_threads'] == 2
            assert config['mem_mb'] == 2048
            assert config['nprocs'] == 2
            assert config['use_plugin'] == 'single'

    def test_custom_config_values(self):
        """Test that custom resource constraints are respected."""
        with patch('src.preprocessing.fmriprep_runner.get_config') as mock_get_config:
            mock_get_config.return_value = {
                'preprocessing_params': {
                    'omp_num_threads': 4,
                    'mem_mb': 4096,
                    'nprocs': 4
                }
            }
            
            config = get_fmriprep_config()
            
            assert config['omp_num_threads'] == 4
            assert config['mem_mb'] == 4096
            assert config['nprocs'] == 4

class TestBuildFMRIPrepCommand:
    def test_basic_command_structure(self):
        """Test that the command includes essential Docker arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset"
            output_path = Path(tmpdir) / "output"
            dataset_path.mkdir()
            
            cmd = build_fmriprep_command(dataset_path, output_path)
            
            assert "docker" in cmd
            assert "run" in cmd
            assert "--rm" in cmd
            assert "participant" in cmd
            assert str(dataset_path) in cmd[cmd.index("-v") + 1].split(":")[0]

    def test_thread_memory_settings(self):
        """Test that thread and memory settings are included."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset"
            output_path = Path(tmpdir) / "output"
            dataset_path.mkdir()
            
            with patch('src.preprocessing.fmriprep_runner.get_fmriprep_config') as mock_config:
                mock_config.return_value = {
                    'omp_num_threads': 4,
                    'mem_mb': 4096,
                    'nprocs': 4,
                    'use_plugin': 'single',
                    'plugin_args': {}
                }
                
                cmd = build_fmriprep_command(dataset_path, output_path)
                
                assert "--nthreads" in cmd
                assert "4" in cmd[cmd.index("--nthreads") + 1]
                assert "--mem-mb" in cmd
                assert "4096" in cmd[cmd.index("--mem-mb") + 1]

    def test_participant_label_included(self):
        """Test that participant label is included when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset"
            output_path = Path(tmpdir) / "output"
            dataset_path.mkdir()
            
            cmd = build_fmriprep_command(
                dataset_path, 
                output_path, 
                participant_label="sub-01"
            )
            
            assert "--participant-label=sub-01" in cmd

    def test_skip_bids_validation_flag(self):
        """Test that skip-bids-validation flag is included when requested."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "dataset"
            output_path = Path(tmpdir) / "output"
            dataset_path.mkdir()
            
            cmd = build_fmriprep_command(
                dataset_path, 
                output_path, 
                skip_bids_validation=True
            )
            
            assert "--skip-bids-validation" in cmd

    def test_nonexistent_dataset_raises_error(self):
        """Test that a nonexistent dataset path raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "nonexistent"
            output_path = Path(tmpdir) / "output"
            
            with pytest.raises(FMRIPrepRunnerError):
                build_fmriprep_command(dataset_path, output_path)

class TestRunFMRIPrep:
    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.exists', return_value=True)
    def test_successful_run(self, mock_exists, mock_get_data_dir, mock_run):
        """Test successful execution of fMRIPrep."""
        mock_get_data_dir.return_value = "/tmp/data"
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
        
        result = run_fmriprep("ds000001", participant_label="sub-01")
        
        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.exists', return_value=True)
    def test_failed_run_raises_error(self, mock_exists, mock_get_data_dir, mock_run):
        """Test that a failed run raises FMRIPrepRunnerError."""
        mock_get_data_dir.return_value = "/tmp/data"
        mock_run.return_value = MagicMock(
            returncode=1, 
            stdout="Error output", 
            stderr="Error details"
        )
        
        with pytest.raises(FMRIPrepRunnerError):
            run_fmriprep("ds000001")

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.exists', return_value=False)
    def test_missing_dataset_raises_error(self, mock_exists, mock_get_data_dir, mock_run):
        """Test that missing dataset raises appropriate error."""
        mock_get_data_dir.return_value = "/tmp/data"
        
        with pytest.raises(FMRIPrepRunnerError):
            run_fmriprep("ds000001")

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.exists', return_value=True)
    def test_docker_not_found_raises_error(self, mock_exists, mock_get_data_dir, mock_run):
        """Test that missing Docker executable raises appropriate error."""
        mock_get_data_dir.return_value = "/tmp/data"
        mock_run.side_effect = FileNotFoundError("Docker not found")
        
        with pytest.raises(FMRIPrepRunnerError):
            run_fmriprep("ds000001")

    @patch('src.preprocessing.fmriprep_runner.subprocess.run')
    @patch('src.preprocessing.fmriprep_runner.get_data_dir')
    @patch('pathlib.Path.exists', return_value=True)
    def test_timeout_raises_error(self, mock_exists, mock_get_data_dir, mock_run):
        """Test that timeout raises appropriate error."""
        mock_get_data_dir.return_value = "/tmp/data"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=7200)
        
        with pytest.raises(FMRIPrepRunnerError):
            run_fmriprep("ds000001")

class TestMain:
    @patch('sys.argv', ['fmriprep_runner.py', 'ds000001'])
    @patch('src.preprocessing.fmriprep_runner.run_fmriprep')
    def test_main_with_dataset_id(self, mock_run):
        """Test main function with dataset ID argument."""
        main()
        mock_run.assert_called_once()
        
    @patch('sys.argv', ['fmriprep_runner.py'])
    @patch('src.preprocessing.fmriprep_runner.logger')
    def test_main_without_arguments_exits(self, mock_logger):
        """Test main function exits gracefully without arguments."""
        with pytest.raises(SystemExit):
            main()
        
    @patch('sys.argv', ['fmriprep_runner.py', 'ds000001', 'sub-01'])
    @patch('src.preprocessing.fmriprep_runner.run_fmriprep')
    def test_main_with_participant_label(self, mock_run):
        """Test main function with participant label."""
        main()
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]['participant_label'] == 'sub-01'