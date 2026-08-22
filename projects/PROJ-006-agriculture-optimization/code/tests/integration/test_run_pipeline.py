"""
Integration tests for the pipeline orchestrator (run_pipeline.py).
Tests the automatic synthetic data fallback mechanism.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from src.cli.run_pipeline import check_and_generate_synthetic_data, run_pipeline, main
from src.utils.io_helpers import FatalError
from src.data.generators.synthetic_generator import SyntheticDataGenerator


class TestPipelineSyntheticFallback:
    """Tests for automatic synthetic data fallback in CI environments."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root with required directory structure."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create required directories
        (project_root / "data" / "raw").mkdir(parents=True)
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "data" / "logs").mkdir(parents=True)
        (project_root / "state" / "projects").mkdir(parents=True)
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_real_data_exists_no_synthetic(self, temp_project_root):
        """Test that synthetic data is NOT generated when real data exists."""
        # Create a dummy real data file
        real_data_file = temp_project_root / "data" / "raw" / "survey_data.csv"
        real_data_file.write_text("household_id,latitude,longitude\n1,12.3,45.6\n")
        
        # Mock the check_real_data_exists function to return True
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=True):
            result = check_and_generate_synthetic_data(temp_project_root, no_synthetic=False)
            
            assert result is False, "Should return False when real data exists"

    def test_missing_data_ci_no_flag(self, temp_project_root):
        """Test automatic synthetic generation in CI when data is missing and no --no-synthetic flag."""
        # Ensure no real data exists
        assert not (temp_project_root / "data" / "raw").glob("*")
        
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=False):
            with patch('src.cli.run_pipeline.SyntheticDataGenerator.generate') as mock_generate:
                # Set CI environment variable
                with patch.dict(os.environ, {"CI": "true"}):
                    result = check_and_generate_synthetic_data(temp_project_root, no_synthetic=False)
                    
                    assert result is True, "Should return True when synthetic data is generated"
                    mock_generate.assert_called_once_with(temp_project_root)

    def test_missing_data_ci_no_synthetic_flag(self, temp_project_root):
        """Test that FatalError is raised in CI when data is missing and --no-synthetic flag is provided."""
        assert not (temp_project_root / "data" / "raw").glob("*")
        
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=False):
            with patch.dict(os.environ, {"CI": "true"}):
                with pytest.raises(FatalError) as exc_info:
                    check_and_generate_synthetic_data(temp_project_root, no_synthetic=True)
                
                assert "no-synthetic" in str(exc_info.value).lower()

    def test_missing_data_not_ci_no_flag(self, temp_project_root):
        """Test that FatalError is raised when data is missing, not in CI, and no --no-synthetic flag."""
        assert not (temp_project_root / "data" / "raw").glob("*")
        
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(FatalError) as exc_info:
                    check_and_generate_synthetic_data(temp_project_root, no_synthetic=False)
                
                assert "real data is missing" in str(exc_info.value).lower()

    def test_missing_data_not_ci_no_synthetic_flag(self, temp_project_root):
        """Test that FatalError is raised when data is missing, not in CI, and --no-synthetic flag is provided."""
        assert not (temp_project_root / "data" / "raw").glob("*")
        
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(FatalError) as exc_info:
                    check_and_generate_synthetic_data(temp_project_root, no_synthetic=True)
                
                assert "real data is missing" in str(exc_info.value).lower()

    def test_dry_run_mode(self, temp_project_root):
        """Test that dry run mode validates data availability without processing."""
        # Create dummy real data
        real_data_file = temp_project_root / "data" / "raw" / "survey_data.csv"
        real_data_file.write_text("household_id,latitude,longitude\n1,12.3,45.6\n")
        
        success = run_pipeline(
            project_root=temp_project_root,
            dry_run=True,
            no_synthetic=False,
            skip_ingestion=False,
            skip_analysis=False
        )
        
        assert success is True

    def test_pipeline_execution_flow(self, temp_project_root):
        """Test the full pipeline execution flow with synthetic data generation."""
        assert not (temp_project_root / "data" / "raw").glob("*")
        
        with patch('src.cli.run_pipeline.check_real_data_exists', return_value=False):
            with patch('src.cli.run_pipeline.SyntheticDataGenerator.generate') as mock_generate:
                with patch.dict(os.environ, {"CI": "true"}):
                    success = run_pipeline(
                        project_root=temp_project_root,
                        dry_run=False,
                        no_synthetic=False,
                        skip_ingestion=False,
                        skip_analysis=False
                    )
                    
                    assert success is True
                    mock_generate.assert_called_once_with(temp_project_root)


class TestPipelineCLI:
    """Tests for the CLI argument parsing and main function."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        (project_root / "data" / "raw").mkdir(parents=True)
        yield project_root
        shutil.rmtree(temp_dir)

    def test_main_with_dry_run(self, temp_project_root, capsys):
        """Test main function with --dry-run flag."""
        with patch('sys.argv', ['run_pipeline.py', '--dry-run', '--project-root', str(temp_project_root)]):
            with patch('src.cli.run_pipeline.run_pipeline', return_value=True) as mock_run:
                main()
                
                mock_run.assert_called_once()
                call_args = mock_run.call_args[1]
                assert call_args['dry_run'] is True

    def test_main_with_no_synthetic(self, temp_project_root):
        """Test main function with --no-synthetic flag."""
        with patch('sys.argv', ['run_pipeline.py', '--no-synthetic', '--project-root', str(temp_project_root)]):
            with patch('src.cli.run_pipeline.run_pipeline', return_value=True) as mock_run:
                main()
                
                mock_run.assert_called_once()
                call_args = mock_run.call_args[1]
                assert call_args['no_synthetic'] is True

    def test_main_with_invalid_project_root(self, tmp_path):
        """Test main function with non-existent project root."""
        invalid_path = tmp_path / "nonexistent"
        
        with patch('sys.argv', ['run_pipeline.py', '--project-root', str(invalid_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 1

    def test_main_with_skip_flags(self, temp_project_root):
        """Test main function with --skip-ingestion and --skip-analysis flags."""
        with patch('sys.argv', [
            'run_pipeline.py', 
            '--skip-ingestion', 
            '--skip-analysis', 
            '--project-root', str(temp_project_root)
        ]):
            with patch('src.cli.run_pipeline.run_pipeline', return_value=True) as mock_run:
                main()
                
                mock_run.assert_called_once()
                call_args = mock_run.call_args[1]
                assert call_args['skip_ingestion'] is True
                assert call_args['skip_analysis'] is True
