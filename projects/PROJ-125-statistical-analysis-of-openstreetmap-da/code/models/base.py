"""
Base model class with common validation and serialization utilities.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseModel:
    """Base class for all data models with common serialization methods."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_') and v is not None
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize model to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save_to_file(self, path: str | Path) -> None:
        """Save model metadata to a JSON file."""
        filepath = Path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        logger.info(f"Saved model metadata to {filepath}")

    @classmethod
    def load_from_file(cls, path: str | Path) -> "BaseModel":
        """Load model metadata from a JSON file and instantiate."""
        filepath = Path(path)
        if not filepath.exists():
            raise FileNotFoundError(f"Metadata file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        cls._validate_required_fields(data)
        return cls(**data)

    @classmethod
    def _validate_required_fields(cls, data: Dict[str, Any]) -> None:
        """Validate that required fields are present in loaded data."""
        # Override in subclasses to define required fields
        pass
