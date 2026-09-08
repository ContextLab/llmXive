"""
Contract tests for validator interface compliance.

Ensures that all validators implement the required validation interface.
"""
import pytest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ValidatorProtocol(ABC):
    @abstractmethod
    def validate(self, data: Any) -> Dict[str, Any]:
        """Validate data and return results."""
        pass

class MockValidator:
    """Mock validator to test interface compliance."""
    def validate(self, data):
        return {"valid": True}

def test_validator_implements_interface():
    """Verify that validators implement the required interface methods."""
    validator = MockValidator()
    assert hasattr(validator, 'validate')
    assert callable(validator.validate)

def test_protocol_compliance():
    """Verify that the protocol class defines required methods."""
    assert hasattr(ValidatorProtocol, 'validate')