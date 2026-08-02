import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Any, Literal
from enum import Enum
import json
import numpy as np

class QuantizationLevel(Enum):
    """Supported quantization levels (bits)."""
    LOW = 4
    MEDIUM = 8
    HIGH = 16

@dataclass
class DiscreteStateVector:
    """
    A discrete state vector represented as a list of integers.
    Values must be within [0, 2^bits - 1].
    """
    values: List[int]
    bits: int

@dataclass
class ErrorMetric:
    """
    Metrics calculated for error analysis.
    """
    mse: float
    p_value: Optional[float] = None
    horizon: int = 0
    confidence_interval: Optional[tuple] = None

def validate_quantization_level(level: Union[int, QuantizationLevel]) -> QuantizationLevel:
    """
    Validates and returns a QuantizationLevel enum.
    
    Args:
        level: An integer (4, 8, 16) or a QuantizationLevel enum.
    
    Returns:
        The corresponding QuantizationLevel enum.
    
    Raises:
        ValueError: If the level is not supported.
    """
    if isinstance(level, QuantizationLevel):
        return level
    
    if level in [4, 8, 16]:
        return QuantizationLevel(level)
    
    raise ValueError(f"Unsupported quantization level: {level}. Must be 4, 8, or 16.")

def validate_state_vector_consistency(vector: List[int], bits: int) -> bool:
    """
    Validates that all values in a vector are consistent with the bit depth.
    
    Args:
        vector: List of integers.
        bits: Bit depth (4, 8, 16).
    
    Returns:
        True if valid, False otherwise.
    """
    max_val = (1 << bits) - 1
    return all(0 <= v <= max_val for v in vector)

def clamp_to_bin(value: Union[int, float], bits: int) -> int:
    """
    Clamps a value to the valid range for a given bit depth.
    
    Args:
        value: The value to clamp.
        bits: Bit depth (4, 8, 16).
    
    Returns:
        The clamped integer value.
    """
    min_val = 0
    max_val = (1 << bits) - 1
    clamped = int(np.clip(value, min_val, max_val))
    return clamped

def calculate_mse(predicted: List[int], actual: List[int], bits: int) -> float:
    """
    Calculates Mean Squared Error between two discrete state vectors.
    
    Args:
        predicted: List of predicted integer values.
        actual: List of actual integer values.
        bits: Bit depth (used for normalization if needed, though MSE is absolute here).
    
    Returns:
        The MSE value.
    """
    if len(predicted) != len(actual):
        raise ValueError("Vectors must have the same length")
    
    if not predicted:
        return 0.0
    
    # Normalize by state space dimensionality if required by FR-004
    # Here we calculate raw MSE. Normalization can be applied externally.
    sq_errors = [(p - a) ** 2 for p, a in zip(predicted, actual)]
    return float(np.mean(sq_errors))