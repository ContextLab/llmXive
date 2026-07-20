"""
Data Models Module.

Defines core data structures for the gravitational wave resolution study.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class StrainEvent:
    """
    Represents a gravitational wave strain event.
    
    Attributes:
        event_id: Unique identifier for the event (e.g., 'GW150914').
        source: Origin of the data (e.g., 'GWOSC', 'Injection').
        sampling_rate: Original sampling rate in Hz.
        duration: Duration of the strain data in seconds.
        snr: Signal-to-noise ratio.
        metadata: Additional event-specific metadata.
    """
    event_id: str
    source: str
    sampling_rate: float
    duration: float
    snr: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResolutionConfig:
    """
    Represents a specific resolution configuration (downsampling/quantization).
    
    Attributes:
        sampling_rate: Target sampling rate in Hz.
        bit_depth: Bit depth for quantization (e.g., 16, 32).
        description: Human-readable description of the configuration.
    """
    sampling_rate: float
    bit_depth: int
    description: str

@dataclass
class PosteriorDistribution:
    """
    Represents a posterior distribution from Bayesian inference.
    
    Attributes:
        event_id: Associated event ID.
        resolution_config: The resolution configuration used.
        parameters: Dictionary of parameter names to their posterior samples (numpy arrays).
        status: Status of the inference run ('valid', 'inconclusive').
        width_to_prior_ratio: Ratio of posterior width to prior width.
        metadata: Additional metadata (e.g., dlogz, steps).
    """
    event_id: str
    resolution_config: ResolutionConfig
    parameters: Dict[str, np.ndarray]
    status: str = 'valid'
    width_to_prior_ratio: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BiasMetric:
    """
    Represents a calculated bias metric comparing a posterior to a baseline/truth.
    
    Attributes:
        event_id: Associated event ID.
        resolution_config: The resolution configuration used.
        parameter_name: Name of the parameter being measured.
        bias_value: Calculated bias value.
        hellinger_distance: Hellinger distance between distributions.
        exceeds_threshold: Boolean indicating if bias exceeds the catalog CI.
        catalog_ci: The catalog-reported confidence interval used for comparison.
    """
    event_id: str
    resolution_config: ResolutionConfig
    parameter_name: str
    bias_value: float
    hellinger_distance: float
    exceeds_threshold: bool
    catalog_ci: float
    metadata: Dict[str, Any] = field(default_factory=dict)
