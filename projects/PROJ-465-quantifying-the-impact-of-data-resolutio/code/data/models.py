"""
Data model definitions for the gravitational wave resolution impact study.

This module defines the core data structures used to represent strain events,
resolution configurations, posterior distributions, and bias metrics.
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
        source: The detector or catalog source (e.g., 'GWOSC').
        start_time: The GPS start time of the event.
        end_time: The GPS end time of the event.
        snr: Signal-to-noise ratio of the event.
        data_path: Path to the raw strain data file.
    """
    event_id: str
    source: str
    start_time: float
    end_time: float
    snr: float
    data_path: str


@dataclass
class ResolutionConfig:
    """
    Configuration for data resolution (sampling rate and bit depth).

    Attributes:
        sampling_rate: The sampling rate in Hz (e.g., 4096, 2048, 1024).
        bit_depth: The bit depth for quantization (e.g., 16, 32).
        name: A human-readable name for this configuration.
    """
    sampling_rate: int
    bit_depth: int
    name: str = field(init=False)

    def __post_init__(self):
        self.name = f"{self.sampling_rate}Hz_{self.bit_depth}bit"


@dataclass
class PosteriorDistribution:
    """
    Represents a posterior distribution from Bayesian inference.

    Attributes:
        event_id: ID of the event this posterior belongs to.
        resolution_config: The resolution configuration used.
        samples: A dictionary mapping parameter names to arrays of samples.
        log_weights: Array of log weights corresponding to the samples.
        is_inconclusive: Flag indicating if the inference run was inconclusive.
        posterior_width_90_ci: The width of the 90% credible interval.
        prior_width_90_ci: The width of the prior 90% credible interval.
    """
    event_id: str
    resolution_config: ResolutionConfig
    samples: Dict[str, np.ndarray]
    log_weights: np.ndarray
    is_inconclusive: bool = False
    posterior_width_90_ci: Optional[float] = None
    prior_width_90_ci: Optional[float] = None


@dataclass
class BiasMetric:
    """
    Represents a calculated bias metric for a specific parameter.

    Attributes:
        event_id: ID of the event.
        parameter: The name of the parameter (e.g., 'mass_1', 'chi_eff').
        resolution_config: The resolution configuration used.
        bias_value: The calculated bias value.
        exceeds_threshold: Boolean indicating if bias exceeds the threshold.
        threshold_value: The threshold value used for comparison.
        hellinger_distance: The Hellinger distance between posteriors.
    """
    event_id: str
    parameter: str
    resolution_config: ResolutionConfig
    bias_value: float
    exceeds_threshold: bool
    threshold_value: float
    hellinger_distance: float
