"""Unit tests for null baseline generation (identity transformation)."""

import pytest
from llm.baseline import generate_identity_baseline, validate_identity_baseline


class TestBaselineGeneration:
    """Tests for the null baseline (identity) generation logic."""

    def test_baseline_returns_identity(self):
        """Assert that the baseline code string matches the input code string exactly.

        This test verifies the core contract of the null baseline: that it performs
        an identity transformation, returning the input code unchanged.
        """
        # Arrange
        input_code = "def hello():\n    print('world')\n"
        
        # Act
        baseline_code = generate_identity_baseline(input_code)
        
        # Assert
        assert baseline_code == input_code, (
            f"Baseline code '{baseline_code}' does not match "
            f"input code '{input_code}'"
        )

    def test_baseline_empty_string(self):
        """Assert that an empty input string returns an empty baseline."""
        # Arrange
        input_code = ""
        
        # Act
        baseline_code = generate_identity_baseline(input_code)
        
        # Assert
        assert baseline_code == input_code
        assert baseline_code == ""

    def test_baseline_multiline_complex(self):
        """Assert that complex multiline code is preserved exactly."""
        # Arrange
        input_code = """
        def calculate_complexity(code):
            import ast
            tree = ast.parse(code)
            return len(list(ast.walk(tree)))
        
        class DataProcessor:
            def __init__(self, data):
                self.data = data
            
            def process(self):
                return [x * 2 for x in self.data if x > 0]
        """
        
        # Act
        baseline_code = generate_identity_baseline(input_code)
        
        # Assert
        assert baseline_code == input_code
        
        # Additional check: validate_identity_baseline should return True
        is_valid = validate_identity_baseline(input_code, baseline_code)
        assert is_valid is True

    def test_baseline_whitespace_preservation(self):
        """Assert that whitespace differences are detected (baseline must be exact)."""
        # Arrange
        input_code = "def foo():\n    pass\n"
        modified_code = "def foo():\n  pass\n"  # Different indentation
        
        # Act
        baseline_code = generate_identity_baseline(input_code)
        
        # Assert
        assert baseline_code == input_code
        assert baseline_code != modified_code
        
        # Validate that the mismatch is caught
        is_valid = validate_identity_baseline(input_code, modified_code)
        assert is_valid is False

    def test_baseline_unicode_preservation(self):
        """Assert that unicode characters are preserved exactly."""
        # Arrange
        input_code = "def greet(name):\n    return f'Héllo, {name}! 你好'\n"
        
        # Act
        baseline_code = generate_identity_baseline(input_code)
        
        # Assert
        assert baseline_code == input_code
        assert baseline_code == input_code.encode('utf-8').decode('utf-8')

    def test_baseline_validation_raises_on_mismatch(self):
        """Assert that validate_identity_baseline returns False on mismatch."""
        # Arrange
        input_code = "x = 1"
        output_code = "y = 2"
        
        # Act
        is_valid = validate_identity_baseline(input_code, output_code)
        
        # Assert
        assert is_valid is False

    def test_baseline_validation_returns_true_on_match(self):
        """Assert that validate_identity_baseline returns True on exact match."""
        # Arrange
        input_code = "x = 1"
        output_code = "x = 1"
        
        # Act
        is_valid = validate_identity_baseline(input_code, output_code)
        
        # Assert
        assert is_valid is True