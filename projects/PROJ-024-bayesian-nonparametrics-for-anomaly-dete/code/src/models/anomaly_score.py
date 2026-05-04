"""
Anomaly Score dataclass definition with support for uncertainty estimates.

This module provides the core AnomalyScore dataclass used throughout the
DPGMM anomaly detection pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class AnomalyScore:
    """
    Core anomaly score dataclass.
    
    Represents the anomaly score for a single observation, computed as
    the negative log posterior probability under the DPGMM model.
    """
    
    # Core score information
    anomaly_score: float = 0.0  # Negative log posterior probability
    is_anomaly: bool = False  # Binary anomaly flag
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Optional diagnostic information
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'anomaly_score': float(self.anomaly_score),
            'is_anomaly': bool(self.is_anomaly),
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'metadata': self.metadata or {},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnomalyScore':
        """Create from dictionary."""
        timestamp = data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            anomaly_score=float(data.get('anomaly_score', 0.0)),
            is_anomaly=bool(data.get('is_anomaly', False)),
            timestamp=timestamp,
            metadata=data.get('metadata', {}),
        )

def main():
    """Main entry point for testing."""
    score = AnomalyScore(anomaly_score=15.5, is_anomaly=True)
    print(f"Anomaly Score: {score.to_dict()}")
    return score

if __name__ == '__main__':
    main()
