"""
Sample file for linting verification (Task T003b).
Contains intentional style elements to verify flake8 configuration.
"""

def sample_function( x,y ):
    """Sample function with intentional spacing issues."""
    result=x+y
    # This is a comment
    return result


def another_function():
    """Another function to test linting."""
    long_variable_name = 10
    another_long_variable_name = 20
    # Testing line length
    very_long_comment_that_might_exceed_standard_line_length_limits_if_not_handled_properly_by_the_linter = "test"
    return long_variable_name + another_long_variable_name
