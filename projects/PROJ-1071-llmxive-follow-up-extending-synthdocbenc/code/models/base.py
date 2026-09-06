"""
Base model class with common validation and serialization logic.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar
import json
import re

T = TypeVar('T', bound='BaseModel')

class BaseModel:
    """Base class for all data models with schema validation."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """Return the schema definition for this model."""
        raise NotImplementedError("Subclasses must implement schema()")

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against the schema.
        Raises ValueError if validation fails.
        Returns cleaned data.
        """
        schema = cls.schema()
        errors = []

        # Check required fields
        for field, field_schema in schema.get('properties', {}).items():
            if field_schema.get('required', False) and field not in data:
                errors.append(f"Missing required field: {field}")

        # Type checking for present fields
        for field, value in data.items():
            if field not in schema.get('properties', {}):
                errors.append(f"Unknown field: {field}")
                continue

            field_schema = schema['properties'][field]
            expected_type = field_schema.get('type')

            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == 'integer':
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' must be integer, got {type(value).__name__}")
            elif expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be boolean, got {type(value).__name__}")
            elif expected_type == 'array':
                if not isinstance(value, list):
                    errors.append(f"Field '{field}' must be array, got {type(value).__name__}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be object, got {type(value).__name__}")

        if errors:
            raise ValueError(f"Validation failed for {cls.__name__}: {'; '.join(errors)}")

        return data

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a dictionary after validation."""
        validated = cls.validate(data)
        return cls(**validated)

    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary."""
        raise NotImplementedError("Subclasses must implement to_dict()")

    def to_json(self, indent: int = 2) -> str:
        """Convert instance to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create an instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"
