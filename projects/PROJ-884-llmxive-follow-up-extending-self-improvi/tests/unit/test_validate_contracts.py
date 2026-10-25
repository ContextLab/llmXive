"""
Unit test for the contract validation script.

The test simply imports the ``validate_contracts`` function and asserts that it
returns ``True`` when both contract files are syntactically correct.  Any
parsing error will raise, causing the test to fail.
"""

import pytest

# Import the function from the script we just added
from code.validate_contracts import validate_contracts

def test_validate_contracts_returns_true():
    """The function should return True if both schemas load without error."""
    assert validate_contracts() is True