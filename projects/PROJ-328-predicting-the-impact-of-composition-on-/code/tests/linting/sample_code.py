"""
Sample code file for testing flake8 configuration.
This file contains intentional style variations to verify linting rules.
"""
import os
import sys
from pathlib import Path

# Test long line that should be caught if max-line-length is too short
long_variable_name_that_exceeds_eighty_eight_characters = "This is a test string to verify line length configuration in flake8"

def sample_function(
    arg1,
    arg2,
    arg3
):
    """Sample function with multi-line arguments."""
    # Test operator at start of line (W503) - should be ignored per config
    result = (
        arg1
        + arg2
        * arg3
    )
    return result

def another_function():
    """Another sample function."""
    # Test unused import warning (F401) - we import but don't use
    unused_module = os
    return "function completed"

# Test E203 (whitespace before ':') - should be ignored per config
my_list = [1, 2, 3]
slice_result = my_list[1:3]
