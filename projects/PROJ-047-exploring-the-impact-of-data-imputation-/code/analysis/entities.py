from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

@dataclass
class SyntheticDataset:
    X: np.ndarray
    T: np.ndarray
    Y: np.ndarray
    ground_truth_ate: float
    seed: int

@dataclass
class ImputationResult:
    method: str
    imputed_data: pd.DataFrame
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CausalEstimate:
    method: str
    estimator: str
    ate: float
    se: float
    ci_lower: float
    ci_upper: float
    p_value: Optional[float] = None
