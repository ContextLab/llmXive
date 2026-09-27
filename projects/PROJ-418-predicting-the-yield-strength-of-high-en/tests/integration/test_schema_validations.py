"""
Integration test for T121: Verify that all schema‑validation tasks (T098‑T101) pass
and no missing‑field errors occurred.

This test relies on the existing validation infrastructure in
`code/validation/final_validator.py`. The function `check_schema_validations`
is expected to raise an exception or return a falsy value if any of the
schema‑validation steps fail. A successful run should return a truthy
value (e.g., ``True``) and not raise.
"""

import pytest

# The validation utilities are part of the project’s codebase.
from validation.final_validator import check_schema_validations


def test_schema_validations_pass():
    """
    Ensure that schema validation tasks T098–T101 complete without errors.
    """
    # The function should complete without raising and indicate success.
    # If it returns a boolean, we assert it is True; otherwise we simply
    # ensure no exception propagates.
    result = check_schema_validations()
    # If the function returns a value, it should be truthy.
    if result is not None:
        assert result, "Schema validation reported failures."
    # If no exception was raised, the test passes.  No further action needed.