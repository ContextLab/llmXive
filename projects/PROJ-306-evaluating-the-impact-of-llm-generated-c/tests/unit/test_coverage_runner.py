"""
Unit tests for coverage_runner.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from coverage_runner import (
    parse_coverage_output,
    is_humaneval_task,
    load_catalog,
    run_coverage_on_task
)

class TestParseCoverageOutput:
    def test_parse_line_coverage(self):
        output = """
        Name                                      Stmts   Miss  Cover   Missing
        -----------------------------------------------------------------------
        data/generated/task_1.py                    12      2    83%   5-6
        -----------------------------------------------------------------------
        TOTAL                                       12      2    83%
        """
        line_cov, branch_cov = parse_coverage_output(output)
        assert line_cov == 83.0
        assert branch_cov is None

    def test_parse_branch_coverage(self):
        # Simulating a case where branch coverage is explicitly printed
        output = """
        Name                                      Stmts   Miss Branch BrPart  Cover
        ---------------------------------------------------------------------------
        data/generated/task_1.py                    12      2      4      1    75%
        ---------------------------------------------------------------------------
        TOTAL                                       12      2      4      1    75%
        Branch coverage: 50.0%
        """
        line_cov, branch_cov = parse_coverage_output(output)
        # Note: The standard parsing logic looks for "Branch coverage: X%"
        assert line_cov == 75.0
        assert branch_cov == 50.0

    def test_parse_no_coverage(self):
        output = "No tests ran."
        line_cov, branch_cov = parse_coverage_output(output)
        assert line_cov is None
        assert branch_cov is None

class TestIsHumanEvalTask:
    def test_prefix_match(self):
        catalog_map = {}
        assert is_humaneval_task("HumanEval/0", catalog_map) is True
        assert is_humaneval_task("HumanEval/123", catalog_map) is True

    def test_catalog_source_match(self):
        catalog_map = {"mbpp_5": "humaneval"}
        assert is_humaneval_task("mbpp_5", catalog_map) is True
        assert is_humaneval_task("mbpp_6", catalog_map) is False

    def test_default_mbpp(self):
        catalog_map = {"mbpp_1": "mbpp"}
        assert is_humaneval_task("mbpp_1", catalog_map) is False

class TestRunCoverageOnTask:
    @pytest.fixture
    def mock_catalog(self, tmp_path):
        catalog_data = [
            {"task_id": "HumanEval/0", "dataset_source": "humaneval"},
            {"task_id": "mbpp_1", "dataset_source": "mbpp"}
        ]
        catalog_path = tmp_path / "data" / "benchmarks" / "processed" / "catalog.json"
        catalog_path.parent.mkdir(parents=True)
        with open(catalog_path, 'w') as f:
            json.dump(catalog_data, f)
        return catalog_path

    @pytest.fixture
    def mock_dirs(self, tmp_path):
        # Setup directory structure
        gen_dir = tmp_path / "data" / "generated"
        test_dir = tmp_path / "data" / "benchmarks" / "processed" / "tests"
        report_dir = tmp_path / "data" / "coverage_reports"
        
        gen_dir.mkdir(parents=True)
        test_dir.mkdir(parents=True)
        report_dir.mkdir(parents=True)
        
        # Create a dummy generated file
        gen_file = gen_dir / "test_task.py"
        gen_file.write_text("def add(a, b): return a + b\n")
        
        # Create a dummy test file
        test_file = test_dir / "test_task.py"
        test_file.write_text("from test_task import add\ndef test_add(): assert add(1, 2) == 3\n")
        
        return {
            "root": tmp_path,
            "gen_dir": gen_dir,
            "test_dir": test_dir,
            "report_dir": report_dir,
            "gen_file": gen_file,
            "test_file": test_file
        }

    @patch('coverage_runner.PROJECT_ROOT')
    @patch('coverage_runner.COVERAGE_REPORTS_DIR')
    @patch('coverage_runner.GENERATED_DIR')
    @patch('coverage_runner.TESTS_DIR')
    @patch('coverage_runner.load_catalog')
    @patch('subprocess.run')
    def test_run_coverage_success(
        self, mock_run, mock_load_cat, mock_tests_dir, mock_gen_dir, mock_cov_dir, mock_proj_root, mock_dirs
    ):
        # Setup mocks
        mock_proj_root.__truediv__ = lambda self, x: mock_dirs["root"] / x
        mock_tests_dir.__truediv__ = lambda self, x: mock_dirs["test_dir"] / x
        mock_gen_dir.__truediv__ = lambda self, x: mock_dirs["gen_dir"] / x
        mock_cov_dir.__truediv__ = lambda self, x: mock_dirs["report_dir"] / x
        
        mock_load_cat.return_value = {"test_task": "mbpp"}
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "TOTAL 12 2 83%\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_coverage_on_task("test_task", mock_dirs["gen_file"])
        
        assert result["status"] == "success"
        assert result["line_coverage"] == 83.0
        assert result["branch_coverage"] is None
        assert result["is_humaneval"] is False

    @patch('coverage_runner.PROJECT_ROOT')
    @patch('coverage_runner.COVERAGE_REPORTS_DIR')
    @patch('coverage_runner.GENERATED_DIR')
    @patch('coverage_runner.TESTS_DIR')
    @patch('coverage_runner.load_catalog')
    @patch('subprocess.run')
    def test_run_coverage_humaneval_force_na(
        self, mock_run, mock_load_cat, mock_tests_dir, mock_gen_dir, mock_cov_dir, mock_proj_root, mock_dirs
    ):
        mock_proj_root.__truediv__ = lambda self, x: mock_dirs["root"] / x
        mock_tests_dir.__truediv__ = lambda self, x: mock_dirs["test_dir"] / x
        mock_gen_dir.__truediv__ = lambda self, x: mock_dirs["gen_dir"] / x
        mock_cov_dir.__truediv__ = lambda self, x: mock_dirs["report_dir"] / x
        
        mock_load_cat.return_value = {"HumanEval/0": "humaneval"}
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "TOTAL 12 2 83%\nBranch coverage: 50%\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_coverage_on_task("HumanEval/0", mock_dirs["gen_file"])
        
        assert result["status"] == "success"
        assert result["line_coverage"] == 83.0
        assert result["branch_coverage"] == "N/A"
        assert result["is_humaneval"] is True