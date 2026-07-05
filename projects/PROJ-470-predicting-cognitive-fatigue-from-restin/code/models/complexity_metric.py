"""
Data model for complexity metrics derived from EEG segments.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Enumeration of supported complexity metric types."""
    LEMPEL_ZIV_COMPLEXITY = "lzc"
    PERMUTATION_ENTROPY = "pe"
    SAMPLE_ENTROPY = "se"
    DETERMINISM = "det"
    LAMINARITY = "lam"


@dataclass
class ComplexityMetric:
    """
    Represents a calculated complexity metric for a specific EEG segment and channel.
    
    Attributes:
        segment_id: Reference to the EEGSegment ID this metric belongs to.
        participant_id: Reference to the participant ID.
        channel_name: Name of the channel the metric was calculated on.
        metric_type: Type of complexity metric (e.g., LZC, PE).
        value: The calculated scalar value.
        parameters: Dictionary of parameters used during calculation (e.g., embedding dimension, delay).
        calculated_at: Timestamp of calculation.
        metadata: Additional context (e.g., sleep stage during calculation).
    """
    segment_id: str
    participant_id: str
    channel_name: str
    metric_type: MetricType
    value: float
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the metric object to a dictionary for serialization (e.g., to CSV/JSON).
        
        Returns:
            Dictionary representation of the metric.
        """
        return {
            "participant_id": self.participant_id,
            "segment_id": self.segment_id,
            "channel_name": self.channel_name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "parameters": self.parameters,
            "calculated_at": self.calculated_at.isoformat(),
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ComplexityMetric":
        """
        Create a ComplexityMetric instance from a dictionary.
        
        Args:
            data: Dictionary containing metric fields.
            
        Returns:
            ComplexityMetric instance.
        """
        metric_type = MetricType(data["metric_type"])
        calculated_at = data.get("calculated_at")
        if calculated_at and isinstance(calculated_at, str):
            calculated_at = datetime.fromisoformat(calculated_at)
        
        return ComplexityMetric(
            segment_id=data["segment_id"],
            participant_id=data["participant_id"],
            channel_name=data["channel_name"],
            metric_type=metric_type,
            value=data["value"],
            parameters=data.get("parameters", {}),
            calculated_at=calculated_at or datetime.now(),
            metadata=data.get("metadata", {})
        )