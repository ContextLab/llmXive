"""
Unit tests for code/models/simplify.py focusing on retry logic and failure handling.

These tests verify that the simplification process correctly handles:
1. Generation failures (empty output, invalid syntax)
2. Retry mechanism (max retries respected)
3. Fallback behavior (returning None or raising appropriate errors)
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.simplify import simplify_function, SimplificationError
from utils.logger import get_logger

# Mock the model loader and generation components
class MockModel:
    def __init__(self, fail_count=0, success_output=None):
        self.fail_count = fail_count
        self.success_output = success_output
        self.call_count = 0

    def generate(self, prompt, max_new_tokens=500, temperature=0.7):
        self.call_count += 1
        if self.call_count <= self.fail_count:
            # Simulate generation failure
            return ""
        return self.success_output or "def simplified():\n    return 42"

class MockTokenizer:
    def __init__(self):
        pass

    def encode(self, text, return_tensors="pt"):
        return MagicMock()

    def decode(self, ids, skip_special_tokens=True):
        return "mocked_output"

@pytest.fixture
def mock_model_loader():
    """Fixture to provide a mock model loader"""
    with patch("models.simplify.load_model") as mock_load:
        mock_model = MockModel()
        mock_load.return_value = (mock_model, MockTokenizer())
        yield mock_load

@pytest.fixture
def mock_logger():
    """Fixture to provide a mock logger"""
    with patch("models.simplify.get_logger") as mock_logger:
        mock_logger.return_value = MagicMock()
        yield mock_logger

def test_simplify_success_on_first_try(mock_model_loader, mock_logger):
    """Test successful simplification on first attempt"""
    original_code = "def add(a, b):\n    return a + b"
    
    result = simplify_function(original_code, max_retries=3)
    
    assert result is not None
    assert "def simplified" in result or "return" in result
    assert mock_model_loader.return_value[0].call_count == 1

def test_simplify_success_after_retries(mock_model_loader, mock_logger):
    """Test successful simplification after some failures"""
    original_code = "def add(a, b):\n    return a + b"
    
    # Configure mock to fail twice then succeed
    mock_model = MockModel(fail_count=2, success_output="def simplified_add(a, b):\n    return a + b")
    mock_model_loader.return_value[0] = mock_model
    
    result = simplify_function(original_code, max_retries=5)
    
    assert result is not None
    assert "def simplified_add" in result
    assert mock_model.call_count == 3  # 2 failures + 1 success

def test_simplify_fails_after_max_retries(mock_model_loader, mock_logger):
    """Test that simplification fails gracefully after max retries"""
    original_code = "def add(a, b):\n    return a + b"
    
    # Configure mock to always fail
    mock_model = MockModel(fail_count=10, success_output=None)
    mock_model_loader.return_value[0] = mock_model
    
    with pytest.raises(SimplificationError) as exc_info:
        simplify_function(original_code, max_retries=3)
    
    assert "Max retries" in str(exc_info.value)
    assert mock_model.call_count == 3  # Should retry exactly max_retries times

def test_simplify_handles_empty_generation(mock_model_loader, mock_logger):
    """Test handling of empty string generation"""
    original_code = "def add(a, b):\n    return a + b"
    
    # Configure mock to return empty strings
    mock_model = MockModel(fail_count=10)
    mock_model.generate = MagicMock(return_value="")
    mock_model_loader.return_value[0] = mock_model
    
    with pytest.raises(SimplificationError) as exc_info:
        simplify_function(original_code, max_retries=2)
    
    assert "empty" in str(exc_info.value).lower() or "generation" in str(exc_info.value).lower()
    assert mock_model.call_count == 2

def test_simplify_handles_invalid_syntax_after_generation(mock_model_loader, mock_logger):
    """Test handling of generated code with invalid syntax"""
    original_code = "def add(a, b):\n    return a + b"
    
    # Configure mock to generate invalid syntax
    mock_model = MockModel(fail_count=10)
    mock_model.generate = MagicMock(return_value="def invalid(")  # Invalid syntax
    mock_model_loader.return_value[0] = mock_model
    
    with pytest.raises(SimplificationError) as exc_info:
        simplify_function(original_code, max_retries=2)
    
    assert "syntax" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    assert mock_model.call_count == 2

def test_simplify_uses_configurable_max_retries(mock_model_loader, mock_logger):
    """Test that max_retries parameter is respected"""
    original_code = "def add(a, b):\n    return a + b"
    
    mock_model = MockModel(fail_count=10)
    mock_model_loader.return_value[0] = mock_model
    
    # Test with max_retries=1
    with pytest.raises(SimplificationError):
        simplify_function(original_code, max_retries=1)
    assert mock_model.call_count == 1
    
    # Reset and test with max_retries=5
    mock_model.call_count = 0
    with pytest.raises(SimplificationError):
        simplify_function(original_code, max_retries=5)
    assert mock_model.call_count == 5

def test_simplify_logs_retry_attempts(mock_model_loader, mock_logger):
    """Test that retry attempts are logged"""
    original_code = "def add(a, b):\n    return a + b"
    
    mock_model = MockModel(fail_count=2, success_output="def simplified():\n    pass")
    mock_model_loader.return_value[0] = mock_model
    
    result = simplify_function(original_code, max_retries=3)
    
    # Verify logger was called for each retry attempt
    assert mock_logger.return_value.warning.call_count >= 2  # At least 2 warnings for retries

def test_simplify_preserves_original_on_failure(mock_model_loader, mock_logger):
    """Test that original function is preserved when simplification fails"""
    original_code = "def add(a, b):\n    return a + b"
    
    mock_model = MockModel(fail_count=10)
    mock_model_loader.return_value[0] = mock_model
    
    with pytest.raises(SimplificationError):
        simplify_function(original_code, max_retries=2)
    
    # The error should be raised, but we verify the original code wasn't modified
    # by checking that the function raises an error rather than returning modified code
    pass

def test_simplify_handles_timeout_during_generation(mock_model_loader, mock_logger):
    """Test handling of timeout during generation"""
    original_code = "def add(a, b):\n    return a + b"
    
    mock_model = MockModel(fail_count=10)
    mock_model.generate = MagicMock(side_effect=TimeoutError("Generation timeout"))
    mock_model_loader.return_value[0] = mock_model
    
    with pytest.raises(SimplificationError) as exc_info:
        simplify_function(original_code, max_retries=2)
    
    assert "timeout" in str(exc_info.value).lower()
    assert mock_model.call_count == 2

def test_simplify_with_complex_function(mock_model_loader, mock_logger):
    """Test simplification with a more complex function"""
    original_code = """
    def complex_calculation(x, y, z):
        result = 0
        for i in range(x):
            if i % 2 == 0:
                result += i * y
            else:
                result -= i * z
        return result
    """
    
    mock_model = MockModel(fail_count=1, success_output="def simplified_calculation(x, y, z):\n    return sum(i * y if i % 2 == 0 else -i * z for i in range(x))")
    mock_model_loader.return_value[0] = mock_model
    
    result = simplify_function(original_code, max_retries=3)
    
    assert result is not None
    assert "simplified_calculation" in result or "sum" in result
    assert mock_model.call_count == 2