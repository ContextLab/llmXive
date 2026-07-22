"""
Data schemas and validation logic for llmXive Kairos project.
"""
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal
from enum import Enum
import json
import numpy as np
import logging

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger

logger = get_logger(__name__)

class QuantizationLevel(Enum):
    LOW = 4
    MEDIUM = 8
    HIGH = 16

@dataclass
class DiscreteStateVector:
    """Represents a quantized state vector."""
    values: List[int]
    bits: int
    episode_id: int

    def __post_init__(self):
        validate_quantization_level(self.bits)
        if not all(isinstance(x, int) for x in self.values):
            raise ValueError("All values in state vector must be integers.")
        if not all(0 <= x < (2 ** self.bits) for x in self.values):
            raise ValueError(f"All values must be in range [0, {2 ** self.bits - 1}]")

@dataclass
class ErrorMetric:
    """Represents an error metric result."""
    mse: float
    horizon: int
    p_value: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None

def validate_quantization_level(bits: int) -> bool:
    """Validate that the quantization level is supported."""
    if bits not in [4, 8, 16]:
        raise ValueError(f"Unsupported quantization level: {bits}. Must be 4, 8, or 16.")
    return True

def validate_state_vector_consistency(state_vector: DiscreteStateVector) -> bool:
    """Validate the consistency of a state vector."""
    if len(state_vector.values) == 0:
        raise ValueError("State vector cannot be empty.")
    return True

def clamp_to_bin(arr: np.ndarray, bits: int) -> np.ndarray:
    """Clamp an array to the valid range for a given bit depth."""
    max_val = (2 ** bits) - 1
    return np.clip(arr, 0, max_val)

def calculate_mse(original: np.ndarray, quantized: np.ndarray) -> float:
    """Calculate Mean Squared Error between original and quantized vectors."""
    if original.shape != quantized.shape:
        raise ValueError("Arrays must have the same shape.")
    return float(np.mean((original - quantized) ** 2))
