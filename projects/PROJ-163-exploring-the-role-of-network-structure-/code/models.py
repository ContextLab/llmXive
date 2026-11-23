"""
Data models for the qubit network analysis project.

Defines dataclasses for QubitDevice, GraphMetric, PerformanceMetric, and CorrelationResult.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class QubitDevice:
    """Represents a quantum device with its basic properties."""
    device_id: str
    timestamp: datetime
    coupling_map: List[List[int]]
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "coupling_map": self.coupling_map,
            "properties": self.properties
        }

@dataclass
class GraphMetric:
    """Represents a graph metric computed from a device's coupling map."""
    device_id: str
    metric_name: str
    value: float
    is_finite: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "is_finite": self.is_finite
        }

@dataclass
class PerformanceMetric:
    """Represents performance metrics (coherence, gate errors) for a device."""
    device_id: str
    timestamp: datetime
    t1_mean: float
    t2_mean: float
    cx_error_mean: float
    readout_error_mean: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "t1_mean": self.t1_mean,
            "t2_mean": self.t2_mean,
            "cx_error_mean": self.cx_error_mean,
            "readout_error_mean": self.readout_error_mean
        }

@dataclass
class CorrelationResult:
    """Represents a statistical correlation result between two metrics."""
    metric_x: str
    metric_y: str
    rho: float
    p_value: float
    adj_p_value: float
    is_significant: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_x": self.metric_x,
            "metric_y": self.metric_y,
            "rho": self.rho,
            "p_value": self.p_value,
            "adj_p_value": self.adj_p_value,
            "is_significant": self.is_significant
        }
