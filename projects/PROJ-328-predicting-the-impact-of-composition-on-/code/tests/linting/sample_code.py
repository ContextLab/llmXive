"""
Sample code file for verifying linting configuration (T003b).
This file contains intentional style violations to test flake8 configuration.
"""
import os
import sys
from pathlib import Path

# This line is too long and should trigger E501 if max-line-length is 88
very_long_variable_name_that_exceeds_the_standard_line_length_limit_for_linting_purposes = "This is a test string"

def sample_function(  ):
    """Sample function with extra spaces."""
    x=1+2
    return x

def another_function( x, y ):
    """Another function with spacing issues."""
    result = x+y
    return result

class SampleClass:
    """A sample class."""
    pass
