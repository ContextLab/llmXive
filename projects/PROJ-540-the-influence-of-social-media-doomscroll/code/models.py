"""
Data models for the Doomscrolling Anxiety study.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from exceptions import DataValidationError

@dataclass
class SurveyResponse:
    """Represents a single survey response."""
    news_exposure_freq: float
    anxiety_score: float
    baseline_anxiety: float
    age: int
    gender: str
    id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'news_exposure_freq': self.news_exposure_freq,
            'anxiety_score': self.anxiety_score,
            'baseline_anxiety': self.baseline_anxiety,
            'age': self.age,
            'gender': self.gender,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurveyResponse':
        # Basic validation
        required = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
        missing = [k for k in required if k not in data]
        if missing:
            raise DataValidationError(f"Missing fields for SurveyResponse: {missing}")
        
        return cls(
            id=data.get('id'),
            news_exposure_freq=float(data['news_exposure_freq']),
            anxiety_score=float(data['anxiety_score']),
            baseline_anxiety=float(data['baseline_anxiety']),
            age=int(data['age']),
            gender=str(data['gender']),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        )

@dataclass
class RegressionModel:
    """Represents a fitted regression model's metadata."""
    formula: str
    coefficients: Dict[str, float]
    r_squared: float
    n_obs: int
    fitted_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'formula': self.formula,
            'coefficients': self.coefficients,
            'r_squared': self.r_squared,
            'n_obs': self.n_obs,
            'fitted_at': self.fitted_at.isoformat()
        }
