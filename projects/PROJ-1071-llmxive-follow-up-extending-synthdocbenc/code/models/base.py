"""
Base model class providing common serialization and validation utilities.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar
import json
import re

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """
    Abstract base class for all data models.
    Provides standard serialization and validation methods.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                result[key] = value
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert model instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create an instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str], model_name: str) -> None:
        """
        Validate that all required fields are present in the data.
        Raises ValueError if any required field is missing.
        """
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields in {model_name}: {missing}")

    @staticmethod
    def validate_type(data: Dict[str, Any], field: str, expected_type: type, model_name: str) -> None:
        """
        Validate that a field has the expected type.
        Raises TypeError if the type does not match.
        """
        if field in data and not isinstance(data[field], expected_type):
            raise TypeError(
                f"Field '{field}' in {model_name} must be of type {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )
