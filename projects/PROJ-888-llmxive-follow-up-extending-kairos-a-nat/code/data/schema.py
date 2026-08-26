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
    MEDIUM = 6
    HIGH = 8
    VERY_HIGH = 16

@dataclass
class DiscreteStateVector:
    """
    A discrete state vector represented as a list of integers.
    Values must be within [0, 2^bits - 1].
    """
    values: List[int]
    bits: int

    def __post_init__(self):
        """Validate the vector immediately upon creation."""
        if not isinstance(self.values, list):
            raise TypeError("values must be a list of integers")
        if not isinstance(self.bits, int):
            raise TypeError("bits must be an integer")
        
        max_val = (1 << self.bits) - 1
        for v in self.values:
            if not isinstance(v, int):
                raise TypeError(f"All values must be integers, got {type(v)}")
            if v < 0 or v > max_val:
                raise ValueError(f"Value {v} out of range [0, {max_val}] for {self.bits}-bit quantization")

@dataclass
class ErrorMetric:
    """
    Metrics calculated for error analysis.
    """
    mse: float
    p_value: Optional[float] = None
    horizon: int = 0
    confidence_interval: Optional[tuple] = None
    mse_ratio: Optional[float] = None
    cumulative_error_rate: Optional[float] = None

def validate_quantization_level(level: Union[int, QuantizationLevel]) -> QuantizationLevel:
    """
    Validates and returns a QuantizationLevel enum.
    
    Args:
        level: An integer (4, 6, 8, 16) or a QuantizationLevel enum.
    
    Returns:
        The corresponding QuantizationLevel enum.
    
    Raises:
        ValueError: If the level is not supported.
    """
    if isinstance(level, QuantizationLevel):
        return level
    
    valid_levels = [4, 6, 8, 16]
    if level in valid_levels:
        return QuantizationLevel(level)
    
    raise ValueError(f"Unsupported quantization level: {level}. Must be one of {valid_levels}.")

def validate_state_vector_consistency(vector: List[int], bits: int) -> bool:
    """
    Validates that all values in a vector are consistent with the bit depth.
    
    Args:
        vector: List of integers.
        bits: Bit depth (4, 6, 8, 16).
    
    Returns:
        True if valid, False otherwise.
    """
    max_val = (1 << bits) - 1
    return all(isinstance(v, int) and 0 <= v <= max_val for v in vector)

def clamp_to_bin(value: Union[int, float], bits: int) -> int:
    """
    Clamps a value to the valid range for a given bit depth.
    
    Args:
        value: The value to clamp.
        bits: Bit depth (4, 6, 8, 16).
    
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

def serialize_state_vector(vector: DiscreteStateVector) -> Dict[str, Any]:
    """
    Serializes a DiscreteStateVector to a dictionary for JSON storage.
    
    Args:
        vector: The DiscreteStateVector to serialize.
    
    Returns:
        A dictionary representation suitable for JSON.
    """
    return {
        "values": vector.values,
        "bits": vector.bits,
        "type": "DiscreteStateVector"
    }

def deserialize_state_vector(data: Dict[str, Any]) -> DiscreteStateVector:
    """
    Deserializes a dictionary back into a DiscreteStateVector.
    
    Args:
        data: The dictionary representation.
    
    Returns:
        A DiscreteStateVector instance.
    
    Raises:
        ValueError: If the data is missing required fields or has invalid type.
    """
    if data.get("type") != "DiscreteStateVector":
        raise ValueError("Invalid data type for DiscreteStateVector")
    if "values" not in data or "bits" not in data:
        raise ValueError("Missing required fields 'values' or 'bits'")
    return DiscreteStateVector(values=data["values"], bits=data["bits"])