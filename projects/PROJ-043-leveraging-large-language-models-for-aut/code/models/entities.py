"""
Core data models for the refactoring pipeline.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError
import hashlib

class FunctionSample(BaseModel):
    """Represents a single Python function sample."""
    code: str
    metrics: Dict[str, float]
    hash: str

    @validator('hash')
    def validate_hash(cls, v, values):
        if not values.get('code'):
            return v
        # Recompute hash to ensure integrity
        computed = hashlib.sha256(values['code'].encode('utf-8')).hexdigest()
        if v != computed:
            raise ValueError("Hash mismatch")
        return v

    @classmethod
    def create(cls, code: str, metrics: Dict[str, float]) -> 'FunctionSample':
        """Factory method to create a sample with auto-computed hash."""
        h = hashlib.sha256(code.encode('utf-8')).hexdigest()
        return cls(code=code, metrics=metrics, hash=h)

class MetricDelta(BaseModel):
    """Represents the difference in metrics between original and refactored code."""
    complexity_delta: float
    pylint_delta: float
    maintainability_delta: float
