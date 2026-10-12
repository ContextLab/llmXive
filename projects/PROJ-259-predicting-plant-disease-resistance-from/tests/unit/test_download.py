"""
Unit tests for the data-fetching logic implemented in ``code.download``.

The purpose of these tests is to verify that the download module can be
imported without side effects and that it exposes the expected public API.
Since the actual download process may involve network access and large
files, the tests deliberately avoid invoking any heavyweight functionality.
"""

import importlib
import pytest


def test_download_module_importable():
    """
    The ``code.download`` module should be importable without raising any
    exceptions. This ensures that all top‑level imports and module‑level
    code are safe to execute in a test environment.
    """
    try:
        importlib.import_module("code.download")
    except Exception as exc:
        pytest.fail(f"Importing code.download raised an exception: {exc}")


def test_download_module_exposes_main():
    """
    The download script is expected to provide a ``main`` callable that can
    be used as an entry point (e.g., ``python -m code.download``). The test
    verifies the attribute exists and is callable.
    """
    module = importlib.import_module("code.download")
    assert hasattr(module, "main"), "code.download should define a 'main' function"
    assert callable(module.main), "'main' in code.download should be callable"


def test_download_module_has_fetch_function():
    """
    A typical download implementation provides a function such as
    ``fetch_dataset`` or ``download_data``. The test checks for at least
    one of these common names to be present. If none are found, the test
    fails, indicating that the public API may have changed.
    """
    module = importlib.import_module("code.download")
    possible_names = ["fetch_dataset", "download_data", "download_dataset"]
    if not any(hasattr(module, name) for name in possible_names):
        pytest.fail(
            "code.download does not expose a known data‑fetching function. "
            f"Expected one of: {possible_names}"
        )