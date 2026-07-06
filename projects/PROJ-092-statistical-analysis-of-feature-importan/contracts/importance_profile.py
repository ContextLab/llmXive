"""
Data schema definitions for the importance_profile entity.
Defines the structure for feature importance scores per window.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ImportanceMethod(Enum):
    """Enum for importance calculation methods."""
    PERMUTATION = "permutation"
    GAIN = "gain"
    SHAP = "shap"


@dataclass
class ImportanceScore:
    """Single feature importance score."""
    feature_name: str
    score: float
    std_dev: float = 0.0
    is_significant: bool = False

@dataclass
class ImportanceProfile:
    """
    Schema for a feature importance profile for a specific window.
    """
    window_id: int
    window_start: str
    window_end: str
    method: ImportanceMethod
    scores: List[ImportanceScore]
    model_r_squared: Optional[float] = None
    n_estimators: int = 100
    max_depth: int = 10
    seed: int = 42

    def get_ranked_features(self) -> List[str]:
        """Return feature names sorted by importance score (descending)."""
        sorted_scores = sorted(self.scores, key=lambda x: x.score, reverse=True)
        return [s.feature_name for s in sorted_scores]

    def get_score_dict(self) -> Dict[str, float]:
        """Return a dictionary mapping feature names to scores."""
        return {s.feature_name: s.score for s in self.scores}

    def to_csv_row(self) -> Dict[str, Any]:
        """Flatten profile into a dictionary suitable for CSV export."""
        row = {
            "window_id": self.window_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "method": self.method.value,
            "model_r_squared": self.model_r_squared,
        }
        # Add scores as columns
        for score_obj in self.scores:
            row[f"importance_{score_obj.feature_name}"] = score_obj.score
            row[f"std_{score_obj.feature_name}"] = score_obj.std_dev
        return row
