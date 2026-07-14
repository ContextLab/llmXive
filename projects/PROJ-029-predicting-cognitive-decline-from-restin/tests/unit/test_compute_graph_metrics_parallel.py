"""Unit test ensuring that ``code/03_compute_graph_metrics.py`` uses joblib.Parallel."""

import ast
import inspect
from pathlib import Path

import pytest

# Import the module under test
from code import _03_compute_graph_metrics as compute_mod


def test_parallel_used():
    """Parse the source of ``main`` and assert a Parallel call is present."""
    source = inspect.getsource(compute_mod.main)
    tree = ast.parse(source)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "Parallel"
    ]
    assert calls, "joblib.Parallel should be used in the main() function"


def test_logger_is_callable():
    """Ensure the logger returned by get_logger can be called as a decorator."""
    from utils.logger import log_operation

    # The decorator should return a wrapper function when used on a callable
    @log_operation
    def dummy(x):
        return x * 2

    assert callable(dummy), "log_operation decorator should return a callable"


if __name__ == "__main__":
    pytest.main([Path(__file__).name])