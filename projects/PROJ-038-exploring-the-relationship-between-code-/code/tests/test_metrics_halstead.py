"""
Unit tests for Halstead Volume calculation.
"""

import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics_halstead import (
    calculate_halstead_volume,
    calculate_halstead_for_file,
    calculate_halstead_batch,
    extract_operators_and_operands
)


class TestExtractOperatorsAndOperands:
    """Tests for operator and operand extraction."""

    def test_simple_assignment(self):
        """Test extraction from a simple assignment statement."""
        code = "int x = 5;"
        operators, operands = extract_operators_and_operands(code)
        
        # Should have operators: int (keyword as operator), =, ;
        # Should have operands: x, 5
        assert 'int' in operators or 'int' in operands  # Depends on categorization
        assert '=' in operators
        assert ';' in operators
        assert 'x' in operands
        assert '5' in operands

    def test_arithmetic_expression(self):
        """Test extraction from arithmetic expression."""
        code = "a + b * c"
        operators, operands = extract_operators_and_operands(code)
        
        assert '+' in operators
        assert '*' in operators
        assert 'a' in operands
        assert 'b' in operands
        assert 'c' in operands

    def test_empty_code(self):
        """Test extraction from empty code."""
        code = ""
        operators, operands = extract_operators_and_operands(code)
        
        assert len(operators) == 0
        assert len(operands) == 0

    def test_string_literal(self):
        """Test that string literals are treated as operands."""
        code = 'String s = "hello";'
        operators, operands = extract_operators_and_operands(code)
        
        assert '"hello"' in operands

    def test_comment_ignored(self):
        """Test that comments are ignored."""
        code = """
        int x = 5; // This is a comment
        """
        operators, operands = extract_operators_and_operands(code)
        
        assert 'This' not in operands
        assert 'comment' not in operands


class TestCalculateHalsteadVolume:
    """Tests for Halstead Volume calculation."""

    def test_simple_case(self):
        """Test calculation with a simple code snippet."""
        code = "int x = 5;"
        volume = calculate_halstead_volume(code)
        
        # Should be a positive number
        assert isinstance(volume, float)
        assert volume >= 0

    def test_empty_code(self):
        """Test calculation with empty code."""
        code = ""
        volume = calculate_halstead_volume(code)
        
        assert volume == 0.0

    def test_complex_expression(self):
        """Test calculation with a more complex expression."""
        code = """
        int result = a + b * c - d / e;
        """
        volume = calculate_halstead_volume(code)
        
        assert isinstance(volume, float)
        assert volume > 0

    def test_no_operators(self):
        """Test calculation with code that has no operators."""
        code = "x"
        volume = calculate_halstead_volume(code)
        
        # Should handle gracefully
        assert isinstance(volume, float)
        assert volume >= 0

    def test_no_operands(self):
        """Test calculation with code that has no operands."""
        code = "= + *"
        volume = calculate_halstead_volume(code)
        
        # Should handle gracefully
        assert isinstance(volume, float)
        assert volume >= 0


class TestCalculateHalsteadForFile:
    """Tests for file-based Halstead calculation."""

    def test_valid_java_file(self):
        """Test calculation for a valid Java file."""
        java_code = """
        public class Test {
            public static void main(String[] args) {
                int x = 5;
                System.out.println(x);
            }
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_path = Path(f.name)
        
        try:
            volume = calculate_halstead_for_file(temp_path)
            assert isinstance(volume, float)
            assert volume >= 0
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """Test calculation for an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            volume = calculate_halstead_for_file(temp_path)
            assert volume == 0.0
        finally:
            os.unlink(temp_path)

    def test_nonexistent_file(self):
        """Test calculation for a non-existent file."""
        volume = calculate_halstead_for_file(Path("/nonexistent/file.java"))
        assert volume is None

    def test_invalid_encoding(self):
        """Test calculation for a file with invalid encoding."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.java', delete=False) as f:
            f.write(b'\x80\x81\x82')  # Invalid UTF-8
            temp_path = Path(f.name)
        
        try:
            volume = calculate_halstead_for_file(temp_path)
            # Should handle gracefully
            assert isinstance(volume, (float, type(None)))
        finally:
            os.unlink(temp_path)

    def test_large_file(self):
        """Test calculation for a larger file."""
        java_code = "public class Test {\n"
        for i in range(1000):
            java_code += f"    int x{i} = {i};\n"
        java_code += "}\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_path = Path(f.name)
        
        try:
            volume = calculate_halstead_for_file(temp_path)
            assert isinstance(volume, float)
            assert volume > 0  # Should be larger than a small file
        finally:
            os.unlink(temp_path)


class TestCalculateHalsteadBatch:
    """Tests for batch Halstead calculation."""

    def test_multiple_files(self):
        """Test batch calculation for multiple files."""
        files = []
        for i in range(3):
            java_code = f"public class Test{i} {{ int x = {i}; }}"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(java_code)
                files.append(Path(f.name))
        
        try:
            results = calculate_halstead_batch(files)
            
            assert len(results) == 3
            for file_path, volume in results.items():
                assert isinstance(volume, float)
                assert volume >= 0
        finally:
            for file_path in files:
                os.unlink(file_path)

    def test_mixed_valid_invalid(self):
        """Test batch calculation with mixed valid and invalid files."""
        valid_code = "public class Test { int x = 5; }"
        
        files = []
        
        # Valid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(valid_code)
            files.append(Path(f.name))
        
        # Non-existent file
        files.append(Path("/nonexistent/file.java"))
        
        # Another valid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(valid_code)
            files.append(Path(f.name))
        
        try:
            results = calculate_halstead_batch(files)
            
            # Should only include valid files
            assert len(results) == 2
            for file_path, volume in results.items():
                assert isinstance(volume, float)
                assert volume >= 0
        finally:
            for file_path in files[:1] + files[2:]:
                if file_path.exists():
                    os.unlink(file_path)

    def test_empty_list(self):
        """Test batch calculation with empty list."""
        results = calculate_halstead_batch([])
        assert results == {}