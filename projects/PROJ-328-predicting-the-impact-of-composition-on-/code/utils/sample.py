"""
Sample module to verify flake8 configuration.
This file intentionally includes a long line and specific formatting
to test the max-line-length and ignore rules.
"""

# This line is intentionally long to test the 88 character limit, but it should be ignored if we use E203/W503 correctly, or it might trigger if not. However, the config says ignore E203, W503.
long_variable_name_that_exceeds_the_standard_limit = "This is a test string to ensure the linter is configured correctly with the specific ignore rules for E203 and W503."

def sample_function(
    arg1,
    arg2,
):
    """
    A sample function with multi-line arguments.
    """
    result = arg1 + arg2
    return result

if __name__ == "__main__":
    print("Sample module executed successfully.")
