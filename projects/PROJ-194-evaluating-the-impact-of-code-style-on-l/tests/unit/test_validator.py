"""
Unit tests for code/transform/validator.py
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from code.transform.validator import (
    validate_python_syntax,
    validate_code_variants,
    filter_valid_variants,
    validate_file,
    save_validation_results,
    ValidationError
)


class TestValidatePythonSyntax:
    """Tests for validate_python_syntax function."""
    
    def test_valid_simple_function(self):
        """Test with a simple valid function."""
        code = "def add(a, b):\n    return a + b"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None
    
    def test_valid_class_definition(self):
        """Test with a valid class definition."""
        code = """
        class Calculator:
            def __init__(self):
                self.value = 0
            
            def increment(self):
                self.value += 1
        """
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None
    
    def test_valid_list_comprehension(self):
        """Test with list comprehension."""
        code = "squares = [x**2 for x in range(10)]"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None
    
    def test_invalid_missing_colon(self):
        """Test with missing colon (syntax error)."""
        code = "def add(a, b)\n    return a + b"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error
    
    def test_invalid_unclosed_parenthesis(self):
        """Test with unclosed parenthesis."""
        code = "result = (1 + 2"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error
    
    def test_invalid_indentation(self):
        """Test with invalid indentation."""
        code = """
        def foo():
            print("hello")
          print("world")
        """
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "SyntaxError" in error
    
    def test_empty_string(self):
        """Test with empty string."""
        code = ""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_whitespace_only(self):
        """Test with whitespace-only string."""
        code = "   \n\t  "
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_non_string_input(self):
        """Test with non-string input."""
        is_valid, error = validate_python_syntax(123)
        assert is_valid is False
        assert "string" in error.lower()
    
    def test_complex_valid_code(self):
        """Test with complex but valid Python code."""
        code = """
        import asyncio
        from typing import List, Optional

        async def fetch_data(url: str, timeout: int = 30) -> Optional[dict]:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            return await response.json()
            except Exception as e:
                print(f"Error fetching {url}: {e}")
            return None

        class DataProcessor:
            def __init__(self, data: List[dict]):
                self.data = data
                self.processed = []

            def process(self) -> List[dict]:
                return [item for item in self.data if item.get('valid', False)]
        """
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None


class TestValidateCodeVariants:
    """Tests for validate_code_variants function."""
    
    def test_all_valid(self):
        """Test with all valid variants."""
        variants = [
            {"variant_id": "v1", "code": "def foo(): pass"},
            {"variant_id": "v2", "code": "x = 1"},
            {"variant_id": "v3", "code": "class A: pass"}
        ]
        results = validate_code_variants(variants)
        
        assert results["total_count"] == 3
        assert results["valid_count"] == 3
        assert results["invalid_count"] == 0
        assert results["success_rate"] == 1.0
        assert len(results["valid_ids"]) == 3
        assert len(results["invalid_details"]) == 0
    
    def test_all_invalid(self):
        """Test with all invalid variants."""
        variants = [
            {"variant_id": "v1", "code": "def foo("},
            {"variant_id": "v2", "code": "x = (1"},
            {"variant_id": "v3", "code": "if True"}
        ]
        results = validate_code_variants(variants)
        
        assert results["total_count"] == 3
        assert results["valid_count"] == 0
        assert results["invalid_count"] == 3
        assert results["success_rate"] == 0.0
        assert len(results["valid_ids"]) == 0
        assert len(results["invalid_details"]) == 3
    
    def test_mixed_validity(self):
        """Test with mixed valid and invalid variants."""
        variants = [
            {"variant_id": "v1", "code": "def foo(): pass"},
            {"variant_id": "v2", "code": "x = (1"},
            {"variant_id": "v3", "code": "class A: pass"},
            {"variant_id": "v4", "code": "if True"}
        ]
        results = validate_code_variants(variants)
        
        assert results["total_count"] == 4
        assert results["valid_count"] == 2
        assert results["invalid_count"] == 2
        assert results["success_rate"] == 0.5
        assert set(results["valid_ids"]) == {"v1", "v3"}
        assert len(results["invalid_details"]) == 2
    
    def test_empty_list(self):
        """Test with empty list."""
        results = validate_code_variants([])
        
        assert results["total_count"] == 0
        assert results["valid_count"] == 0
        assert results["invalid_count"] == 0
        assert results["success_rate"] == 1.0
        assert len(results["valid_ids"]) == 0
        assert len(results["invalid_details"]) == 0
    
    def test_missing_variant_id(self):
        """Test with missing variant_id (should use 'unknown')."""
        variants = [
            {"code": "def foo(): pass"},
            {"variant_id": "v2", "code": "x = (1"}
        ]
        results = validate_code_variants(variants)
        
        assert "unknown" in results["valid_ids"]
        assert len(results["invalid_details"]) == 1


class TestFilterValidVariants:
    """Tests for filter_valid_variants function."""
    
    def test_filter_all_valid(self):
        """Test filtering when all are valid."""
        variants = [
            {"variant_id": "v1", "code": "def foo(): pass"},
            {"variant_id": "v2", "code": "x = 1"}
        ]
        filtered = filter_valid_variants(variants)
        
        assert len(filtered) == 2
        assert filtered[0]["variant_id"] == "v1"
        assert filtered[1]["variant_id"] == "v2"
    
    def test_filter_some_invalid(self):
        """Test filtering when some are invalid."""
        variants = [
            {"variant_id": "v1", "code": "def foo(): pass"},
            {"variant_id": "v2", "code": "x = ("},
            {"variant_id": "v3", "code": "class A: pass"}
        ]
        filtered = filter_valid_variants(variants)
        
        assert len(filtered) == 2
        ids = [v["variant_id"] for v in filtered]
        assert "v1" in ids
        assert "v2" not in ids
        assert "v3" in ids
    
    def test_filter_all_invalid(self):
        """Test filtering when all are invalid."""
        variants = [
            {"variant_id": "v1", "code": "def foo("},
            {"variant_id": "v2", "code": "x = ("}
        ]
        filtered = filter_valid_variants(variants)
        
        assert len(filtered) == 0


class TestValidateFile:
    """Tests for validate_file function."""
    
    def test_validate_valid_file(self):
        """Test validation of a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"variant_id": "v1", "code": "def foo(): pass"},
                {"variant_id": "v2", "code": "x = 1"}
            ], f)
            temp_path = f.name
        
        try:
            results = validate_file(temp_path)
            assert results["total_count"] == 2
            assert results["valid_count"] == 2
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        with pytest.raises(FileNotFoundError):
            validate_file("/nonexistent/path/file.json")
    
    def test_validate_dict_with_variants_key(self):
        """Test validation of JSON with 'variants' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "variants": [
                    {"variant_id": "v1", "code": "def foo(): pass"},
                    {"variant_id": "v2", "code": "x = ("}
                ]
            }, f)
            temp_path = f.name
        
        try:
            results = validate_file(temp_path)
            assert results["total_count"] == 2
            assert results["valid_count"] == 1
        finally:
            os.unlink(temp_path)
    
    def test_validate_invalid_structure(self):
        """Test validation of JSON with invalid structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"data": []}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                validate_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestSaveValidationResults:
    """Tests for save_validation_results function."""
    
    def test_save_results(self):
        """Test saving results to file."""
        results = {
            "total_count": 2,
            "valid_count": 1,
            "invalid_count": 1,
            "success_rate": 0.5,
            "valid_ids": ["v1"],
            "invalid_details": [{"variant_id": "v2", "error_message": "SyntaxError"}]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_validation_results(results, temp_path)
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                saved = json.load(f)
            
            assert saved["total_count"] == 2
            assert "timestamp" in saved
        finally:
            os.unlink(temp_path)
    
    def test_create_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        results = {"total_count": 0, "valid_count": 0, "invalid_count": 0, "success_rate": 1.0, "valid_ids": [], "invalid_details": []}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "subdir", "results.json")
            save_validation_results(results, output_path)
            assert os.path.exists(output_path)