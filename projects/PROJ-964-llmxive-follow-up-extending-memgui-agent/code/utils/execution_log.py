"""
Execution Log Module

Provides data structures for structured decision recording and trajectory execution tracking.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from utils.config import get_project_root

@dataclass
class ExecutionLog:
    """
    Base data model for recording a single execution decision or step.
    
    Attributes:
        timestamp: ISO format timestamp of the log entry.
        agent_id: Identifier of the agent that generated the log.
        trajectory_id: Identifier of the trajectory this log belongs to.
        step_index: The step number in the trajectory (0-indexed).
        action: The action taken by the agent.
        observation: The observation resulting from the action.
        success: Boolean indicating if the step was successful.
        memory_snapshot: Optional dictionary containing memory metrics at this step.
        latency_ms: Execution latency in milliseconds.
        metadata: Additional key-value pairs for context.
    """
    timestamp: str
    agent_id: str
    trajectory_id: str
    step_index: int
    action: str
    observation: str
    success: bool
    memory_snapshot: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the log entry to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "trajectory_id": self.trajectory_id,
            "step_index": self.step_index,
            "action": self.action,
            "observation": self.observation,
            "success": self.success,
            "memory_snapshot": self.memory_snapshot,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the log entry to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionLog':
        """Create an ExecutionLog instance from a dictionary."""
        return cls(
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            agent_id=data["agent_id"],
            trajectory_id=data["trajectory_id"],
            step_index=data["step_index"],
            action=data["action"],
            observation=data["observation"],
            success=data["success"],
            memory_snapshot=data.get("memory_snapshot"),
            latency_ms=data.get("latency_ms"),
            metadata=data.get("metadata", {})
        )


@dataclass
class TrajectoryExecutionLog:
    """
    Aggregated log for an entire trajectory, containing a sequence of ExecutionLogs.
    
    Attributes:
        trajectory_id: Unique identifier for the trajectory.
        agent_id: Identifier of the agent that executed the trajectory.
        start_time: ISO timestamp when the trajectory execution started.
        end_time: ISO timestamp when the trajectory execution finished.
        steps: List of ExecutionLog entries for each step.
        final_success: Boolean indicating if the entire trajectory succeeded.
        total_latency_ms: Sum of latencies for all steps.
        dependency_links: List of strings describing dependency links encountered.
    """
    trajectory_id: str
    agent_id: str
    start_time: str
    end_time: str
    steps: List[ExecutionLog] = field(default_factory=list)
    final_success: bool = True
    total_latency_ms: float = 0.0
    dependency_links: List[str] = field(default_factory=list)

    def add_step(self, step_log: ExecutionLog) -> None:
        """Add a step log to the trajectory."""
        self.steps.append(step_log)
        if step_log.latency_ms is not None:
            self.total_latency_ms += step_log.latency_ms
        if not step_log.success:
            self.final_success = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the trajectory log to a dictionary."""
        return {
            "trajectory_id": self.trajectory_id,
            "agent_id": self.agent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [step.to_dict() for step in self.steps],
            "final_success": self.final_success,
            "total_latency_ms": self.total_latency_ms,
            "dependency_links": self.dependency_links
        }

    def to_json(self) -> str:
        """Serialize the trajectory log to a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrajectoryExecutionLog':
        """Create a TrajectoryExecutionLog instance from a dictionary."""
        steps = [ExecutionLog.from_dict(s) for s in data.get("steps", [])]
        return cls(
            trajectory_id=data["trajectory_id"],
            agent_id=data["agent_id"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            steps=steps,
            final_success=data.get("final_success", True),
            total_latency_ms=data.get("total_latency_ms", 0.0),
            dependency_links=data.get("dependency_links", [])
        )

    def get_failure_step(self) -> Optional[ExecutionLog]:
        """Return the first step that failed, or None if all succeeded."""
        for step in self.steps:
            if not step.success:
                return step
        return None

    def get_step_by_index(self, index: int) -> Optional[ExecutionLog]:
        """Retrieve a specific step by its index."""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def get_memory_at_step(self, index: int) -> Optional[Dict[str, Any]]:
        """Get memory snapshot at a specific step index."""
        step = self.get_step_by_index(index)
        if step and step.memory_snapshot:
            return step.memory_snapshot
        return None