import pytest
import sys
from pathlib import Path

# Add parent directory to path to import calculate_emissions
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from calculate_emissions import count_loc

def test_count_loc_basic():
    """Test basic line counting."""
    code = "def hello():\n    print('hi')\n"
    assert count_loc(code) == 2

def test_count_loc_empty():
    """Test empty string."""
    assert count_loc("") == 0
    assert count_loc(None) == 0
    assert count_loc("   \n  \n  ") == 0

def test_count_loc_comments():
    """Test that comment-only lines are excluded."""
    code = "# This is a comment\nprint('hi')\n# Another comment\n"
    assert count_loc(code) == 1

def test_count_loc_mixed():
    """Test mixed code and comments."""
    code = """
    import os
    # comment
    def func():
        pass
    # end
    """
    # Lines: import, def, pass
    assert count_loc(code) == 3

def test_count_loc_whitespace_handling():
    """Test that whitespace-only lines are excluded."""
    code = "x = 1\n\n\ny = 2"
    assert count_loc(code) == 2

def test_count_loc_realistic_snippet():
    """Test a realistic code snippet similar to LLM output."""
    code = """
    def calculate_sum(a, b):
        # Add numbers
        return a + b

    result = calculate_sum(5, 10)
    print(result)
    """
    # Lines: def, return, result, print (4 lines)
    # Comments and empty lines excluded
    assert count_loc(code) == 4