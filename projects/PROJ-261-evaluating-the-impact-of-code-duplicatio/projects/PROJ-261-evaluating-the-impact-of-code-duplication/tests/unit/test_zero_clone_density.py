"""Unit test for handling zero clone density.

This test ensures that the clone density computation function gracefully
handles the edge case where no code files (or no clones) are provided.
The expected behaviour is to return a density of ``0.0`` rather than
raising an exception such as ``ZeroDivisionError``.
"""

import pytest

# The implementation of ``compute_clone_density`` is part of the
# ``code.ast_cloner`` module, which will be provided in a later task.
# Importing it here validates the public API contract.
from code.ast_cloner import compute_clone_density


def test_zero_clone_density_returns_zero():
    """When given an empty collection of files, the function should return 0.0."""
    # Empty input represents the scenario with no source files to analyse.
    empty_file_list: list[str] = []

    density = compute_clone_density(empty_file_list)

    assert isinstance(density, float), "Clone density should be a float"
    assert density == 0.0, "Clone density for empty input must be 0.0"