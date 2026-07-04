"""
Importance profile schema definitions.
Defines the structure for feature importance scores per window.
"""
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ImportanceProfile:
    """
    Represents the feature importance profile for a specific window.
    """
    window_id: int
    model_type: str
    r_squared: float
    is_valid: bool
    features: List[str]
    importance_scores: List[float]
    ranking: Dict[str, int]  # feature_name -> rank (1-based)

@dataclass
class AggregatedStats:
    """
    Aggregated statistics across all windows.
    """
    total_windows: int
    valid_windows: int
    mean_r_squared: float
    mean_importance_stability: float  # Average variance of importance scores across windows
    dropped_features_count: int