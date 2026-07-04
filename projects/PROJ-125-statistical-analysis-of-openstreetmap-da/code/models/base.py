"""
Base model class with common serialization and validation logic.
"""
from abc import ABC
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class BaseModel(ABC):
    """Abstract base class for all data models with JSON serialization."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def to_json(self, indent: int = 2) -> str:
        """Serialize model to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, path: Path) -> None:
        """Save model state to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        logger.info(f"Model saved to {path}")

    @classmethod
    def load(cls, path: Path) -> "BaseModel":
        """Load model state from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Filter data to only include fields present in the class
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

    def validate(self) -> bool:
        """Validate model state. Override in subclasses for specific logic."""
        return True
