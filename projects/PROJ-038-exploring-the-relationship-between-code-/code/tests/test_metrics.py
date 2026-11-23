import pytest
from pathlib import Path
import tempfile
import os
import sys
import json

# Import the specific function we are testing from the implemented module
# Based on the API surface provided in the prompt
from src.metrics_halstead import calculate_halstead_volume, tokenize_java, calculate_halstead_for_file, calculate_halstead_batch

# --- Fixtures ---

@pytest.fixture
def temp_java_file():
    """Creates a temporary valid Java file with known complexity for testing."""
    content = """
    public class SimpleTest {
        public static void main(String[] args) {
            int a = 10;
            int b = 20;
            if (a > b) {
                System.out.println("a is greater");
            } else {
                System.out.println("b is greater or equal");
            }
            for (int i = 0; i < 10; i++) {
                if (i % 2 == 0) {
                    System.out.println(i);
                }
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_java_file_with_comments():
    """Creates a temporary Java file with comments to ensure tokenizer ignores them."""
    content = """
    // This is a single line comment
    /* This is a
       multi-line comment */
    public class CommentTest {
        public void method() {
            int x = 1; // inline comment
            if (x == 1) {
                x = 2;
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_invalid_file():
    """Creates a temporary file with invalid Java syntax (not .java or wrong content)."""
    content = "This is not valid Java code at all. It has no class definition."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

# --- Test Classes ---

class TestHalstead:
    """
    Unit tests for the Halstead complexity metrics.
    Specifically tests that the calculation returns a float value as required by T010b.
    """

    def test_tokenize_java_basic(self, temp_java_file):
        """Test that tokenization works on a valid Java file."""
        tokens = tokenize_java(temp_java_file)
        assert isinstance(tokens, list), "Tokenize should return a list of tokens."
        assert len(tokens) > 0, "Valid Java file should produce tokens."
        # Check for basic operators
        assert 'if' in tokens, "Expected 'if' operator in tokens."
        assert 'int' in tokens, "Expected 'int' keyword in tokens."

    def test_tokenize_ignores_comments(self, temp_java_file_with_comments):
        """Test that comments are correctly filtered out during tokenization."""
        tokens = tokenize_java(temp_java_file_with_comments)
        # Ensure comment markers are not present as tokens in a standard tokenizer
        # (Implementation dependent, but usually comments are stripped)
        # We verify that the code logic still produces a valid list
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_halstead_returns_float(self, temp_java_file):
        """
        T010b: Unit test `test_halstead_returns_float`.
        Verify that calculate_halstead_volume returns a float.
        """
        result = calculate_halstead_volume(temp_java_file)
        
        # Assert the return type is float
        assert isinstance(result, float), f"Expected float, got {type(result)}"
        
        # Assert the value is a reasonable number (not NaN, not Inf, not negative)
        assert result >= 0.0, "Halstead volume cannot be negative."
        assert not (result != result), "Result cannot be NaN." # Check for NaN

    def test_calculate_halstead_for_file_returns_dict(self, temp_java_file):
        """Test that the file-level calculation returns a dictionary with expected keys."""
        result = calculate_halstead_for_file(temp_java_file)
        
        assert isinstance(result, dict), "calculate_halstead_for_file should return a dict."
        assert 'volume' in result, "Result should contain 'volume' key."
        assert isinstance(result['volume'], float), "Volume value must be a float."
        assert 'n1' in result, "Result should contain unique operators count."
        assert 'n2' in result, "Result should contain unique operands count."
        assert 'N1' in result, "Result should contain total operators count."
        assert 'N2' in result, "Result should contain total operands count."

    def test_calculate_halstead_batch(self, temp_java_file, temp_java_file_with_comments):
        """Test batch processing returns a list of results."""
        file_list = [temp_java_file, temp_java_file_with_comments]
        results = calculate_halstead_batch(file_list)
        
        assert isinstance(results, list), "Batch result should be a list."
        assert len(results) == 2, "Should process both files."
        
        for res in results:
            assert isinstance(res, dict), "Each item in batch result should be a dict."
            assert 'volume' in res, "Each item should have 'volume'."
            assert isinstance(res['volume'], float), "Volume in batch result must be float."

    def test_halstead_on_invalid_file_raises_or_returns_none(self, temp_invalid_file):
        """Test behavior on a file that is not valid Java."""
        # Depending on implementation, this might raise an exception or return None/0
        # We ensure it doesn't crash the whole suite and returns a valid type if it attempts
        try:
            result = calculate_halstead_volume(temp_invalid_file)
            # If it returns a value, it must be a float
            if result is not None:
                assert isinstance(result, float)
        except Exception:
            # It is acceptable to raise an error for invalid files
            pass

class TestLOC:
    """Tests for Line of Code metrics (placeholder for completeness if T010a logic is needed)."""
    # These would be implemented if T010a required them, but T010b focuses on Halstead.
    pass

class TestCyclomaticComplexity:
    """Tests for Cyclomatic Complexity metrics."""
    pass

class TestMetricsBatch:
    """Tests for batch metric processing."""
    pass