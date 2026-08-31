"""Schema for FeatureVector contract."""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FeatureVector:
    """Contract for extracted static features."""
    sample_id: str
    prompt_length: int
    mean_attention_entropy: float
    hidden_state_norm: float
    metadata: Optional[dict] = None
