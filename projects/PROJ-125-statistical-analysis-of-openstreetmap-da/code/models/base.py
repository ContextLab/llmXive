"""
Base model class providing common serialization and validation logic.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path


class BaseModel:
    """
    Abstract base class for all data models in the pipeline.
    Provides common methods for validation, serialization, and file I/O.
    """

    def validate(self) -> bool:
        """
        Validate the integrity of the model data.
        Subclasses must override this to implement specific checks.
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.
        """
        raise NotImplementedError("Subclasses must implement to_dict()")

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize the model to a JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, path: Path) -> None:
        """
        Save the model state to a JSON file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "BaseModel":
        """
        Load a model instance from a JSON file.
        Subclasses must override this to handle specific constructors.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Default factory logic; subclasses should override for specific types
        return cls(**data)
