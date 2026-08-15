"""
Base class for all data models with common serialization and validation logic.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path


class BaseModel:
    """
    Abstract base class for data models.
    Provides common serialization (to_json, from_json) and validation hooks.
    """

    def to_json(self, path: Optional[Path] = None) -> Optional[str]:
        """
        Serialize the model instance to a JSON string.
        Optionally writes to a file if `path` is provided.
        """
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, default=str)

        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str, encoding="utf-8")
            return None

        return json_str

    @classmethod
    def from_json(cls, json_str: str) -> "BaseModel":
        """
        Deserialize a JSON string into a model instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: Path) -> "BaseModel":
        """
        Load a model instance from a JSON file.
        """
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        content = path.read_text(encoding="utf-8")
        return cls.from_json(content)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.
        Override in subclasses to include specific fields.
        """
        raise NotImplementedError("Subclasses must implement to_dict()")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """
        Create a model instance from a dictionary.
        Override in subclasses to handle specific fields.
        """
        raise NotImplementedError("Subclasses must implement from_dict()")

    def validate(self) -> bool:
        """
        Validate the model's internal state.
        Returns True if valid, raises ValueError otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate()")
