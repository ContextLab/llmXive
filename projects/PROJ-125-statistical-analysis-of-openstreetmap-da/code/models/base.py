"""
Base model class providing common serialization and validation logic.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path


class BaseModel:
    """Base class for all data models with JSON serialization support."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a dictionary."""
        return self.__dict__.copy()

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize model to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str | Path) -> None:
        """Save model to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "BaseModel":
        """Load model from a JSON file."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(**data)

    @classmethod
    def validate_schema(cls, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that a dictionary contains all required fields.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValueError: If any required field is missing or None
        """
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
