"""
Importance Profile Schema Definitions.

Defines the structure for storing feature importance scores
calculated for specific time windows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class ImportanceProfile:
    """
    Schema for a single window's feature importance profile.
    
    Attributes:
        window_id: Unique identifier for the time window (e.g., 'window_1', 'window_2')
        start_timestamp: ISO format start time of the window
        end_timestamp: ISO format end time of the window
        model_type: Type of model used (e.g., 'RandomForestRegressor')
        model_params: Dictionary of model hyperparameters used
        r2_score: R-squared score of the model on this window
        is_valid: Boolean indicating if the model met the R2 threshold (>= 0.8)
        feature_names: Ordered list of feature names used in the model
        importance_scores: List of importance scores corresponding to feature_names
        importance_ranks: List of ranks (1-based) corresponding to feature_names
        variance_dropped_features: List of features dropped due to zero variance
        calculation_date: ISO timestamp when importance was calculated
    """
    window_id: str
    start_timestamp: str
    end_timestamp: str
    model_type: str = "RandomForestRegressor"
    model_params: Dict[str, any] = field(default_factory=lambda: {"n_estimators": 100, "max_depth": 10, "random_state": 42})
    r2_score: Optional[float] = None
    is_valid: bool = True
    feature_names: List[str] = field(default_factory=list)
    importance_scores: List[float] = field(default_factory=list)
    importance_ranks: List[int] = field(default_factory=list)
    variance_dropped_features: List[str] = field(default_factory=list)
    calculation_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary."""
        return {
            "window_id": self.window_id,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "model_type": self.model_type,
            "model_params": self.model_params,
            "r2_score": self.r2_score,
            "is_valid": self.is_valid,
            "feature_names": self.feature_names,
            "importance_scores": self.importance_scores,
            "importance_ranks": self.importance_ranks,
            "variance_dropped_features": self.variance_dropped_features,
            "calculation_date": self.calculation_date
        }

    def get_ranked_features(self) -> List[tuple]:
        """
        Returns a list of (feature_name, score, rank) sorted by rank.
        """
        if not self.feature_names or not self.importance_ranks:
            return []
        
        # Create list of tuples and sort by rank
        ranked = []
        for i, name in enumerate(self.feature_names):
            score = self.importance_scores[i] if i < len(self.importance_scores) else 0.0
            rank = self.importance_ranks[i] if i < len(self.importance_ranks) else 0
            ranked.append((name, score, rank))
        
        return sorted(ranked, key=lambda x: x[2])
