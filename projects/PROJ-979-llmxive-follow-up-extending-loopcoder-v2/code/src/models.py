from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ConvergenceStatus(Enum):
    CONVERGED = "converged"
    CENSORED = "censored"
    UNKNOWN = "unknown"

@dataclass
class InputProblem:
    task_id: str
    prompt: str
    solution: str
    difficulty: Optional[str] = None

@dataclass
class ConvergenceTrajectory:
    task_id: str
    k_values: List[int]
    correctness: List[bool]
    first_correct_step: Optional[int] = None
    censored: bool = False
    time_to_event: Optional[int] = None
