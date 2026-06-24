"""Unit test for syntax‑error handling in the ast_cloner module.

This test creates a temporary Python file containing an intentional syntax
error and verifies that the `compute_clone_density` function (to be
implemented in `code/ast_cloner.py`) raises a `SyntaxError`.  The test is
deliberately written before the implementation exists, so it is expected
to fail until the corresponding functionality is added.
"""

import pytest
from pathlib import Path


def test_syntax_error_handling(tmp_path: Path):
    """
    Ensure that a file with a syntax error is handled appropriately by the
    clone‑density computation function.

    The test writes a malformed Python source file, imports the target
    function, and asserts that a `SyntaxError` is raised.
    """
    # Create a temporary Python file with a deliberate syntax error.
    bad_file = tmp_path / "bad_syntax.py"
    bad_file.write_text("def broken_func(:\n    pass")  # Invalid function definition

    # Import the function that will be implemented in the future.
    # The import is expected to fail until `code/ast_cloner.py` provides it.
    from code.ast_cloner import compute_clone_density  # type: ignore

    # The function should raise a SyntaxError when attempting to parse the bad file.
    with pytest.raises(SyntaxError):
        compute_clone_density(str(bad_file))