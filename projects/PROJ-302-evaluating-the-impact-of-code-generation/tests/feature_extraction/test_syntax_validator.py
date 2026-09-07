import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Adjust import path based on how tests are run (usually from project root)
try:
    from code.feature_extraction.syntax_validator import validate_snippet_syntax, validate_dataset, main
except ImportError:
    # Fallback for direct execution in tests directory if structure differs
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.feature_extraction.syntax_validator import validate_snippet_syntax, validate_dataset, main

def test_validate_snippet_syntax_valid():
    valid_code = "def hello():\n    print('world')"
    is_valid, error = validate_snippet_syntax(valid_code)
    assert is_valid is True
    assert error is None

def test_validate_snippet_syntax_invalid():
    invalid_code = "def broken(:\n    print('world')"
    is_valid, error = validate_snippet_syntax(invalid_code)
    assert is_valid is False
    assert error is not None
    assert "SyntaxError" in error

def test_validate_snippet_syntax_empty():
    is_valid, error = validate_snippet_syntax("")
    assert is_valid is False
    assert error is not None

def test_validate_dataset_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "nonexistent.parquet")
        output_path = os.path.join(tmpdir, "report.json")
        
        report = validate_dataset(input_path, output_path)
        
        assert report["status"] == "generation_failed"
        assert report["meets_threshold"] is False
        assert os.path.exists(output_path)

def test_validate_dataset_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock dataset
        data = {
            "code": [
                "x = 1",
                "def func():\n    return 1",
                "y = 2"
            ]
        }
        df = pd.DataFrame(data)
        input_path = os.path.join(tmpdir, "data.parquet")
        output_path = os.path.join(tmpdir, "report.json")
        
        df.to_parquet(input_path)
        
        report = validate_dataset(input_path, output_path)
        
        assert report["status"] == "completed"
        assert report["total_snippets"] == 3
        assert report["valid_count"] == 3
        assert report["invalid_count"] == 0
        assert report["validity_rate"] == 1.0
        assert report["meets_threshold"] is True

def test_validate_dataset_failure_scenario():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dataset with invalid syntax
        data = {
            "code": [
                "x = 1",
                "def broken(:", # Invalid
                "y = 2"
            ]
        }
        df = pd.DataFrame(data)
        input_path = os.path.join(tmpdir, "data.parquet")
        output_path = os.path.join(tmpdir, "report.json")
        
        df.to_parquet(input_path)
        
        report = validate_dataset(input_path, output_path)
        
        assert report["status"] == "completed"
        assert report["total_snippets"] == 3
        assert report["valid_count"] == 2
        assert report["invalid_count"] == 1
        # 2/3 = 0.666 < 0.95
        assert report["validity_rate"] < 0.95
        assert report["meets_threshold"] is False
        assert len(report["errors"]) == 1