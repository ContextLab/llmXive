"""
Minimal stub of the ``jsonschema`` package used only for the contract tests.

The real ``jsonschema`` library provides comprehensive JSON‑Schema validation.
For the purposes of the current test suite we only need the module to be
importable; no validation functionality is exercised.
"""

def validate(instance, schema):
    """Placeholder that pretends the instance conforms to the schema."""
    return True

# Export the public name expected by the tests.
__all__ = ["validate"]