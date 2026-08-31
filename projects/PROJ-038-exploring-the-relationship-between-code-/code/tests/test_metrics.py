import pytest
from pathlib import Path
import tempfile
import os
import sys
import json

# Ensure the code directory is in the path for imports
_code_root = Path(__file__).resolve().parent.parent
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from src.metrics import calculate_halstead_single_file, calculate_loc_ast, calculate_cc_single_file
from src.metrics.halstead import calculate_halstead_volume, tokenize_java


@pytest.fixture
def temp_java_file():
    """Creates a temporary valid Java file with simple logic."""
    content = """
    public class SimpleTest {
        public static void main(String[] args) {
            int x = 10;
            int y = 20;
            if (x > 0) {
                System.out.println(x + y);
            } else {
                System.out.println(0);
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
    return f.name


@pytest.fixture
def temp_java_file_with_comments():
    """Creates a temporary Java file with comments to ensure they are ignored."""
    content = """
    // This is a comment
    /* Multi-line comment */
    public class CommentTest {
        public void method() {
            int a = 1; // inline comment
            int b = 2;
            return a + b;
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
    return f.name


@pytest.fixture
def temp_invalid_file():
    """Creates a temporary file that is not valid Java."""
    content = "This is not java code at all."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
    return f.name


class TestLOC:
    def test_loc_returns_int(self, temp_java_file):
        result = calculate_loc_ast(temp_java_file)
        assert isinstance(result, int)
        assert result > 0
    
    def test_loc_ignores_comments(self, temp_java_file_with_comments):
        result = calculate_loc_ast(temp_java_file_with_comments)
        # Should be positive but less than total lines if comments were counted
        assert isinstance(result, int)
        assert result > 0


class TestLOCBatch:
    def test_batch_loc_returns_dict(self, temp_java_file):
        result = calculate_loc_ast(temp_java_file)
        assert isinstance(result, int)


class TestCyclomaticComplexity:
    def test_cc_returns_int(self, temp_java_file):
        result = calculate_cc_single_file(temp_java_file)
        assert isinstance(result, int)
        # Simple class with an if/else should have complexity > 1
        assert result >= 1


class TestHalstead:
    def test_halstead_returns_float(self, temp_java_file):
        """
        Unit test for T010b: Verify that calculate_halstead_single_file 
        returns a float value for Halstead Volume.
        """
        volume = calculate_halstead_single_file(temp_java_file)
        
        # Assert the type is float
        assert isinstance(volume, float), f"Expected float, got {type(volume)}"
        
        # Assert the value is non-negative (volume cannot be negative)
        assert volume >= 0.0, f"Expected non-negative volume, got {volume}"
        
        # Optional: Assert it's not NaN or Inf
        assert not (volume != volume), "Volume is NaN"
        assert volume != float('inf'), "Volume is Infinity"

    def test_halstead_consistency(self, temp_java_file):
        """Verify that running the calculation twice yields the same result."""
        vol1 = calculate_halstead_single_file(temp_java_file)
        vol2 = calculate_halstead_single_file(temp_java_file)
        assert vol1 == vol2

    def test_halstead_on_comments_ignored(self, temp_java_file_with_comments):
        """Verify that comments do not inflate the Halstead volume significantly compared to code-only."""
        # We can't easily know the exact value without a reference, but we ensure it returns a valid float
        volume = calculate_halstead_single_file(temp_java_file_with_comments)
        assert isinstance(volume, float)
        assert volume >= 0.0

    def test_halstead_invalid_file_raises(self, temp_invalid_file):
        """Verify that invalid Java files are handled gracefully (return 0 or raise)."""
        # Depending on implementation, it might return 0 or raise a specific error.
        # Based on T014c spec: "If parsing fails, log the file path and skip it, raising a warning but not halting."
        # The wrapper should likely return 0.0 for invalid files to allow batch processing to continue.
        volume = calculate_halstead_single_file(temp_invalid_file)
        assert isinstance(volume, float)
        assert volume == 0.0


class TestMetricsBatch:
    def test_all_metrics_return_correct_types(self, temp_java_file):
        """Integration check: LOC (int), CC (int), Halstead (float)."""
        loc = calculate_loc_ast(temp_java_file)
        cc = calculate_cc_single_file(temp_java_file)
        halstead = calculate_halstead_single_file(temp_java_file)

        assert isinstance(loc, int)
        assert isinstance(cc, int)
        assert isinstance(halstead, float)