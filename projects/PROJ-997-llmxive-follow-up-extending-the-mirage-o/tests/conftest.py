"""
Pytest fixtures used by the integration tests.

The ``subprocess`` fixture provides a thin wrapper around ``subprocess.run``
that automatically inherits the current environment (including the virtual
environment activated by the runner) and raises a clear error if the
command cannot be found.
"""

import subprocess as _subprocess
import pytest

@pytest.fixture
def subprocess():
    class Runner:
        def run(self, *args, **kwargs):
            return _subprocess.run(*args, **kwargs)
    return Runner()