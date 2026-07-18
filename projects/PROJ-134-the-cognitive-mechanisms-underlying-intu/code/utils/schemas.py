"""
Schema definitions for ModelResult and other artifacts.
This file is referenced by T051 and used by T023.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class ModelResult:
    """
    Schema definition for the ModelResult artifact.
    Fields:
        participant_id: str
        posterior_samples: List[float] or np.array
        r_hat: float
        is_inconclusive: bool
        mle_fallback: float
    """
    
    def __init__(self, participant_id: str, posterior_samples: List[float], r_hat: float, is_inconclusive: bool, mle_fallback: float):
        self.participant_id = participant_id
        self.posterior_samples = posterior_samples
        self.r_hat = r_hat
        self.is_inconclusive = is_inconclusive
        self.mle_fallback = mle_fallback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "posterior_samples": self.posterior_samples,
            "r_hat": self.r_hat,
            "is_inconclusive": self.is_inconclusive,
            "mle_fallback": self.mle_fallback
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ModelResult':
        return ModelResult(
            participant_id=data['participant_id'],
            posterior_samples=data['posterior_samples'],
            r_hat=data['r_hat'],
            is_inconclusive=data['is_inconclusive'],
            mle_fallback=data['mle_fallback']
        )

def validate_model_result_schema(data: Dict[str, Any]) -> bool:
    """
    Validates that a dictionary matches the ModelResult schema.
    """
    required_fields = ['participant_id', 'posterior_samples', 'r_hat', 'is_inconclusive', 'mle_fallback']
    if not all(field in data for field in required_fields):
        return False
    if not isinstance(data['is_inconclusive'], bool):
        return False
    if not isinstance(data['r_hat'], (int, float)):
        return False
    if not isinstance(data['mle_fallback'], (int, float)):
        return False
    return True