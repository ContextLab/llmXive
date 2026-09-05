"""
Sample Python file for linting verification.
This file contains intentional style issues to test flake8 configuration.
"""
import os
import sys

# Intentional: long line that should trigger E501 if max-line-length is 88
very_long_variable_name_that_exceeds_eighty_eight_characters = "This is a very long string value that exceeds the standard line length limit"

def sample_function( x,y ):
    """Sample function with bad spacing."""
    result=x+y  # Intentional: missing spaces around operator
    return result

# Intentional: unused import
from collections import defaultdict

if __name__ == "__main__":
    print(sample_function(1, 2))
