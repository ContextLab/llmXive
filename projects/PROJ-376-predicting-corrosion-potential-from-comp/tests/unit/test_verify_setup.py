"""
Unit test for ``code.utils.verify_setup`` (T001a).

The test simply imports the module and calls its ``main`` function.
If the manifest is missing or incomplete, the call will raise,
causing the test to fail.
"""

import pytest

from code.utils import verify_setup

def test_verify_setup_passes():
    """
    Ensure that the verification script runs without raising.
    """
    # The script will raise RuntimeError if anything is wrong.
    verify_setup.main()
