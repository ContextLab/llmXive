"""
Unit tests for code/04_validation.py
"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
# We import the module to access internal helpers for testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validation import validate_record, load_data, REQUIRED_FIELDS, VALID_COMPLEXITY_LABELS, MAX_TOKENS

class TestValidateRecord:
    
    def test_valid_record(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            'complexity': 'low',
            'explanation': 'Simple print statement',
            'token_count': 10,
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert len(errors) == 0

    def test_missing_required_field(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            # missing complexity
            'explanation': 'Simple print statement',
            'token_count': 10,
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert any("complexity" in e for e in errors)
        assert any("null" in e or "Missing" in e for e in errors)

    def test_null_value_in_required_field(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            'complexity': None,
            'explanation': 'Simple print statement',
            'token_count': 10,
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert any("null" in e for e in errors)

    def test_invalid_complexity_label(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            'complexity': 'extreme',
            'explanation': 'Simple print statement',
            'token_count': 10,
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert any("Invalid complexity" in e for e in errors)

    def test_token_count_exceeds_limit(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            'complexity': 'low',
            'explanation': 'Simple print statement',
            'token_count': 150, # Limit is < 150
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert any("exceeds limit" in e for e in errors)

    def test_token_count_at_limit(self):
        record = {
            'snippet_id': '1',
            'code': 'print("hello")',
            'complexity': 'low',
            'explanation': 'Simple print statement',
            'token_count': 149,
            'model_used': 'llama',
            'status': 'success'
        }
        errors = validate_record(record, 0)
        assert len(errors) == 0

class TestLoadData:
    
    def test_load_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{'key': 'value'}], f)
            f.flush()
            path = Path(f.name)
            
            data = load_data(path)
            assert len(data) == 1
            assert data[0]['key'] == 'value'
        
        path.unlink()

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_data(Path("/nonexistent/path/file.json"))

    def test_load_non_list_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            path = Path(f.name)
            
            with pytest.raises(ValueError):
                load_data(path)
        
        path.unlink()