"""
Base model class for schema validation and serialization.
"""
from typing import Any, Dict, Optional
import json
from pathlib import Path

class BaseModel:
    """Base class for data models with JSON serialization support."""
    
    def __init__(self, **kwargs):
        """Initialize model with keyword arguments."""
        self._data = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self._data.copy()
    
    def to_json(self, indent: int = 2) -> str:
        """Convert model to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, path: Path) -> None:
        """Save model to a JSON file."""
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_json(cls, path: Path) -> 'BaseModel':
        """Load model from a JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)