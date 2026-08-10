"""
Unit tests for T022e: generate_eval_tasks.py
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.generate_eval_tasks import (
    validate_raw_data_exists,
    generate_task_ids,
    save_eval_tasks,
    main,
    K_VALUES,
    ALFWORLD_TASKS,
    SEARCHQA_TASKS,
    COMPOSITE_TASKS
)

class TestValidateRawDataExists:
    """Tests for validate_raw_data_exists function."""

    def test_validate_raw_data_exists_missing_directory(self, tmp_path):
        """Test validation fails when raw data directory doesn't exist."""
        with patch('src.validation.generate_eval_tasks.RAW_DATA_DIR', tmp_path / "nonexistent"):
            with patch('src.validation.generate_eval_tasks.logger') as mock_logger:
                result = validate_raw_data_exists()
                assert result is False
                mock_logger.error.assert_called()

    def test_validate_raw_data_exists_missing_files(self, tmp_path):
        """Test validation fails when expected weight files are missing."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        with patch('src.validation.generate_eval_tasks.RAW_DATA_DIR', raw_dir):
            with patch('src.validation.generate_eval_tasks.logger') as mock_logger:
                result = validate_raw_data_exists()
                assert result is False
                mock_logger.error.assert_called()

    def test_validate_raw_data_exists_success(self, tmp_path):
        """Test validation succeeds when all files exist."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        # Create expected files
        (raw_dir / "alfworld_weights.npz").touch()
        (raw_dir / "searchqa_weights.npz").touch()

        with patch('src.validation.generate_eval_tasks.RAW_DATA_DIR', raw_dir):
            with patch('src.validation.generate_eval_tasks.logger') as mock_logger:
                result = validate_raw_data_exists()
                assert result is True

class TestGenerateTaskIds:
    """Tests for generate_task_ids function."""

    def test_generate_task_ids_returns_list(self):
        """Test that generate_task_ids returns a list."""
        tasks = generate_task_ids()
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_generate_task_ids_contains_expected_fields(self):
        """Test that each task has required fields."""
        tasks = generate_task_ids()

        required_fields = ["task_id", "task_type", "benchmark", "description", "sensitivity_k_values"]

        for task in tasks:
            for field in required_fields:
                assert field in task, f"Missing field: {field}"

    def test_generate_task_ids_correct_count(self):
        """Test that the correct number of tasks is generated."""
        tasks = generate_task_ids()
        expected_count = len(ALFWORLD_TASKS) + len(SEARCHQA_TASKS) + len(COMPOSITE_TASKS)
        assert len(tasks) == expected_count

    def test_generate_task_ids_base_tasks(self):
        """Test that base tasks have correct type."""
        tasks = generate_task_ids()
        base_tasks = [t for t in tasks if t["task_type"] == "base"]
        assert len(base_tasks) == len(ALFWORLD_TASKS) + len(SEARCHQA_TASKS)

    def test_generate_task_ids_composite_tasks(self):
        """Test that composite tasks have correct type."""
        tasks = generate_task_ids()
        composite_tasks = [t for t in tasks if t["task_type"] == "composite"]
        assert len(composite_tasks) == len(COMPOSITE_TASKS)

    def test_generate_task_ids_k_values(self):
        """Test that each task has the correct k_values."""
        tasks = generate_task_ids()

        for task in tasks:
            assert task["sensitivity_k_values"] == K_VALUES

    def test_generate_task_ids_benchmarks(self):
        """Test that tasks have correct benchmark assignments."""
        tasks = generate_task_ids()

        alfworld_tasks = [t for t in tasks if t["benchmark"] == "alfworld"]
        searchqa_tasks = [t for t in tasks if t["benchmark"] == "searchqa"]
        composite_tasks = [t for t in tasks if t["benchmark"] == "interpolated"]

        assert len(alfworld_tasks) == len(ALFWORLD_TASKS)
        assert len(searchqa_tasks) == len(SEARCHQA_TASKS)
        assert len(composite_tasks) == len(COMPOSITE_TASKS)

class TestSaveEvalTasks:
    """Tests for save_eval_tasks function."""

    def test_save_eval_tasks_creates_file(self, tmp_path):
        """Test that save_eval_tasks creates the output file."""
        tasks = generate_task_ids()

        output_file = tmp_path / "eval_tasks.yaml"

        with patch('src.validation.generate_eval_tasks.PROCESSED_DATA_DIR', tmp_path):
            with patch('src.validation.generate_eval_tasks.OUTPUT_FILE', output_file):
                save_eval_tasks(tasks)

                assert output_file.exists()

    def test_save_eval_tasks_valid_yaml(self, tmp_path):
        """Test that the saved file is valid YAML."""
        tasks = generate_task_ids()

        output_file = tmp_path / "eval_tasks.yaml"

        with patch('src.validation.generate_eval_tasks.PROCESSED_DATA_DIR', tmp_path):
            with patch('src.validation.generate_eval_tasks.OUTPUT_FILE', output_file):
                save_eval_tasks(tasks)

                with open(output_file, 'r') as f:
                    data = yaml.safe_load(f)

                assert "metadata" in data
                assert "tasks" in data
                assert isinstance(data["tasks"], list)

    def test_save_eval_tasks_metadata(self, tmp_path):
        """Test that the saved file contains correct metadata."""
        tasks = generate_task_ids()

        output_file = tmp_path / "eval_tasks.yaml"

        with patch('src.validation.generate_eval_tasks.PROCESSED_DATA_DIR', tmp_path):
            with patch('src.validation.generate_eval_tasks.OUTPUT_FILE', output_file):
                save_eval_tasks(tasks)

                with open(output_file, 'r') as f:
                    data = yaml.safe_load(f)

                metadata = data["metadata"]
                assert "generated_by" in metadata
                assert "purpose" in metadata
                assert "k_values" in metadata
                assert metadata["k_values"] == K_VALUES
                assert metadata["total_tasks"] == len(tasks)

class TestMain:
    """Tests for main function."""

    def test_main_success(self, tmp_path):
        """Test that main returns 0 on success."""
        # Create mock raw data directory
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        (raw_dir / "alfworld_weights.npz").touch()
        (raw_dir / "searchqa_weights.npz").touch()

        with patch('src.validation.generate_eval_tasks.RAW_DATA_DIR', raw_dir):
            with patch('src.validation.generate_eval_tasks.PROCESSED_DATA_DIR', tmp_path / "processed"):
                with patch('src.validation.generate_eval_tasks.OUTPUT_FILE', tmp_path / "processed" / "eval_tasks.yaml"):
                    result = main()
                    assert result == 0

    def test_main_failure_missing_data(self, tmp_path):
        """Test that main returns 1 when raw data is missing."""
        with patch('src.validation.generate_eval_tasks.RAW_DATA_DIR', tmp_path / "nonexistent"):
            result = main()
            assert result == 1