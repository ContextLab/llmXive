"""
Data model definitions for the gravitational wave analysis pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class StrainEvent:
    """Represents a gravitational wave strain event."""
    event_id: str
    detector: str
    time: float
    strain_data: np.ndarray
    sampling_rate: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResolutionConfig:
    """Configuration for data resolution (downsampling/quantization)."""
    sampling_rate: int  # Hz
    bit_depth: int      # bits
    quantization_type: str = "float" # "float", "int"

@dataclass
class PosteriorDistribution:
    """Represents a posterior distribution from Bayesian inference."""
    event_id: str
    resolution_config: ResolutionConfig
    samples: Dict[str, np.ndarray]
    log_weights: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_inconclusive: bool = False

@dataclass
class BiasMetric:
    """Metrics quantifying bias and divergence."""
    event_id: str
    resolution_config: ResolutionConfig
    hellinger_distance: float
    mass_bias: float
    spin_bias: float
    catalog_ci_exceeded: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
