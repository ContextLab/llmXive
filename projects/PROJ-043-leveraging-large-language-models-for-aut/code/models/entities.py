from typing import Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError
import hashlib
import json
from pathlib import Path

class FunctionSample(BaseModel):
    """
    Represents a single Python function sample with its metrics.
    """
    code: str
    metrics: Dict[str, Any]
    hash: str

    @validator('hash', pre=True)
    def compute_hash_if_missing(cls, v, values):
        if not v and 'code' in values:
            return hashlib.sha256(values['code'].encode('utf-8')).hexdigest()
        return v

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()

class MetricDelta(BaseModel):
    """
    Represents the delta in metrics between original and refactored code.
    """
    complexity_delta: float
    pylint_delta: float
    maintainability_delta: float

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()
