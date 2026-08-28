"""
Base data models for the llmXive simulation pipeline.

This module defines the core data structures used throughout the project:
- SimulationRun: Represents a single execution of a simulation.
- MetricRecord: Stores individual metric measurements.
- ParameterGrid: Defines a grid of parameters for sweeping experiments.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class SimulationRun:
    """
    Represents a single execution of a simulation.

    Attributes:
        run_id: Unique identifier for this run.
        config_hash: Hash of the configuration used.
        start_time: When the run started.
        end_time: When the run ended (optional, for in-progress runs).
        status: Current status of the run (e.g., 'running', 'completed', 'failed').
        parameters: Dictionary of parameters used for this run.
        metrics_path: Path to the file where metrics are stored.
        logs_path: Path to the log file for this run.
        metadata: Additional arbitrary metadata.
    """
    run_id: str
    config_hash: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics_path: Optional[str] = None
    logs_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the SimulationRun to a dictionary."""
        return {
            "run_id": self.run_id,
            "config_hash": self.config_hash,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "parameters": self.parameters,
            "metrics_path": self.metrics_path,
            "logs_path": self.logs_path,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the SimulationRun to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationRun":
        """Create a SimulationRun from a dictionary."""
        return cls(
            run_id=data["run_id"],
            config_hash=data["config_hash"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            status=data.get("status", "running"),
            parameters=data.get("parameters", {}),
            metrics_path=data.get("metrics_path"),
            logs_path=data.get("logs_path"),
            metadata=data.get("metadata", {})
        )


@dataclass
class MetricRecord:
    """
    Stores individual metric measurements from a simulation step or aggregate.

    Attributes:
        run_id: ID of the simulation run this metric belongs to.
        step: The simulation step number (if applicable).
        timestamp: When the metric was recorded.
        metric_name: Name of the metric (e.g., 'coherence_score', 'latency').
        value: The numeric value of the metric.
        tags: Optional tags for categorizing the metric.
        metadata: Additional context about the metric.
    """
    run_id: str
    step: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metric_name: str = ""
    value: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the MetricRecord to a dictionary."""
        return {
            "run_id": self.run_id,
            "step": self.step,
            "timestamp": self.timestamp.isoformat(),
            "metric_name": self.metric_name,
            "value": self.value,
            "tags": self.tags,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the MetricRecord to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricRecord":
        """Create a MetricRecord from a dictionary."""
        return cls(
            run_id=data["run_id"],
            step=data.get("step"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metric_name=data["metric_name"],
            value=float(data["value"]),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class ParameterGrid:
    """
    Defines a grid of parameters for sweeping experiments.

    Attributes:
        name: Name of the parameter grid configuration.
        description: Human-readable description.
        parameters: Dictionary mapping parameter names to lists of values to sweep.
        created_at: When this grid was created.
        tags: Optional tags for categorization.
    """
    name: str
    parameters: Dict[str, List[Any]]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def generate_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all possible parameter combinations from the grid.

        Returns:
            A list of dictionaries, each representing a unique parameter combination.
        """
        import itertools

        keys = list(self.parameters.keys())
        values = [self.parameters[k] for k in keys]

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations

    def to_dict(self) -> Dict[str, Any]:
        """Convert the ParameterGrid to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }

    def to_json(self) -> str:
        """Serialize the ParameterGrid to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterGrid":
        """Create a ParameterGrid from a dictionary."""
        return cls(
            name=data["name"],
            parameters=data["parameters"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            tags=data.get("tags", [])
        )
