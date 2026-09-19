from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class QubitDevice:
    """
    Represents a single superconducting qubit device (backend) from IBM Quantum.
    Contains topology and performance characteristics extracted from calibration data.
    """
    device_id: str
    backend_name: str
    qubit_count: int
    coupling_map: List[List[int]]
    timestamp: datetime
    t1_times: List[float]  # Microseconds
    t2_times: List[float]  # Microseconds
    readout_errors: List[float]
    cx_errors: List[float]  # Mean CNOT error rate
    gate_errors: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "device_id": self.device_id,
            "backend_name": self.backend_name,
            "qubit_count": self.qubit_count,
            "coupling_map": self.coupling_map,
            "timestamp": self.timestamp.isoformat(),
            "t1_times": self.t1_times,
            "t2_times": self.t2_times,
            "readout_errors": self.readout_errors,
            "cx_errors": self.cx_errors,
            "gate_errors": self.gate_errors,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QubitDevice":
        """Deserialize from dictionary."""
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        return cls(
            device_id=data["device_id"],
            backend_name=data["backend_name"],
            qubit_count=data["qubit_count"],
            coupling_map=data["coupling_map"],
            timestamp=timestamp,
            t1_times=data.get("t1_times", []),
            t2_times=data.get("t2_times", []),
            readout_errors=data.get("readout_errors", []),
            cx_errors=data.get("cx_errors", []),
            gate_errors=data.get("gate_errors", {}),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "QubitDevice":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class GraphMetric:
    """
    Represents a topological metric computed for a device's coupling graph.
    """
    device_id: str
    metric_name: str
    value: float
    is_finite: bool = True
    component_count: int = 1  # Number of connected components
    is_connected: bool = True
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "is_finite": self.is_finite,
            "component_count": self.component_count,
            "is_connected": self.is_connected,
            "timestamp": self.timestamp.isoformat()
        }

    def to_row(self) -> List[Any]:
        """Convert to a row list for CSV export."""
        return [
            self.device_id,
            self.metric_name,
            self.value,
            self.is_finite,
            self.component_count,
            self.is_connected,
            self.timestamp.isoformat()
        ]


@dataclass
class PerformanceMetric:
    """
    Represents aggregated performance metrics for a device.
    """
    device_id: str
    mean_t1: float
    mean_t2: float
    mean_readout_error: float
    mean_cx_error: float
    qubit_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "mean_t1": self.mean_t1,
            "mean_t2": self.mean_t2,
            "mean_readout_error": self.mean_readout_error,
            "mean_cx_error": self.mean_cx_error,
            "qubit_count": self.qubit_count,
            "timestamp": self.timestamp.isoformat()
        }

    def to_row(self) -> List[Any]:
        """Convert to a row list for CSV export."""
        return [
            self.device_id,
            self.mean_t1,
            self.mean_t2,
            self.mean_readout_error,
            self.mean_cx_error,
            self.qubit_count,
            self.timestamp.isoformat()
        ]


@dataclass
class CorrelationResult:
    """
    Represents the result of a statistical correlation analysis between
    a graph metric and a performance metric.
    """
    metric_a: str  # Graph metric name (e.g., "avg_shortest_path")
    metric_b: str  # Performance metric name (e.g., "mean_cx_error")
    spearman_rho: float
    p_value: float
    adj_p_value: float  # Benjamini-Hochberg adjusted p-value
    is_significant: bool
    sample_size: int
    is_excluded: bool = False
    exclusion_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "spearman_rho": self.spearman_rho,
            "p_value": self.p_value,
            "adj_p_value": self.adj_p_value,
            "is_significant": self.is_significant,
            "sample_size": self.sample_size,
            "is_excluded": self.is_excluded,
            "exclusion_reason": self.exclusion_reason,
            "timestamp": self.timestamp.isoformat()
        }

    def to_row(self) -> List[Any]:
        """Convert to a row list for CSV export."""
        return [
            self.metric_a,
            self.metric_b,
            self.spearman_rho,
            self.p_value,
            self.adj_p_value,
            self.is_significant,
            self.sample_size,
            self.is_excluded,
            self.exclusion_reason or "",
            self.timestamp.isoformat()
        ]