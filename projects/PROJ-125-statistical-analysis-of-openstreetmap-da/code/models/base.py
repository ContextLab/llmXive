"""
Base model class providing common serialization and validation utilities.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path

class BaseModel:
    """Base class for all data models with JSON serialization support."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return self.__dict__.copy()

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize the model to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Path) -> None:
        """Save the model to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_json_file(cls, path: Path) -> "BaseModel":
        """Load a model instance from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(**data)

    @classmethod
    def validate_schema(cls, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that the data dictionary contains all required fields.
        
        Args:
            data: The dictionary to validate.
            required_fields: List of field names that must be present.
        
        Raises:
            ValueError: If any required field is missing or None.
        """
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)
        
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
