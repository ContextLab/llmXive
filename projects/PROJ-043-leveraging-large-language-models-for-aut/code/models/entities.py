"""
Base data models for the LLM Refactoring research pipeline.

Defines core entities for function samples and metric deltas.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError
import hashlib


class FunctionSample(BaseModel):
    """
    Represents a single Python function sample extracted from a dataset.

    Attributes:
        code (str): The raw source code of the function.
        metrics (dict): A dictionary of computed structural metrics (e.g., LOC, complexity).
        hash (str): A unique SHA-256 hash of the code string for caching and deduplication.
    """
    code: str = Field(..., description="Raw source code of the function")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Computed structural metrics")
    hash: str = Field(..., description="SHA-256 hash of the code")

    @validator('hash')
    def validate_hash_format(cls, v):
        """Ensure the hash is a valid hexadecimal string of expected length."""
        if not v or len(v) != 64:
            raise ValueError("Hash must be a 64-character hexadecimal string (SHA-256).")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Hash must contain only hexadecimal characters.")
        return v

    @classmethod
    def from_code(cls, code: str, metrics: Dict[str, Any] = None) -> 'FunctionSample':
        """
        Factory method to create a FunctionSample from code, automatically computing the hash.

        Args:
            code (str): The source code.
            metrics (dict, optional): Pre-computed metrics. Defaults to empty dict.

        Returns:
            FunctionSample: A new instance with the computed hash.
        """
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
        return cls(code=code, metrics=metrics or {}, hash=code_hash)


class MetricDelta(BaseModel):
    """
    Represents the difference in quality metrics between two versions of code
    (e.g., Original vs. Refactored, or Original vs. Baseline).

    Attributes:
        complexity_delta (float): Change in Cyclomatic Complexity (Refactored - Original).
        pylint_delta (float): Change in Pylint score (Refactored - Original).
        maintainability_delta (float): Change in Maintainability Index (Refactored - Original).
    """
    complexity_delta: float = Field(..., description="Delta in cyclomatic complexity")
    pylint_delta: float = Field(..., description="Delta in pylint score")
    maintainability_delta: float = Field(..., description="Delta in maintainability index")

    @validator('complexity_delta', 'pylint_delta', 'maintainability_delta')
    def validate_numeric(cls, v):
        """Ensure delta values are finite numbers."""
        if not isinstance(v, (int, float)):
            raise ValueError("Delta values must be numeric.")
        if v != v:  # Check for NaN
            raise ValueError("Delta values cannot be NaN.")
        if abs(v) == float('inf'):
            raise ValueError("Delta values cannot be infinite.")
        return v

    def is_significant(self, threshold: float = 0.0) -> bool:
        """
        Check if any delta exceeds a given absolute threshold.

        Args:
            threshold (float): The minimum absolute change to consider significant.

        Returns:
            bool: True if any delta's absolute value is greater than threshold.
        """
        return (
            abs(self.complexity_delta) > threshold or
            abs(self.pylint_delta) > threshold or
            abs(self.maintainability_delta) > threshold
        )