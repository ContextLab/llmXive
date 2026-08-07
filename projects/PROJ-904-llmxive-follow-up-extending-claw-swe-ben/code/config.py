import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import random
import numpy as np

class StrategyType(Enum):
    NAIVE = "naive"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC = "semantic"

class MemoryConstraintError(Exception):
    """Raised when memory usage exceeds the 7GB limit."""
    pass

@dataclass
class TaskInstance:
    issue_id: str
    repo_state: str
    tests: List[str]

@dataclass
class ContextConfiguration:
    model_size: str
    strategy: str

@dataclass
class ExecutionResult:
    pass_status: bool
    token_count: int
    failure_mode: str

def load_environment_config() -> Dict[str, str]:
    return {
        "HF_TOKEN": os.getenv("HF_TOKEN", ""),
        "MODEL_PATH": os.getenv("MODEL_PATH", "default")
    }

def set_global_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
