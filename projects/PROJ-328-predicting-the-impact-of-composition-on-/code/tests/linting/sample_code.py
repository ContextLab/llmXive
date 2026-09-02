"""Sample code file for linting verification."""
def sample_function(x, y):
    """A simple function to test linting."""
    result = x + y
    return result

# This line is intentionally long to test max-line-length if set to <100
# This is a comment that is deliberately made very long to exceed typical line length limits if the configuration is set to 88 or 100 characters.
long_variable_name_that_is_still_reasonable = "This is a test string"

if __name__ == "__main__":
    print(sample_function(1, 2))
