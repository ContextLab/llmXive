"""Tests for the resource‑guard utilities."""
import pytest
from llmxive_toolkit import paths

# Import the module to trigger the size check and log creation.
import code.utils as utils  # noqa: F401


def test_guard_log_exists_and_mode():
    """The guard log must exist and contain a valid mode."""
    log_path = paths.outputs("logs", "guard_log.txt")
    assert log_path.is_file(), "guard_log.txt was not created"

    content = log_path.read_text().strip()
    assert content.startswith("resource_guard: mode="), "Unexpected log format"

    mode = content.split("=")[1]
    # In the CI environment the ``data/raw`` directory is empty, so we expect ``full``.
    assert mode == "full", f"Expected mode 'full' but got '{mode}'"