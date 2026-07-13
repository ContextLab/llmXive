import json
import os
import tempfile
from pathlib import Path
import pytest

from ast_validation import parse_snippet, validate_datasets, run_ast_validation, ERROR_INVALID_PARSE_THRESHOLD

class TestParseSnippet:
    def test_valid_python_function(self):
        code = "def foo(x):\n    return x + 1"
        success, error = parse_snippet("test-001", code, "python")
        assert success is True
        assert error is None

    def test_valid_python_class(self):
        code = "class Bar:\n    def __init__(self):\n        self.val = 1"
        success, error = parse_snippet("test-002", code, "python")
        assert success is True
        assert error is None

    def test_syntax_error(self):
        code = "def broken("
        success, error = parse_snippet("test-003", code, "python")
        assert success is False
        assert "SyntaxError" in error

    def test_unsupported_language(self):
        code = "function foo() { return 1; }"
        success, error = parse_snippet("test-004", code, "javascript")
        assert success is False
        assert "Unsupported language" in error

class TestValidateDatasets:
    def test_all_valid(self):
        data = [
            {"id": "1", "code": "def a(): pass", "language": "python"},
            {"id": "2", "code": "def b(): pass", "language": "python"}
        ]
        passed, failed_ids, rate = validate_datasets(data, threshold=0.95)
        assert passed is True
        assert failed_ids == []
        assert rate == 1.0

    def test_below_threshold(self):
        data = [
            {"id": "1", "code": "def a(): pass", "language": "python"},
            {"id": "2", "code": "def b(: pass", "language": "python"}, # Syntax error
            {"id": "3", "code": "def c(): pass", "language": "python"},
            {"id": "4", "code": "def d(: pass", "language": "python"}  # Syntax error
        ]
        # 2/4 = 0.5, threshold 0.95 -> fail
        passed, failed_ids, rate = validate_datasets(data, threshold=0.95)
        assert passed is False
        assert len(failed_ids) == 2
        assert rate == 0.5

    def test_empty_list(self):
        passed, failed_ids, rate = validate_datasets([], threshold=0.95)
        assert passed is False
        assert rate == 0.0

class TestRunAstValidation:
    def test_full_workflow_pass(self):
        data = [
            {"id": "1", "code": "def a(): return 1", "language": "python"},
            {"id": "2", "code": "def b(): return 2", "language": "python"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "report.json")
            
            with open(input_path, 'w') as f:
                json.dump(data, f)
            
            success = run_ast_validation(input_path, output_path, threshold=0.95)
            
            assert success is True
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["passed"] is True
            assert report["success_rate"] == 1.0

    def test_full_workflow_fail(self):
        data = [
            {"id": "1", "code": "def a(): pass", "language": "python"},
            {"id": "2", "code": "def b(: pass", "language": "python"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "report.json")
            
            with open(input_path, 'w') as f:
                json.dump(data, f)
            
            success = run_ast_validation(input_path, output_path, threshold=0.95)
            
            assert success is False
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report["passed"] is False
            assert report["success_rate"] == 0.5
            assert len(report["failed_ids"]) == 1