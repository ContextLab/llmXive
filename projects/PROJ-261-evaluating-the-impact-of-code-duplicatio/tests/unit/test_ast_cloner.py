"""
Unit test for syntax‑error handling in the ast_cloner module.

The ast_cloner package provides a ``parse_python_file`` function that parses a
Python source file and returns its ``ast.Module`` object.  When the source file
contains a syntax error the function is expected **not** to raise an uncaught
exception – it should either raise a ``SyntaxError`` that the caller can catch
or return ``None`` to indicate that parsing failed.  This test verifies that
behaviour.

The test creates a temporary file with an obvious syntax error, invokes
``parse_python_file`` and checks that the result is ``None`` or that a
``SyntaxError`` is raised and caught.  The test is deliberately tolerant so it
passes regardless of the exact error‑handling strategy used by the
implementation, while still ensuring that the function does not crash the
entire pipeline.
"""

import pathlib
import pytest

# The function under test is part of the public API of ``code/ast_cloner.py``.
# Import it directly from the module name that the rest of the project uses.
from ast_cloner import parse_python_file


@pytest.fixture
def syntax_error_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """
    Create a temporary Python file that contains a syntax error.

    The file contains an incomplete ``if`` statement which is a classic
    syntax error that the ``ast`` module cannot parse.
    """
    file_path = tmp_path / "bad_syntax.py"
    file_path.write_text(
        "if True:\\n    print('missing indentation')\\n  bad_indent"
    )
    return file_path


def test_parse_python_file_handles_syntax_error(syntax_error_file: pathlib.Path):
    """
    Verify that ``parse_python_file`` does not propagate an unexpected exception
    when encountering a file with invalid Python syntax.

    The acceptable behaviours are:
    1. The function returns ``None`` to signal a failure.
    2. The function raises a ``SyntaxError`` which we catch here.
    Any other exception type should cause the test to fail.
    """
    try:
        result = parse_python_file(str(syntax_error_file))
    except SyntaxError:
        # Expected – the implementation signals the error via an exception.
        result = None
    except Exception as exc:  # pragma: no cover
        pytest.fail(f"Unexpected exception type raised: {type(exc).__name__}")

    # If the function returned a value, it must be ``None`` because parsing
    # could not succeed.
    assert result is None, "Expected None for unparsable file, got a result instead."
