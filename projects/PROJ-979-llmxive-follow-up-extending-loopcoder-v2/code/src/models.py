"""
Data models for the inference and convergence tracking system.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ConvergenceStatus(Enum):
    CONVERGED = "converged"
    NOT_CONVERGED = "not_converged"
    ERROR = "error"

@dataclass
class InputProblem:
    """Represents a coding problem input."""
    task_id: str
    prompt: str
    test: str
    difficulty: Optional[str] = None

@dataclass
class ConvergenceTrajectory:
    """Tracks the convergence trajectory for a problem across k iterations."""
    task_id: str
    k: int
    output: str
    is_correct: bool
    converged: bool
    first_correct_step: Optional[int] = None
    error: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[str] = None
