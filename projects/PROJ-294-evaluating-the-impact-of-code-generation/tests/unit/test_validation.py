"""
Unit tests for validation utilities (T039).
Tests the validate_quickstart.py script components.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
import sys
sys.path.insert(0, str(code_dir))

from utils import compute_sha256, ensure_directory


class TestDirectoryValidation:
    """Tests for directory existence checks."""

    def test_check_directory_exists(self, tmp_path):
        """Verify check_directory returns True for existing directory."""
        from validate_quickstart import check_directory
        result = check_directory(tmp_path, "test directory")
        assert result is True

    def test_check_directory_missing(self, tmp_path):
        """Verify check_directory returns False for missing directory."""
        from validate_quickstart import check_directory
        missing_dir = tmp_path / "nonexistent"
        result = check_directory(missing_dir, "missing directory")
        assert result is False


class TestFileValidation:
    """Tests for file existence and size checks."""

    def test_check_file_exists(self, tmp_path):
        """Verify check_file returns True for existing file."""
        from validate_quickstart import check_file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        result = check_file(test_file, "test file")
        assert result is True

    def test_check_file_missing(self, tmp_path):
        """Verify check_file returns False for missing file."""
        from validate_quickstart import check_file
        missing_file = tmp_path / "nonexistent.txt"
        result = check_file(missing_file, "missing file")
        assert result is False

    def test_check_file_size_too_small(self, tmp_path):
        """Verify check_file returns False when file is too small."""
        from validate_quickstart import check_file
        test_file = tmp_path / "small.txt"
        test_file.write_text("x")  # 1 byte
        result = check_file(test_file, "small file", min_size=100)
        assert result is False


class TestJSONValidation:
    """Tests for JSON structure validation."""

    def test_verify_json_list_with_required_keys(self, tmp_path):
        """Verify JSON list with required keys passes validation."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        data = [
            {"task_id": "1", "value": 10},
            {"task_id": "2", "value": 20}
        ]
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["task_id", "value"], "test list")
        assert result is True

    def test_verify_json_list_missing_keys(self, tmp_path):
        """Verify JSON list missing required keys fails validation."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        data = [{"task_id": "1"}]  # Missing 'value'
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["task_id", "value"], "test list")
        assert result is False

    def test_verify_json_empty_list(self, tmp_path):
        """Verify empty JSON list fails validation."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        test_file.write_text("[]")
        result = verify_json_structure(test_file, ["task_id"], "empty list")
        assert result is False

    def test_verify_json_dict_with_required_keys(self, tmp_path):
        """Verify JSON dict with required keys passes validation."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        data = {"summary": "test", "count": 5}
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["summary", "count"], "test dict")
        assert result is True


class TestMetricsValidation:
    """Tests for metrics.json specific validation."""

    def test_metrics_json_structure(self, tmp_path):
        """Verify metrics.json has all required fields."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "metrics.json"
        required_keys = [
            "task_id", "cyclomatic_complexity", "halstead_volume",
            "branch_coverage_pct", "pass_rate"
        ]
        data = [{key: 0 for key in required_keys}]
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, required_keys, "metrics.json")
        assert result is True

    def test_metrics_json_insufficient_samples(self, tmp_path):
        """Verify metrics.json with <40 samples triggers warning."""
        # This is tested in the main validation logic
        # Here we just verify the structure check works
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "metrics.json"
        data = [{"task_id": "1", "value": 1}] * 39  # Less than 40
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["task_id", "value"], "metrics.json")
        assert result is True  # Structure is valid, count check is separate


class TestPipelineStageValidation:
    """Tests for pipeline stage execution validation."""

    def test_run_pipeline_stage_success(self, tmp_path):
        """Verify run_pipeline_stage returns True for successful script."""
        from validate_quickstart import run_pipeline_stage
        # Create a simple successful script
        script = tmp_path / "success.py"
        script.write_text("import sys; sys.exit(0)")
        # Mock the code_dir
        import validate_quickstart
        original_code_dir = validate_quickstart.code_dir
        validate_quickstart.code_dir = tmp_path
        result = run_pipeline_stage("success.py", "test stage")
        validate_quickstart.code_dir = original_code_dir
        assert result is True

    def test_run_pipeline_stage_failure(self, tmp_path):
        """Verify run_pipeline_stage returns False for failed script."""
        from validate_quickstart import run_pipeline_stage
        script = tmp_path / "fail.py"
        script.write_text("import sys; sys.exit(1)")
        import validate_quickstart
        original_code_dir = validate_quickstart.code_dir
        validate_quickstart.code_dir = tmp_path
        result = run_pipeline_stage("fail.py", "test stage")
        validate_quickstart.code_dir = original_code_dir
        assert result is False

    def test_run_pipeline_stage_missing(self, tmp_path):
        """Verify run_pipeline_stage returns False for missing script."""
        from validate_quickstart import run_pipeline_stage
        import validate_quickstart
        original_code_dir = validate_quickstart.code_dir
        validate_quickstart.code_dir = tmp_path
        result = run_pipeline_stage("nonexistent.py", "test stage")
        validate_quickstart.code_dir = original_code_dir
        assert result is False


class TestSHA256Validation:
    """Tests for SHA256 checksum utilities."""

    def test_compute_sha256_file(self):
        """Verify SHA256 computation for a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        try:
            hash1 = compute_sha256(temp_path)
            hash2 = compute_sha256(temp_path)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_content_changes(self):
        """Verify SHA256 changes with content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("content1")
            temp_path1 = f.name
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("content2")
            temp_path2 = f.name
        try:
            hash1 = compute_sha256(temp_path1)
            hash2 = compute_sha256(temp_path2)
            assert hash1 != hash2
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestEdgeCases:
    """Tests for edge cases in validation."""

    def test_json_with_null_values(self, tmp_path):
        """Verify JSON with null values is handled correctly."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        data = [{"task_id": "1", "value": None}]
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["task_id", "value"], "test")
        assert result is True  # Structure is valid, null values are allowed

    def test_json_with_nested_structure(self, tmp_path):
        """Verify JSON with nested structure is handled."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        data = [{"task_id": "1", "metrics": {"complexity": 5}}]
        test_file.write_text(json.dumps(data))
        result = verify_json_structure(test_file, ["task_id", "metrics"], "test")
        assert result is True

    def test_invalid_json_syntax(self, tmp_path):
        """Verify invalid JSON syntax is caught."""
        from validate_quickstart import verify_json_structure
        test_file = tmp_path / "test.json"
        test_file.write_text("{invalid json}")
        result = verify_json_structure(test_file, ["task_id"], "test")
        assert result is False