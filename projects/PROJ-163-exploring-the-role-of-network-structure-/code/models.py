"""
Base data models for the llmXive Superconducting Qubit Network Structure project.

This module defines the core dataclasses used to represent:
- QubitDevice: Metadata and properties of a quantum backend.
- GraphMetric: Topological descriptors of the qubit connectivity graph.
- PerformanceMetric: Hardware performance indicators (coherence, errors).
- CorrelationResult: Statistical results linking topology to performance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class QubitDevice:
    """
    Represents a quantum computing device (backend) from IBM Quantum.

    Attributes:
        device_id: Unique identifier for the device (e.g., 'ibmq_manila').
        backend_name: Human-readable name of the backend.
        num_qubits: Total number of physical qubits.
        coupling_map: List of directed edges (source, target) representing connectivity.
        basis_gates: List of native gate sets supported.
        dt: System time resolution in seconds.
        dtm: Measurement time resolution in seconds.
        processor_type: Type of processor (e.g., 'Falcon', 'Eagle').
        last_updated: Timestamp of the last calibration update.
        metadata: Raw JSON payload or additional properties not explicitly mapped.
    """
    device_id: str
    backend_name: str
    num_qubits: int
    coupling_map: List[List[int]]
    basis_gates: List[str]
    dt: Optional[float] = None
    dtm: Optional[float] = None
    processor_type: Optional[str] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the device to a dictionary for JSON/CSV serialization."""
        data = self.__dict__.copy()
        if data.get('last_updated'):
            data['last_updated'] = data['last_updated'].isoformat()
        # Convert coupling_map to list of tuples if needed, but list of lists is fine
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QubitDevice':
        """Construct a QubitDevice from a dictionary."""
        # Handle datetime parsing if string
        if 'last_updated' in data and isinstance(data['last_updated'], str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class GraphMetric:
    """
    Represents a topological metric computed from the device's coupling graph.

    Attributes:
        device_id: Reference to the QubitDevice.
        metric_name: Name of the metric (e.g., 'average_shortest_path', 'clustering_coeff').
        value: The computed numerical value.
        is_finite: Boolean flag indicating if the value is finite (not inf/nan).
        method: Description of the algorithm or library used (e.g., 'networkx').
        timestamp: When the metric was computed.
    """
    device_id: str
    metric_name: str
    value: float
    is_finite: bool
    method: str = "networkx"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            'device_id': self.device_id,
            'metric_name': self.metric_name,
            'value': self.value,
            'is_finite': self.is_finite,
            'method': self.method,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PerformanceMetric:
    """
    Represents a hardware performance indicator for a specific qubit or the device.

    Attributes:
        device_id: Reference to the QubitDevice.
        metric_name: Name of the metric (e.g., 'T1', 'T2', 'gate_error', 'readout_error').
        value: The measured value.
        unit: Unit of measurement (e.g., 'seconds', 'unitless', 'percent').
        qubit_index: Optional index of the specific qubit if the metric is qubit-specific.
        timestamp: When the metric was recorded.
    """
    device_id: str
    metric_name: str
    value: float
    unit: str
    qubit_index: Optional[int] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        d = {
            'device_id': self.device_id,
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit
        }
        if self.qubit_index is not None:
            d['qubit_index'] = self.qubit_index
        if self.timestamp:
            d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class CorrelationResult:
    """
    Represents the result of a statistical correlation test between two metrics.

    Attributes:
        metric_a: Name of the first metric (independent/topological).
        metric_b: Name of the second metric (dependent/performance).
        spearman_rho: Spearman rank correlation coefficient.
        p_value: Raw p-value from the test.
        adj_p_value: Adjusted p-value (e.g., Benjamini-Hochberg).
        is_significant: Boolean flag if adj_p_value < 0.05.
        sample_size: Number of data points used.
        method: Statistical method used (e.g., 'spearman').
        timestamp: When the analysis was run.
    """
    metric_a: str
    metric_b: str
    spearman_rho: float
    p_value: float
    adj_p_value: float
    is_significant: bool
    sample_size: int
    method: str = "spearman"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        return {
            'metric_a': self.metric_a,
            'metric_b': self.metric_b,
            'spearman_rho': self.spearman_rho,
            'p_value': self.p_value,
            'adj_p_value': self.adj_p_value,
            'is_significant': self.is_significant,
            'sample_size': self.sample_size,
            'method': self.method,
            'timestamp': self.timestamp.isoformat()
        }