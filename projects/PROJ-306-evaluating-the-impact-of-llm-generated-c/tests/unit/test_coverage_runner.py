import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from coverage_runner import (
    parse_pytest_cov_output,
    run_coverage,
    is_humaneval_task,
    run_coverage_with_catalog_check,
    save_coverage_report
)

class TestParsePytestCovOutput:
    def test_parse_standard_output(self):
        """Test parsing standard pytest-cov output with TOTAL line"""
        output = """
        Name                 Stmts   Miss  Cover   Missing
        --------------------------------------------------
        mycode.py              10      2    80%   5-6
        --------------------------------------------------
        TOTAL                  10      2    80%
        """
        result = parse_pytest_cov_output(output)
        assert result["line_coverage"] == 80.0
        assert result["branch_coverage"] is None

    def test_parse_branch_coverage(self):
        """Test parsing output with branch coverage"""
        output = """
        Name                 Stmts   Miss Branch BrPart  Cover
        ------------------------------------------------------
        mycode.py              10      2      4      1    80%
        ------------------------------------------------------
        TOTAL                  10      2      4      1    80%   45% (branches)
        """
        result = parse_pytest_cov_output(output)
        assert result["line_coverage"] == 80.0
        assert result["branch_coverage"] == 45.0

    def test_parse_no_coverage_data(self):
        """Test parsing output with no coverage data"""
        output = "No tests were collected."
        result = parse_pytest_cov_output(output)
        assert result["line_coverage"] is None
        assert result["branch_coverage"] is None

class TestIsHumanEvalTask:
    def test_human_eval_prefix(self):
        """Test detection of HumanEval tasks by prefix"""
        assert is_humaneval_task("HumanEval/0") is True
        assert is_humaneval_task("HumanEval/123") is True
        assert is_humaneval_task("mbpp_1") is False
        assert is_humaneval_task("MBPP/task_5") is False

    def test_catalog_data(self):
        """Test detection using catalog data"""
        catalog_data = {"task_id": "test", "dataset_source": "humaneval"}
        assert is_humaneval_task("test", catalog_data) is True
        
        catalog_data = {"task_id": "test", "dataset_source": "mbpp"}
        assert is_humaneval_task("test", catalog_data) is False

    def test_fallback_detection(self):
        """Test fallback detection in task_id"""
        assert is_humaneval_task("humaneval_task_1") is True
        assert is_humaneval_task("HumanEval_task") is True

class TestRunCoverage:
    def test_missing_generated_file(self):
        """Test handling of missing generated code file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generated_path = Path(tmpdir) / "missing.py"
            test_path = Path(tmpdir) / "test.py"
            test_path.touch()
            
            result = run_coverage("test_task", generated_path, test_path)
            assert result["status"] == "failed"
            assert "not found" in result["error_message"]

    def test_missing_test_suite(self):
        """Test handling of missing test suite"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generated_path = Path(tmpdir) / "code.py"
            generated_path.write_text("def hello(): pass")
            test_path = Path(tmpdir) / "missing_test.py"
            
            result = run_coverage("test_task", generated_path, test_path)
            assert result["status"] == "no_tests"
            assert result["line_coverage"] == 0.0
            assert result["branch_coverage"] == 0.0

    @patch('coverage_runner.subprocess.run')
    def test_successful_coverage_run(self, mock_run):
        """Test successful coverage execution"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="TOTAL 10 2 80%",
            stderr=""
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generated_path = Path(tmpdir) / "code.py"
            generated_path.write_text("def hello(): pass")
            test_path = Path(tmpdir) / "test.py"
            test_path.write_text("def test_hello(): pass")
            
            result = run_coverage("test_task", generated_path, test_path)
            assert result["status"] == "completed"
            assert result["line_coverage"] == 80.0

class TestRunCoverageWithCatalogCheck:
    def test_humaneval_branch_coverage_set_to_na(self):
        """Test that HumanEval tasks have branch_coverage set to N/A"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock catalog
            catalog_data = {
                "tasks": [
                    {"task_id": "HumanEval/0", "dataset_source": "humaneval"}
                ]
            }
            catalog_path = Path(tmpdir) / "catalog.json"
            with open(catalog_path, 'w') as f:
                json.dump(catalog_data["tasks"], f)
            
            generated_path = Path(tmpdir) / "code.py"
            generated_path.write_text("def hello(): pass")
            test_path = Path(tmpdir) / "test.py"
            test_path.write_text("def test_hello(): pass")
            
            # Mock the run_coverage to return a branch coverage
            with patch('coverage_runner.run_coverage') as mock_run:
                mock_run.return_value = {
                    "task_id": "HumanEval/0",
                    "status": "completed",
                    "line_coverage": 80.0,
                    "branch_coverage": 50.0,
                    "error_message": None
                }
                
                result = run_coverage_with_catalog_check(
                    "HumanEval/0",
                    generated_path,
                    test_path,
                    catalog_path
                )
                
                assert result["branch_coverage"] == "N/A"
                assert result["line_coverage"] == 80.0

    def test_non_humaneval_preserves_branch_coverage(self):
        """Test that non-HumanEval tasks preserve branch coverage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog_path = Path(tmpdir) / "catalog.json"
            with open(catalog_path, 'w') as f:
                json.dump([{"task_id": "mbpp_1", "dataset_source": "mbpp"}], f)
            
            generated_path = Path(tmpdir) / "code.py"
            generated_path.write_text("def hello(): pass")
            test_path = Path(tmpdir) / "test.py"
            test_path.write_text("def test_hello(): pass")
            
            with patch('coverage_runner.run_coverage') as mock_run:
                mock_run.return_value = {
                    "task_id": "mbpp_1",
                    "status": "completed",
                    "line_coverage": 80.0,
                    "branch_coverage": 50.0,
                    "error_message": None
                }
                
                result = run_coverage_with_catalog_check(
                    "mbpp_1",
                    generated_path,
                    test_path,
                    catalog_path
                )
                
                assert result["branch_coverage"] == 50.0

class TestSaveCoverageReport:
    def test_save_report_creates_file(self):
        """Test that save_report creates the JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "reports"
            result = {
                "task_id": "test",
                "status": "completed",
                "line_coverage": 80.0,
                "branch_coverage": 50.0
            }
            
            path = save_coverage_report(result, output_dir, "test_task")
            
            assert path.exists()
            with open(path, 'r') as f:
                saved_data = json.load(f)
                assert saved_data["task_id"] == "test_task"
                assert saved_data["status"] == "completed"
                assert "timestamp" in saved_data