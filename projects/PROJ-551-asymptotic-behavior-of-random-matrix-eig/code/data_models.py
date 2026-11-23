from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EigenvalueResult(BaseModel):
    run_id: str
    eigenvalue_index: int
    value: float
    is_outlier: bool
    theoretical_bbp: float
    deviation: float

class SimulationRun(BaseModel):
    run_id: str
    timestamp: str
    seed: int
    N: int
    k: int
    theta: float
    pattern_type: str
    support_density: Optional[float] = None
    computation_time_ms: float
    empirical_bulk_edge: float
    eigenvalues: List[EigenvalueResult]
