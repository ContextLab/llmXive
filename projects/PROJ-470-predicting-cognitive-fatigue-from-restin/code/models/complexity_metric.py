from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json
import numpy as np

class MetricType(Enum):
    """Enumeration of supported complexity metric types."""
    LEMPEL_ZIV_COMPLEXITY = "lzc"
    PERMUTATION_ENTROPY = "pe"
    SAMPLE_ENTROPY = "sample_entropy"
    SPECTRAL_SLOPE = "spectral_slope"

@dataclass
class ComplexityMetric:
    """
    Represents a calculated complexity metric for a specific EEG segment.
    
    Attributes:
        participant_id: Unique identifier for the participant.
        channel: The EEG channel name.
        metric_type: The type of metric calculated.
        value: The calculated metric value (float).
        parameters: Dictionary of parameters used for calculation (e.g., embedding dimension).
        timestamp: When the calculation was performed.
        metadata: Additional context (e.g., fatigue score at time of recording).
    """
    participant_id: str
    channel: str
    metric_type: MetricType
    value: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure value is a valid float."""
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"value must be numeric, got {type(self.value)}")
        if np.isnan(self.value) or np.isinf(self.value):
            raise ValueError(f"value cannot be NaN or Inf, got {self.value}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary for serialization."""
        return {
            'participant_id': self.participant_id,
            'channel': self.channel,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplexityMetric':
        """Reconstruct a ComplexityMetric from a dictionary."""
        return cls(
            participant_id=data['participant_id'],
            channel=data['channel'],
            metric_type=MetricType(data['metric_type']),
            value=float(data['value']),
            parameters=data.get('parameters', {}),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            metadata=data.get('metadata', {})
        )

    def __str__(self) -> str:
        return f"{self.metric_type.value.upper()}[{self.channel}]: {self.value:.4f}"
