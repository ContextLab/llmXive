"""
Script to create the `tests/` directory in an idempotent manner
and verify that it is writable. This satisfies task T001b.
"""

import os
from llmxive_toolkit import paths


def create_and_verify_tests_dir() -> None:
    """
    Create the `tests/` directory (if it does not already exist) and
    assert that the resulting path is writable.

    The function is idempotent: calling it multiple times has no adverse
    effect and will always leave the directory in a writable state.
    """
    # `paths.tests()` creates the directory (parents=True, exist_ok=True)
    tests_dir = paths.tests()

    # Verify write access; raise an informative error if not writable.
    if not os.access(tests_dir, os.W_OK):
        raise PermissionError(f"Directory {tests_dir} is not writable")


if __name__ == "__main__":
    # When run as a script, simply perform the creation/verification.
    create_and_verify_tests_dir()
