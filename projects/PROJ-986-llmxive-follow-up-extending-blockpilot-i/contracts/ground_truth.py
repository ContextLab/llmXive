"""Schema for GroundTruth contract."""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class GroundTruth:
    """Contract for sweep results and optimal block size."""
    sample_id: str
    block_sizes_tested: List[int]
    latencies: List[float]
    optimal_block_size: int
    winner_latency: float
    oom_occurred: bool = False
    metadata: Optional[dict] = None
