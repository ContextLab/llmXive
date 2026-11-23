"""Schema for Prediction contract."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Prediction:
    """Contract for model predictions."""
    sample_id: str
    predicted_block_size: int
    confidence: Optional[float] = None
    model_name: Optional[str] = None
