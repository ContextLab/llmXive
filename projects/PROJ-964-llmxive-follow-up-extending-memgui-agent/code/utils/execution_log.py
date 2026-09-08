"""
Execution Log Data Model

Provides a structured dataclass for recording agent decisions,
trajectory steps, and information decay events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from utils.config import get_project_root


@dataclass
class ExecutionLog:
    """
    A dataclass representing a single step or decision in an agent's execution.
    
    This model is used to record structured decision data for analysis,
    particularly for tracing information decay and dependency link failures.
    
    Attributes:
        trajectory_id: Unique identifier for the trajectory this step belongs to.
        step_index: The integer index of this step within the trajectory (0-based).
        timestamp: ISO format timestamp of when the log entry was created.
        agent_type: String identifier for the agent type (e.g., 'baseline', 'recall').
        current_state: JSON-serializable representation of the agent's current state.
        action_taken: The action or decision made by the agent at this step.
        success: Boolean indicating if the step was successful.
        failure_reason: Optional string explaining why a step failed (if success=False).
        dependency_links: List of IDs of previous steps this step depends on.
        context_window: List of strings representing the context provided to the agent.
        latency_ms: Optional float for step execution latency in milliseconds.
        metadata: Dictionary for any additional custom fields.
    """
    trajectory_id: str
    step_index: int
    agent_type: str
    current_state: Dict[str, Any]
    action_taken: str
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    failure_reason: Optional[str] = None
    dependency_links: List[str] = field(default_factory=list)
    context_window: List[str] = field(default_factory=list)
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the log entry to a dictionary for JSON serialization."""
        return {
            "trajectory_id": self.trajectory_id,
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "agent_type": self.agent_type,
            "current_state": self.current_state,
            "action_taken": self.action_taken,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "dependency_links": self.dependency_links,
            "context_window": self.context_window,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the log entry to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionLog":
        """Create an ExecutionLog instance from a dictionary."""
        return cls(
            trajectory_id=data["trajectory_id"],
            step_index=data["step_index"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            agent_type=data["agent_type"],
            current_state=data["current_state"],
            action_taken=data["action_taken"],
            success=data["success"],
            failure_reason=data.get("failure_reason"),
            dependency_links=data.get("dependency_links", []),
            context_window=data.get("context_window", []),
            latency_ms=data.get("latency_ms"),
            metadata=data.get("metadata", {})
        )

    def record_failure(self, reason: str, dependency_id: Optional[str] = None) -> None:
        """
        Helper method to mark this step as failed and record the reason.
        
        Args:
            reason: The reason for failure.
            dependency_id: Optional ID of the specific dependency that caused the failure.
        """
        self.success = False
        self.failure_reason = reason
        if dependency_id:
            self.dependency_links.append(dependency_id)


@dataclass
class TrajectoryExecutionLog:
    """
    Container for a full trajectory's execution logs.
    
    This class aggregates individual ExecutionLog entries for a single trajectory
    and provides methods for serialization and analysis.
    
    Attributes:
        trajectory_id: Unique identifier for the trajectory.
        agent_type: Type of agent that executed this trajectory.
        logs: List of ExecutionLog entries for each step.
    """
    trajectory_id: str
    agent_type: str
    logs: List[ExecutionLog] = field(default_factory=list)

    def add_log(self, log_entry: ExecutionLog) -> None:
        """Add a new log entry to the trajectory."""
        if log_entry.trajectory_id != self.trajectory_id:
            raise ValueError(
                f"Trajectory ID mismatch: expected {self.trajectory_id}, "
                f"got {log_entry.trajectory_id}"
            )
        self.logs.append(log_entry)

    def get_success_rate(self) -> float:
        """Calculate the success rate for this trajectory."""
        if not self.logs:
            return 0.0
        success_count = sum(1 for log in self.logs if log.success)
        return success_count / len(self.logs)

    def get_failure_steps(self) -> List[ExecutionLog]:
        """Return a list of all failed steps in the trajectory."""
        return [log for log in self.logs if not log.success]

    def to_jsonl(self) -> str:
        """Serialize all logs to JSONL format (one JSON object per line)."""
        return "\n".join(log.to_json() for log in self.logs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire trajectory log to a dictionary."""
        return {
            "trajectory_id": self.trajectory_id,
            "agent_type": self.agent_type,
            "total_steps": len(self.logs),
            "success_rate": self.get_success_rate(),
            "logs": [log.to_dict() for log in self.logs]
        }

    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """
        Save the trajectory logs to a file.
        
        Args:
            filepath: Optional path to save to. If None, uses default path based on trajectory_id.
        """
        if filepath is None:
            project_root = get_project_root()
            filepath = str(project_root / "data" / "results" / f"{self.trajectory_id}_log.jsonl")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_jsonl())