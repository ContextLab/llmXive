import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_baseline import (
    load_json_file,
    load_prompt_ids,
    synthesize_baseline,
    validate_schema,
    save_baseline
)

class TestLoadJsonFile:
    def test_load_valid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            result = load_json_file(temp_path)
            assert result == {"test": "data"}
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        result = load_json_file("/nonexistent/file.json")
        assert result is None

    def test_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            temp_path = f.name

        try:
            result = load_json_file(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

class TestLoadPromptIds:
    def test_load_list_of_dicts(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": "1"}, {"id": "2"}], f)
            temp_path = f.name

        try:
            result = load_prompt_ids(temp_path)
            assert result == ["1", "2"]
        finally:
            os.unlink(temp_path)

    def test_load_dict_with_prompts_key(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"prompts": [{"id": "a"}, {"id": "b"}]}, f)
            temp_path = f.name

        try:
            result = load_prompt_ids(temp_path)
            assert result == ["a", "b"]
        finally:
            os.unlink(temp_path)

class TestSynthesizeBaseline:
    def test_synthesize_baseline_returns_dict(self):
        prompt_ids = ["1", "2", "3"]
        result = synthesize_baseline(prompt_ids)
        
        assert isinstance(result, dict)
        assert len(result) == 3
        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
            assert value > 0

    def test_synthesize_baseline_consistency(self):
        prompt_ids = ["1", "2", "3"]
        result1 = synthesize_baseline(prompt_ids)
        result2 = synthesize_baseline(prompt_ids)
        
        assert result1 == result2

class TestValidateSchema:
    def test_valid_schema(self):
        data = {"1": 10.5, "2": 15.2}
        assert validate_schema(data) is True

    def test_invalid_key_type(self):
        data = {1: 10.5}
        assert validate_schema(data) is False

    def test_invalid_value_type(self):
        data = {"1": "10.5"}
        assert validate_schema(data) is False

    def test_invalid_value_negative(self):
        data = {"1": -5.0}
        assert validate_schema(data) is False

    def test_invalid_value_zero(self):
        data = {"1": 0.0}
        assert validate_schema(data) is False

class TestSaveBaseline:
    def test_save_baseline(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            data = {"1": 10.5, "2": 15.2}
            save_baseline(data, temp_path)
            
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == data
        finally:
            os.unlink(temp_path)