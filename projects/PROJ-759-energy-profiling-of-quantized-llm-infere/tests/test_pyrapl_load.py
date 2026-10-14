"""
Test that the pyRAPL library can be imported and initialised.

The benchmark's ``--dry-run`` mode relies on this capability; a passing
test guarantees that the quickstart verification step will succeed.
"""

import pytest

def test_pyrapl_import_and_setup():
    try:
        import pyRAPL
    except Exception as exc:
        pytest.fail(f"Importing pyRAPL raised an exception: {exc}")

    try:
        pyRAPL.setup()
    except Exception as exc:
        pytest.fail(f"pyRAPL.setup() raised an exception: {exc}")

    # If we reach this point the library is available.
    assert True
