"""
Data Models for llmXive Simulation Pipeline (T007).

Defines the core data structures used throughout the simulation and analysis
pipeline, including SimulationRun, MetricRecord, and ParameterGrid.
"""
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

@dataclass
class MetricRecord:
    """
    Represents a single metric record from a simulation step.
    
    Attributes:
        step (int): The simulation step number.
        timestamp (float): Unix timestamp of the record.
        coherence_score (Optional[float]): Coherence metric.
        diversity_score (Optional[float]): Diversity metric.
        step_latency (Optional[float]): Latency of the step in seconds.
        physics_violations (Dict[str, float]): Specific physics constraint violations.
        metadata (Dict[str, Any]): Additional metadata.
    """
    step: int
    timestamp: float
    coherence_score: Optional[float] = None
    diversity_score: Optional[float] = None
    step_latency: Optional[float] = None
    physics_violations: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricRecord':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'MetricRecord':
        return cls(**json.loads(json_str))


@dataclass
class ParameterGrid:
    """
    Represents a grid of parameters for a simulation configuration.
    
    Attributes:
        name (str): Name of the parameter grid.
        parameters (Dict[str, Any]): Dictionary of parameter names to values.
        description (Optional[str]): Description of the grid.
    """
    name: str
    parameters: Dict[str, Any]
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterGrid':
        return cls(**data)


@dataclass
class SimulationRun:
    """
    Represents a complete simulation run.
    
    Attributes:
        run_id (str): Unique identifier for the run.
        start_time (datetime): Start time of the run.
        end_time (Optional[datetime]): End time of the run.
        status (str): Status of the run (e.g., 'running', 'completed', 'failed').
        parameters (ParameterGrid): The parameters used for this run.
        metrics (List[MetricRecord]): List of metric records collected during the run.
        error_message (Optional[str]): Error message if the run failed.
    """
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "running"
    parameters: Optional[ParameterGrid] = None
    metrics: List[MetricRecord] = field(default_factory=list)
    error_message: Optional[str] = None

    def add_metric(self, metric: MetricRecord):
        self.metrics.append(metric)

    def finish(self, status: str = "completed", error_message: Optional[str] = None):
        self.end_time = datetime.now()
        self.status = status
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "parameters": self.parameters.to_dict() if self.parameters else None,
            "metrics": [m.to_dict() for m in self.metrics],
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRun':
        params = data.get("parameters")
        parameters = ParameterGrid.from_dict(params) if params else None
        
        metrics_data = data.get("metrics", [])
        metrics = [MetricRecord.from_dict(m) for m in metrics_data]
        
        return cls(
            run_id=data.get("run_id", str(uuid.uuid4())),
            start_time=datetime.fromisoformat(data["start_time"]) if "start_time" in data else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            status=data.get("status", "running"),
            parameters=parameters,
            metrics=metrics,
            error_message=data.get("error_message")
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'SimulationRun':
        return cls.from_dict(json.loads(json_str))