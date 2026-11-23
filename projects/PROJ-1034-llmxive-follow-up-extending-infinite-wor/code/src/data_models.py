"""
Core data models for the llmXive simulation pipeline.

Defines the primary data structures for tracking simulation runs,
metric records, and parameter configurations.
"""
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class SimulationRun:
    """
    Represents a single execution of a simulation (either Eco-Director or Neural Baseline).
    
    Attributes:
        run_id: Unique identifier for this run (UUID).
        simulation_type: 'eco_director' or 'neural_baseline'.
        start_time: ISO format timestamp of when the run started.
        end_time: ISO format timestamp of when the run ended (or None if ongoing).
        status: Current status ('running', 'completed', 'failed', 'timeout', 'out_of_memory').
        config_hash: Hash of the configuration used for reproducibility.
        parameters: Dictionary of all parameters used in this run.
        total_steps: Total number of time-steps executed.
        target_steps: Target number of steps defined in config.
        final_metrics: Summary metrics calculated at the end of the run.
        flags: List of flags indicating special conditions (e.g., 'Power-Limited', 'Time-Bound').
    """
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    simulation_type: str = "eco_director"
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    status: str = "running"
    config_hash: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    total_steps: int = 0
    target_steps: int = 0
    final_metrics: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the run to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationRun':
        """Create a SimulationRun instance from a dictionary."""
        return cls(**data)

    def mark_completed(self, metrics: Dict[str, Any], flags: Optional[List[str]] = None):
        """Mark the run as completed and record final metrics."""
        self.end_time = datetime.utcnow().isoformat()
        self.status = "completed"
        self.final_metrics = metrics
        if flags:
            self.flags.extend(flags)

    def mark_failed(self, reason: str):
        """Mark the run as failed with a specific reason."""
        self.end_time = datetime.utcnow().isoformat()
        self.status = "failed"
        self.flags.append(f"Failed: {reason}")

    def mark_timeout(self):
        """Mark the run as timed out."""
        self.end_time = datetime.utcnow().isoformat()
        self.status = "timeout"
        self.flags.append("Time-Bound")

    def mark_oom(self):
        """Mark the run as out of memory."""
        self.end_time = datetime.utcnow().isoformat()
        self.status = "out_of_memory"
        self.flags.append("Memory Explosion")


@dataclass
class MetricRecord:
    """
    Represents a single metric observation at a specific time-step.
    
    Attributes:
        run_id: ID of the parent simulation run.
        step: Time-step index (0-indexed).
        timestamp: ISO format timestamp of the recording.
        coherence_score: Measure of internal consistency (0.0 to 1.0).
        diversity_score: Measure of state variety (0.0 to 1.0).
        step_latency: Time taken to compute this step in seconds.
        memory_usage_mb: Current memory usage in MB.
        physics_violations: List of physics constraint violation descriptions.
        extra_data: Dictionary for any additional metrics or context.
    """
    run_id: str
    step: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    coherence_score: Optional[float] = None
    diversity_score: Optional[float] = None
    step_latency: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    physics_violations: List[str] = field(default_factory=list)
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the record to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricRecord':
        """Create a MetricRecord instance from a dictionary."""
        return cls(**data)

    def add_physics_violation(self, violation_desc: str):
        """Add a specific physics constraint violation to the record."""
        self.physics_violations.append(violation_desc)


@dataclass
class ParameterGrid:
    """
    Represents a grid of parameter configurations for a sweep.
    
    Attributes:
        grid_id: Unique identifier for this grid configuration.
        name: Human-readable name for the grid.
        parameters: Dictionary mapping parameter names to lists of possible values.
        created_at: Timestamp of grid creation.
        generated_combinations: List of all unique parameter combinations (generated on demand).
    """
    grid_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default_grid"
    parameters: Dict[str, List[Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    _combinations: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "grid_id": self.grid_id,
            "name": self.name,
            "parameters": self.parameters,
            "created_at": self.created_at,
            "generated_combinations": self.get_combinations()
        }

    def to_json(self) -> str:
        """Serialize the grid to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterGrid':
        """Create a ParameterGrid instance from a dictionary."""
        instance = cls(
            grid_id=data.get("grid_id", str(uuid.uuid4())),
            name=data.get("name", "default_grid"),
            parameters=data.get("parameters", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat())
        )
        # Pre-compute combinations if provided in data
        if "generated_combinations" in data and data["generated_combinations"]:
            instance._combinations = data["generated_combinations"]
        return instance

    def get_combinations(self) -> List[Dict[str, Any]]:
        """
        Generate all unique parameter combinations using Cartesian product.
        
        Returns:
            List of dictionaries, where each dictionary represents one configuration.
        """
        if self._combinations is not None:
            return self._combinations

        if not self.parameters:
            self._combinations = [{}]
            return self._combinations

        keys = list(self.parameters.keys())
        values = [self.parameters[k] for k in keys]

        import itertools
        combos = []
        for combination in itertools.product(*values):
            config = dict(zip(keys, combination))
            combos.append(config)

        self._combinations = combos
        return combos

    def __len__(self) -> int:
        """Return the number of configurations in the grid."""
        return len(self.get_combinations())

    def __iter__(self):
        """Iterate over configurations."""
        return iter(self.get_combinations())