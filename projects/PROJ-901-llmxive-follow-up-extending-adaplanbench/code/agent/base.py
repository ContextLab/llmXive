"""
Base abstract interface for all agent architectures in the llmXive pipeline.

This module defines the contract that both the Dual-Track and Monolithic agents
must implement to ensure consistent execution and logging across the research
pipeline.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Internal data structures for consistent logging
class ViolationType(Enum):
    """Categories of constraint violations detected during execution."""
    EXPLICIT_VIOLATION = "explicit_violation"
    IMPLICIT_UNVERIFIED = "implicit_unverified"
    FALSE_NEGATIVE = "false_negative"
    NONE = "none"


@dataclass
class ExecutionResult:
    """
    Standardized container for the output of an agent's execution on a single task.

    Attributes:
        task_id: Unique identifier of the input task.
        architecture: Name of the agent architecture (e.g., 'dual_track', 'monolithic').
        final_plan: The generated plan string.
        violations: List of detected constraint violations.
        violation_type: The primary category of violation (if any).
        score: Final execution score (0.0 to 1.0).
        logs: Detailed execution trace for debugging/analysis.
    """
    task_id: str
    architecture: str
    final_plan: str
    violations: List[Dict[str, Any]] = field(default_factory=list)
    violation_type: ViolationType = ViolationType.NONE
    score: float = 0.0
    logs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TaskContext:
    """
    Context object passed to agents containing task details and constraints.

    Attributes:
        task_id: Unique identifier.
        initial_state: Description of the starting environment.
        goal: The target objective.
        constraints: List of constraints active at the start.
        progressive_constraints: List of constraints revealed over time (if applicable).
        metadata: Additional task metadata.
    """
    task_id: str
    initial_state: str
    goal: str
    constraints: List[str] = field(default_factory=list)
    progressive_constraints: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class defining the interface for all agent implementations.

    Subclasses must implement the `execute` method to perform the planning task.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with configuration parameters.

        Args:
            config: Dictionary containing model parameters, resource limits, and other settings.
        """
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, context: TaskContext) -> ExecutionResult:
        """
        Execute the agent on the provided task context.

        This is the core entry point for the research pipeline. It must return
        a standardized ExecutionResult containing the plan, any violations detected,
        and the final score.

        Args:
            context: The TaskContext containing the problem definition and constraints.

        Returns:
            ExecutionResult: The outcome of the execution, including the plan and metrics.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
            RuntimeError: If execution fails due to resource limits or model errors.
        """
        pass

    def _log_event(self, logs: List[Dict[str, Any]], event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Helper method to append structured logs to the execution trace.

        Args:
            logs: The list to append to.
            event_type: Type of event (e.g., 'step', 'violation', 'constraint_reveal').
            message: Human-readable description.
            data: Optional structured data associated with the event.
        """
        entry = {
            "timestamp": self._get_timestamp(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        logs.append(entry)

    def _get_timestamp(self) -> str:
        """
        Generate a ISO-format timestamp for logs.

        Returns:
            str: Current timestamp string.
        """
        from datetime import datetime
        return datetime.now().isoformat()

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the agent's internal state for a new task.

        This ensures no state leakage between tasks in the batch execution loop.
        """
        pass