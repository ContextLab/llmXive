"""
Unit test for the CI citation‑validation entry point.

The test ensures that the ``run_citation_validation`` script correctly
propagates the exit status from ``src.ci.validate_citations.main``.
It does this by monkey‑patching the imported ``validate_citations_main``
function to return ``True`` and ``False`` in separate sub‑tests.
"""

import importlib
import sys
import types

import pytest

# Import the script under test.
script_path = "src.ci.run_citation_validation"
run_citation_validation = importlib.import_module(script_path)


@pytest.fixture(autouse=True)
def patch_sys_exit(monkeypatch):
    """Replace ``sys.exit`` with a mock that records the exit code."""
    calls = {}

    def fake_exit(code=0):
        calls["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", fake_exit)
    return calls


def test_validation_success(monkeypatch, patch_sys_exit):
    """When the validator reports success, the script exits with 0."""
    # Patch the validator to return True (success).
    monkeypatch.setattr(
        run_citation_validation,
        "validate_citations_main",
        lambda: True,
    )
    with pytest.raises(SystemExit) as excinfo:
        run_citation_validation.main()
    assert excinfo.value.code == 0
    assert patch_sys_exit["code"] == 0


def test_validation_failure(monkeypatch, patch_sys_exit):
    """When the validator reports failure, the script exits with 1."""
    # Patch the validator to return False (failure).
    monkeypatch.setattr(
        run_citation_validation,
        "validate_citations_main",
        lambda: False,
    )
    with pytest.raises(SystemExit) as excinfo:
        run_citation_validation.main()
    assert excinfo.value.code == 1
    assert patch_sys_exit["code"] == 1


def test_validation_exception(monkeypatch, patch_sys_exit):
    """If the validator raises an exception, the script exits with 1."""
    def raise_error():
        raise RuntimeError("unexpected error")

    monkeypatch.setattr(
        run_citation_validation,
        "validate_citations_main",
        raise_error,
    )
    with pytest.raises(SystemExit) as excinfo:
        run_citation_validation.main()
    assert excinfo.value.code == 1
    assert patch_sys_exit["code"] == 1