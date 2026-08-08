"""
Unit tests for syntax_validator.py (Task T019)
"""
import pytest
import ast
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feature_extraction.syntax_validator import validate_snippet_syntax, validate_dataset, SUCCESS_RATE_THRESHOLD

class TestValidateSnippetSyntax:
    """Tests for the validate_snippet_syntax function."""
    
    def test_valid_python(self):
        """Test that valid Python code returns True."""
        code = "x = 1\ny = x + 1\nprint(y)"
        is_valid, error_msg = validate_snippet_syntax(code)
        assert is_valid is True
        assert error_msg is None
    
    def test_valid_class_definition(self):
        """Test that a class definition is valid."""
        code = """
        class MyClass:
            def __init__(self):
                self.value = 0
            
            def method(self):
                return self.value
        """
        is_valid, error_msg = validate_snippet_syntax(code)
        assert is_valid is True
        assert error_msg is None
    
    def test_invalid_syntax_missing_colon(self):
        """Test that invalid syntax (missing colon) returns False."""
        code = "if x == 1\n    print(x)"
        is_valid, error_msg = validate_snippet_syntax(code)
        assert is_valid is False
        assert error_msg is not None
        assert "SyntaxError" in error_msg
    
    def test_invalid_syntax_unclosed_parenthesis(self):
        """Test that unclosed parenthesis is invalid."""
        code = "print('hello'"
        is_valid, error_msg = validate_snippet_syntax(code)
        assert is_valid is False
        assert error_msg is not None
    
    def test_empty_string(self):
        """Test that empty string is invalid."""
        is_valid, error_msg = validate_snippet_syntax("")
        assert is_valid is False
        assert "Empty snippet" in error_msg
    
    def test_whitespace_only(self):
        """Test that whitespace-only string is invalid."""
        is_valid, error_msg = validate_snippet_syntax("   \n\t  ")
        assert is_valid is False
        assert "Empty snippet" in error_msg
    
    def test_non_string_input(self):
        """Test that non-string input returns False."""
        is_valid, error_msg = validate_snippet_syntax(123)
        assert is_valid is False
        assert "Invalid type" in error_msg
    
    def test_none_input(self):
        """Test that None input returns False."""
        is_valid, error_msg = validate_snippet_syntax(None)
        assert is_valid is False
        assert "Invalid type" in error_msg
    
    def test_complex_valid_code(self):
        """Test complex but valid Python code."""
        code = """
        import os
        import sys
        from typing import List, Dict, Optional
        
        def calculate_sum(numbers: List[int]) -> int:
            return sum(numbers)
        
        class DataProcessor:
            def __init__(self, data: Dict[str, Any]):
                self.data = data
                self.processed = False
            
            def process(self) -> Optional[List[str]]:
                if not self.processed:
                    return [str(v) for v in self.data.values()]
                return None
        """
        is_valid, error_msg = validate_snippet_syntax(code)
        assert is_valid is True
        assert error_msg is None

class TestValidateDataset:
    """Tests for the validate_dataset function."""
    
    def test_validate_dataset_with_valid_snippets(self, tmp_path):
        """Test validation with all valid snippets."""
        # Create a test parquet file
        test_data = pd.DataFrame({
            'snippet_id': [1, 2, 3],
            'code': [
                'x = 1',
                'def foo(): return 1',
                'class Bar: pass'
            ]
        })
        input_file = tmp_path / "test_input.parquet"
        test_data.to_parquet(input_file)
        
        result = validate_dataset(input_file)
        
        assert len(result) == 3
        assert all(result['is_valid'] == True)
        assert result['overall_success_rate'].iloc[0] == 1.0
        assert result['success_rate_threshold_met'].iloc[0] is True
    
    def test_validate_dataset_with_invalid_snippets(self, tmp_path):
        """Test validation with some invalid snippets."""
        test_data = pd.DataFrame({
            'snippet_id': [1, 2, 3, 4, 5],
            'code': [
                'x = 1',  # valid
                'if x:',  # valid
                'if x',   # invalid (missing colon)
                'def f():', # valid
                'def g('   # invalid (unclosed)
            ]
        })
        input_file = tmp_path / "test_input.parquet"
        test_data.to_parquet(input_file)
        
        result = validate_dataset(input_file)
        
        assert len(result) == 5
        assert result['is_valid'].sum() == 3  # 3 valid
        assert result['overall_success_rate'].iloc[0] == 0.6  # 60%
        assert result['success_rate_threshold_met'].iloc[0] is False  # < 95%
    
    def test_validate_dataset_different_column_names(self, tmp_path):
        """Test that different column names for code are handled."""
        # Test with 'snippet' column
        test_data = pd.DataFrame({
            'snippet_id': [1, 2],
            'snippet': ['x = 1', 'y = 2']
        })
        input_file = tmp_path / "test_snippet.parquet"
        test_data.to_parquet(input_file)
        
        result = validate_dataset(input_file)
        assert all(result['is_valid'] == True)
        
        # Test with 'code_content' column
        test_data = pd.DataFrame({
            'snippet_id': [1, 2],
            'code_content': ['a = 1', 'b = 2']
        })
        input_file = tmp_path / "test_content.parquet"
        test_data.to_parquet(input_file)
        
        result = validate_dataset(input_file)
        assert all(result['is_valid'] == True)
    
    def test_validate_dataset_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        input_file = tmp_path / "nonexistent.parquet"
        
        with pytest.raises(FileNotFoundError):
            validate_dataset(input_file)

class TestThresholdConstants:
    """Tests for threshold constants."""
    
    def test_threshold_is_95_percent(self):
        """Verify the success rate threshold is 0.95 (95%)."""
        assert SUCCESS_RATE_THRESHOLD == 0.95
    
    def test_threshold_value_reasonable(self):
        """Verify threshold is between 0 and 1."""
        assert 0 < SUCCESS_RATE_THRESHOLD < 1