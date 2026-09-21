"""
Unit tests for cleanup and refactoring utilities.
"""
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from refactor.cleanup_utils import (
    ensure_output_directories,
    validate_environment,
    cleanup_temp_files,
    setup_pipeline_logger,
    validate_config_consistency,
    generate_config_report,
    run_cleanup
)
from utils.config import Config, get_config, reset_config

class TestEnsureOutputDirectories:
    def test_creates_missing_directories(self, tmp_path):
        """Test that missing directories are created."""
        # Create a temporary config
        config = Config()
        config.output_paths.raw_dir = str(tmp_path / "raw")
        config.output_paths.processed_dir = str(tmp_path / "processed")
        config.output_paths.artifacts_dir = str(tmp_path / "artifacts")
        config.output_paths.logs_dir = str(tmp_path / "logs")
        config.output_paths.behavioral_dir = str(tmp_path / "behavioral")
        config.output_paths.centrality_dir = str(tmp_path / "centrality")
        config.output_paths.regression_dir = str(tmp_path / "regression")
        config.output_paths.validation_dir = str(tmp_path / "validation")
        config.output_paths.figures_dir = str(tmp_path / "figures")
        config.output_paths.temp_dir = str(tmp_path / "temp")
        
        # Ensure directories exist
        ensure_output_directories(config)
        
        # Verify all directories were created
        assert tmp_path.joinpath("raw").exists()
        assert tmp_path.joinpath("processed").exists()
        assert tmp_path.joinpath("artifacts").exists()
        assert tmp_path.joinpath("logs").exists()
        
        # Verify they are directories
        assert tmp_path.joinpath("raw").is_dir()
        assert tmp_path.joinpath("processed").is_dir()

    def test_does_not_fail_if_exists(self, tmp_path):
        """Test that existing directories don't cause errors."""
        # Pre-create a directory
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        config = Config()
        config.output_paths.raw_dir = str(existing_dir)
        config.output_paths.processed_dir = str(tmp_path / "processed")
        config.output_paths.artifacts_dir = str(tmp_path / "artifacts")
        config.output_paths.logs_dir = str(tmp_path / "logs")
        config.output_paths.behavioral_dir = str(tmp_path / "behavioral")
        config.output_paths.centrality_dir = str(tmp_path / "centrality")
        config.output_paths.regression_dir = str(tmp_path / "regression")
        config.output_paths.validation_dir = str(tmp_path / "validation")
        config.output_paths.figures_dir = str(tmp_path / "figures")
        config.output_paths.temp_dir = str(tmp_path / "temp")
        
        # Should not raise
        ensure_output_directories(config)
        
        assert existing_dir.exists()

class TestValidateEnvironment:
    def test_valid_environment(self, tmp_path, monkeypatch):
        """Test validation passes with correct environment."""
        monkeypatch.setenv("DATASET_URL", "http://example.com")
        
        config = Config()
        config.output_paths.raw_dir = str(tmp_path / "raw")
        config.output_paths.processed_dir = str(tmp_path / "processed")
        config.output_paths.artifacts_dir = str(tmp_path / "artifacts")
        
        # Create required directories
        tmp_path.joinpath("raw").mkdir()
        tmp_path.joinpath("processed").mkdir()
        tmp_path.joinpath("artifacts").mkdir()
        
        with patch('refactor.cleanup_utils.get_config', return_value=config):
            result = validate_environment()
            
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_directory(self, tmp_path, monkeypatch):
        """Test validation fails when required directory is missing."""
        monkeypatch.setenv("DATASET_URL", "http://example.com")
        
        config = Config()
        config.output_paths.raw_dir = str(tmp_path / "raw")
        config.output_paths.processed_dir = str(tmp_path / "missing")
        config.output_paths.artifacts_dir = str(tmp_path / "artifacts")
        
        # Only create some directories
        tmp_path.joinpath("raw").mkdir()
        tmp_path.joinpath("artifacts").mkdir()
        
        with patch('refactor.cleanup_utils.get_config', return_value=config):
            result = validate_environment()
            
        assert result["valid"] is False
        assert any("missing" in err.lower() for err in result["errors"])

class TestCleanupTempFiles:
    def test_removes_files(self, tmp_path):
        """Test that temp files are removed."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        # Create some temp files
        (temp_dir / "file1.tmp").touch()
        (temp_dir / "file2.tmp").touch()
        (temp_dir / "file3.tmp").touch()
        
        removed = cleanup_temp_files(str(temp_dir))
        
        assert removed == 3
        assert not (temp_dir / "file1.tmp").exists()
        assert not (temp_dir / "file2.tmp").exists()
        assert not (temp_dir / "file3.tmp").exists()

    def test_ignores_directories(self, tmp_path):
        """Test that subdirectories are not removed."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        # Create a file and a directory
        (temp_dir / "file.tmp").touch()
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.tmp").touch()
        
        removed = cleanup_temp_files(str(temp_dir))
        
        assert removed == 1
        assert (temp_dir / "subdir").exists()
        assert (subdir / "nested.tmp").exists()

    def test_empty_directory(self, tmp_path):
        """Test handling of empty temp directory."""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        removed = cleanup_temp_files(str(temp_dir))
        assert removed == 0

    def test_nonexistent_directory(self, tmp_path):
        """Test handling of non-existent directory."""
        removed = cleanup_temp_files(str(tmp_path / "nonexistent"))
        assert removed == 0

class TestValidateConfigConsistency:
    def test_valid_config(self):
        """Test validation passes with valid config."""
        config = Config()
        config.centrality.vif_threshold = 5.0
        config.validation.permutation_shuffles = 1000
        config.validation.permutation_seed = 42
        
        with patch('refactor.cleanup_utils.get_config', return_value=config):
            result = validate_config_consistency()
        
        assert result is True

    def test_invalid_vif_threshold(self):
        """Test validation fails with invalid VIF threshold."""
        config = Config()
        config.centrality.vif_threshold = 0.5  # Invalid
        config.validation.permutation_shuffles = 1000
        
        with patch('refactor.cleanup_utils.get_config', return_value=config):
            result = validate_config_consistency()
        
        assert result is False

    def test_invalid_permutation_seed(self):
        """Test validation fails with invalid permutation seed."""
        config = Config()
        config.centrality.vif_threshold = 5.0
        config.validation.permutation_shuffles = 1000
        config.validation.permutation_seed = "invalid"
        
        with patch('refactor.cleanup_utils.get_config', return_value=config):
            result = validate_config_consistency()
        
        assert result is False

class TestGenerateConfigReport:
    def test_generates_json_string(self):
        """Test that config report is valid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            json_str = generate_config_report(output_path)
            
            # Verify it's valid JSON
            parsed = json.loads(json_str)
            assert "dataset" in parsed
            assert "preprocessing" in parsed
            assert "centrality" in parsed
            
            # Verify file was written
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                file_content = f.read()
            assert json.loads(file_content) == parsed
        finally:
            os.unlink(output_path)

    def test_returns_json_without_writing(self):
        """Test that function returns JSON string without writing file."""
        json_str = generate_config_report()
        
        parsed = json.loads(json_str)
        assert "dataset" in parsed
        assert isinstance(json_str, str)

class TestRunCleanup:
    @patch('refactor.cleanup_utils.validate_environment')
    @patch('refactor.cleanup_utils.cleanup_temp_files')
    @patch('refactor.cleanup_utils.validate_config_consistency')
    def test_successful_cleanup(self, mock_validate_config, mock_cleanup, mock_validate_env):
        """Test successful cleanup execution."""
        mock_validate_env.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_cleanup.return_value = 5
        mock_validate_config.return_value = True
        
        # Should not raise
        run_cleanup()
        
        mock_validate_env.assert_called_once()
        mock_cleanup.assert_called_once()
        mock_validate_config.assert_called_once()

    @patch('refactor.cleanup_utils.validate_environment')
    def test_fails_on_invalid_env(self, mock_validate_env):
        """Test cleanup fails when environment is invalid."""
        mock_validate_env.return_value = {
            "valid": False,
            "errors": ["Missing directory"],
            "warnings": []
        }
        
        with pytest.raises(RuntimeError, match="Environment validation failed"):
            run_cleanup()

    @patch('refactor.cleanup_utils.validate_environment')
    @patch('refactor.cleanup_utils.cleanup_temp_files')
    @patch('refactor.cleanup_utils.validate_config_consistency')
    def test_fails_on_invalid_config(self, mock_validate_config, mock_cleanup, mock_validate_env):
        """Test cleanup fails when config is invalid."""
        mock_validate_env.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_cleanup.return_value = 0
        mock_validate_config.return_value = False
        
        with pytest.raises(RuntimeError, match="Configuration consistency check failed"):
            run_cleanup()