"""
T096-Exception: Custom Exception Definitions.

Defines the custom exception class `RealDataUnavailableError` and error messages
required by NFR-002 and FR-006.
"""
from __future__ import annotations

class RealDataUnavailableError(Exception):
    """
    Raised when real data is required but unavailable.
    
    This exception enforces the "fail loudly" constraint. It should be raised
    when a real data source cannot be fetched or is missing, and no authorized
    simulation fallback is available.
    """
    pass

# Constant error message for FR-006 violations
ERROR_MSG_FR006_MISSING_VR = (
    "FR-006 Violation: Real VR logs missing. "
    "Spec Amendment T090 is required to enable simulation mode. "
    "Please complete T090 before proceeding."
)
