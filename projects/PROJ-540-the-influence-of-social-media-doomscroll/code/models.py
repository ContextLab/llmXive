from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from exceptions import DataValidationError

@dataclass
class SurveyResponse:
    """Data model for a single survey response."""
    news_exposure_freq: Optional[float] = None
    anxiety_score: Optional[float] = None
    baseline_anxiety: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'news_exposure_freq': self.news_exposure_freq,
            'anxiety_score': self.anxiety_score,
            'baseline_anxiety': self.baseline_anxiety,
            'age': self.age,
            'gender': self.gender,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurveyResponse':
        """Create instance from dictionary."""
        return cls(
            news_exposure_freq=data.get('news_exposure_freq'),
            anxiety_score=data.get('anxiety_score'),
            baseline_anxiety=data.get('baseline_anxiety'),
            age=data.get('age'),
            gender=data.get('gender'),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        )

@dataclass
class RegressionModel:
    """Data model for regression model results."""
    coefficients: Dict[str, float] = field(default_factory=dict)
    p_values: Dict[str, float] = field(default_factory=dict)
    r_squared: Optional[float] = None
    adj_r_squared: Optional[float] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'coefficients': self.coefficients,
            'p_values': self.p_values,
            'r_squared': self.r_squared,
            'adj_r_squared': self.adj_r_squared,
            'diagnostics': self.diagnostics,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegressionModel':
        """Create instance from dictionary."""
        return cls(
            coefficients=data.get('coefficients', {}),
            p_values=data.get('p_values', {}),
            r_squared=data.get('r_squared'),
            adj_r_squared=data.get('adj_r_squared'),
            diagnostics=data.get('diagnostics', {}),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        )