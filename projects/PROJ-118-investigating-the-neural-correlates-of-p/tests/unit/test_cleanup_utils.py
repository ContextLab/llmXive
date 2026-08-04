"""
Unit tests for cleanup_utils module.

These tests verify the utility functions used across the pipeline
for logging, validation, and cleanup operations.
"""
import pytest
import numpy as np
from pathlib import Path
import logging
import tempfile
import os

from cleanup_utils import (
    setup_logger,
    validate_array_shape,
    safe_divide,
    cleanup_mne_cache,
    log_execution_time,
    validate_pipeline_config,
    find_files_by_extension,
    get_memory_usage_gb
)


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_console_only(self, tmp_path):
        """Test logger creation with only console output."""
        logger = setup_logger("test_console", level=logging.DEBUG)
        assert logger.name == "test_console"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0
        # Verify console handler exists
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_setup_logger_with_file(self, tmp_path):
        """Test logger creation with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=str(log_file), level=logging.INFO)
        assert logger.name == "test_file"

        # Verify file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_setup_logger_idempotent(self):
        """Test that calling setup_logger multiple times doesn't duplicate handlers."""
        logger = setup_logger("test_idempotent", level=logging.INFO)
        initial_count = len(logger.handlers)
        # Call again with same name
        logger2 = setup_logger("test_idempotent", level=logging.DEBUG)
        # Should have same handlers (not duplicated)
        assert len(logger2.handlers) == initial_count


class TestValidateArrayShape:
    """Tests for validate_array_shape function."""

    def test_valid_array(self):
        """Test validation of a correctly shaped array."""
        arr = np.array([1, 2, 3, 4, 5])
        assert validate_array_shape(arr, min_dims=1, max_dims=1) is True

    def test_valid_2d_array(self):
        """Test validation of a 2D array."""
        arr = np.array([[1, 2], [3, 4]])
        assert validate_array_shape(arr, min_dims=2, max_dims=2) is True

    def test_valid_3d_array(self):
        """Test validation of a 3D array."""
        arr = np.random.rand(10, 20, 30)
        assert validate_array_shape(arr, min_dims=1, max_dims=3) is True

    def test_invalid_dimension_count(self):
        """Test that wrong dimension count raises ValueError."""
        arr = np.array([1, 2, 3])
        with pytest.raises(ValueError, match="dimensions"):
            validate_array_shape(arr, min_dims=2, max_dims=2)

    def test_invalid_shape(self):
        """Test that wrong shape raises ValueError."""
        arr = np.array([[1, 2], [3, 4]])
        with pytest.raises(ValueError, match="shape"):
            validate_array_shape(arr, expected_shape=(3, 3))

    def test_none_array(self):
        """Test that None array raises ValueError."""
        with pytest.raises(ValueError, match="None"):
            validate_array_shape(None)

    def test_non_numpy_array(self):
        """Test that non-numpy array raises TypeError."""
        with pytest.raises(TypeError):
            validate_array_shape([1, 2, 3])


class TestSafeDivide:
    """Tests for safe_divide function."""

    def test_normal_division(self):
        """Test normal division operation."""
        assert safe_divide(10, 2) == 5.0

    def test_division_by_zero(self):
        """Test that division by zero returns default."""
        assert safe_divide(10, 0) == 0.0

    def test_division_by_zero_custom_default(self):
        """Test division by zero with custom default value."""
        assert safe_divide(10, 0, default=-1.0) == -1.0

    def test_float_division(self):
        """Test float division."""
        assert abs(safe_divide(7, 3) - 2.333333) < 0.0001


class TestCleanupMneCache:
    """Tests for cleanup_mne_cache function."""

    def test_cleanup_nonexistent_directory(self):
        """Test cleanup on non-existent directory returns 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_cache = Path(tmpdir) / "nonexistent" / "cache"
            removed = cleanup_mne_cache(str(fake_cache))
            assert removed == 0

    def test_cleanup_empty_directory(self, tmp_path):
        """Test cleanup on empty directory returns 0."""
        removed = cleanup_mne_cache(str(tmp_path))
        assert removed == 0

    def test_cleanup_with_files(self, tmp_path):
        """Test cleanup removes files."""
        # Create some files
        (tmp_path / "file1.txt").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").touch()

        removed = cleanup_mne_cache(str(tmp_path))
        assert removed == 2
        # Verify files are gone
        assert not (tmp_path / "file1.txt").exists()


class TestLogExecutionTime:
    """Tests for log_execution_time decorator."""

    def test_decorator_executes_function(self):
        """Test that decorator allows function to execute."""
        @log_execution_time
        def simple_func():
            return 42

        result = simple_func()
        assert result == 42

    def test_decorator_logs_time(self, caplog):
        """Test that decorator logs execution time."""
        @log_execution_time
        def slow_func():
            time.sleep(0.1)
            return "done"

        with caplog.at_level(logging.INFO):
            result = slow_func()

        assert result == "done"
        assert "executed in" in caplog.text


class TestValidatePipelineConfig:
    """Tests for validate_pipeline_config function."""

    def test_valid_config(self):
        """Test validation of a complete valid config."""
        config = {
            'filter': {'lowcut': 1.0, 'highcut': 30.0},
            'epoch': {'tmin': -0.2, 'tmax': 0.5},
            'ica': {'n_components': 0.95},
            'channels': ['Fz', 'Cz']
        }
        assert validate_pipeline_config(config) is True

    def test_missing_filter_key(self):
        """Test validation fails when filter is missing."""
        config = {
            'epoch': {'tmin': -0.2, 'tmax': 0.5},
            'ica': {'n_components': 0.95},
            'channels': ['Fz', 'Cz']
        }
        with pytest.raises(ValueError, match="missing required key"):
            validate_pipeline_config(config)

    def test_invalid_filter_lowcut_highcut(self):
        """Test validation fails when lowcut >= highcut."""
        config = {
            'filter': {'lowcut': 30.0, 'highcut': 1.0},
            'epoch': {'tmin': -0.2, 'tmax': 0.5},
            'ica': {'n_components': 0.95},
            'channels': ['Fz', 'Cz']
        }
        with pytest.raises(ValueError, match="lowcut must be less than highcut"):
            validate_pipeline_config(config)

    def test_missing_epoch_keys(self):
        """Test validation fails when epoch keys are missing."""
        config = {
            'filter': {'lowcut': 1.0, 'highcut': 30.0},
            'epoch': {'tmin': -0.2},  # Missing tmax
            'ica': {'n_components': 0.95},
            'channels': ['Fz', 'Cz']
        }
        with pytest.raises(ValueError, match="must contain"):
            validate_pipeline_config(config)

    def test_invalid_ica_n_components(self):
        """Test validation fails with invalid n_components."""
        config = {
            'filter': {'lowcut': 1.0, 'highcut': 30.0},
            'epoch': {'tmin': -0.2, 'tmax': 0.5},
            'ica': {'n_components': -1},
            'channels': ['Fz', 'Cz']
        }
        with pytest.raises(ValueError, match="positive number"):
            validate_pipeline_config(config)


class TestFindFilesByExtension:
    """Tests for find_files_by_extension function."""

    def test_find_fif_files(self, tmp_path):
        """Test finding .fif files."""
        # Create test files
        (tmp_path / "data1.fif").touch()
        (tmp_path / "data2.fif").touch()
        (tmp_path / "data3.txt").touch()

        results = find_files_by_extension(tmp_path, ".fif")
        assert len(results) == 2
        assert all(str(r).endswith(".fif") for r in results)

    def test_find_in_subdirectory(self, tmp_path):
        """Test finding files in subdirectories."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.fif").touch()

        results = find_files_by_extension(tmp_path, ".fif")
        assert len(results) == 1
        assert "nested.fif" in str(results[0])

    def test_nonexistent_directory(self, tmp_path):
        """Test finding files in non-existent directory."""
        fake_dir = tmp_path / "nonexistent"
        results = find_files_by_extension(fake_dir, ".fif")
        assert results == []


class TestGetMemoryUsage:
    """Tests for get_memory_usage_gb function."""

    def test_returns_positive_value(self):
        """Test that memory usage is a positive number."""
        mem = get_memory_usage_gb()
        assert isinstance(mem, float)
        assert mem > 0


class TestCleanupUtilsIntegration:
    """Integration tests for cleanup_utils module."""

    def test_combined_workflow(self, tmp_path):
        """Test a workflow combining multiple utilities."""
        # Set up logger
        log_file = tmp_path / "workflow.log"
        logger = setup_logger("workflow", log_file=str(log_file))

        # Validate config
        config = {
            'filter': {'lowcut': 1.0, 'highcut': 30.0},
            'epoch': {'tmin': -0.2, 'tmax': 0.5},
            'ica': {'n_components': 0.95},
            'channels': ['Fz', 'Cz']
        }
        validate_pipeline_config(config)

        # Create test data
        data = np.random.rand(100, 10)
        validate_array_shape(data, min_dims=2, max_dims=2)

        # Safe division
        ratio = safe_divide(100, 10)
        assert ratio == 10.0

        # Check memory
        mem = get_memory_usage_gb()
        assert mem > 0

        # Verify log file was created
        assert log_file.exists()