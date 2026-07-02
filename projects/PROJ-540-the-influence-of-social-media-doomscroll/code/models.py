"""
Base data models and entities for the Doomscrolling-Anticipatory Anxiety study.

This module defines the core data structures for survey responses and regression models,
ensuring type safety and consistency across the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from exceptions import DataValidationError


@dataclass
class SurveyResponse:
    """
    Represents a single respondent's data from the survey.

    Attributes:
        response_id: Unique identifier for the response.
        news_exposure_freq: Frequency of news exposure (e.g., daily, weekly).
        anxiety_score: The measured anxiety score (outcome variable).
        baseline_anxiety: Baseline anxiety level measured prior to exposure (distinct construct).
        age: Age of the respondent.
        gender: Gender of the respondent.
        social_media_engagement: Level of engagement with social media platforms.
        general_anxiety: Proxy measure for general anxiety (if available).
        anticipatory_anxiety: Specific measure for anticipatory anxiety (if available).
        timestamp: When the response was recorded.
        raw_data: Dictionary of all raw fields from the source dataset.
    """
    response_id: str
    news_exposure_freq: float
    anxiety_score: float
    baseline_anxiety: float
    age: int
    gender: str
    social_media_engagement: Optional[float] = None
    general_anxiety: Optional[float] = None
    anticipatory_anxiety: Optional[float] = None
    timestamp: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate required fields and types after initialization."""
        required_fields = {
            'response_id': str,
            'news_exposure_freq': (int, float),
            'anxiety_score': (int, float),
            'baseline_anxiety': (int, float),
            'age': int,
            'gender': str
        }

        for field_name, expected_type in required_fields.items():
            value = getattr(self, field_name)
            if value is None:
                raise DataValidationError(f"Field '{field_name}' cannot be None.")
            if not isinstance(value, expected_type):
                raise DataValidationError(
                    f"Field '{field_name}' must be of type {expected_type}, got {type(value)}."
                )

        # Validate numeric ranges if applicable
        if self.age < 0 or self.age > 120:
            raise DataValidationError(f"Invalid age: {self.age}. Must be between 0 and 120.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary for serialization."""
        return {
            'response_id': self.response_id,
            'news_exposure_freq': self.news_exposure_freq,
            'anxiety_score': self.anxiety_score,
            'baseline_anxiety': self.baseline_anxiety,
            'age': self.age,
            'gender': self.gender,
            'social_media_engagement': self.social_media_engagement,
            'general_anxiety': self.general_anxiety,
            'anticipatory_anxiety': self.anticipatory_anxiety,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'raw_data': self.raw_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurveyResponse':
        """Create a SurveyResponse instance from a dictionary."""
        # Handle timestamp parsing if it exists
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            data['timestamp'] = datetime.fromisoformat(timestamp)

        return cls(
            response_id=data['response_id'],
            news_exposure_freq=data['news_exposure_freq'],
            anxiety_score=data['anxiety_score'],
            baseline_anxiety=data['baseline_anxiety'],
            age=data['age'],
            gender=data['gender'],
            social_media_engagement=data.get('social_media_engagement'),
            general_anxiety=data.get('general_anxiety'),
            anticipatory_anxiety=data.get('anticipatory_anxiety'),
            timestamp=data.get('timestamp'),
            raw_data=data.get('raw_data', {})
        )


@dataclass
class RegressionModel:
    """
    Represents a fitted multiple linear regression model and its diagnostics.

    This class encapsulates the results of the OLS regression fitting process,
    including coefficients, p-values, and assumption check results.

    Attributes:
        model_id: Unique identifier for the model instance.
        formula: The regression formula string used.
        coefficients: Dictionary of predictor names to their estimated coefficients.
        p_values: Dictionary of predictor names to their p-values.
        r_squared: Coefficient of determination (R^2).
        adjusted_r_squared: Adjusted R^2.
        f_statistic: F-statistic for the model.
        f_p_value: P-value for the F-statistic.
        diagnostics: Dictionary of assumption check results (linearity, homoscedasticity, etc.).
        fitted_values: List of predicted values.
        residuals: List of residuals.
        sample_size: Number of observations used in the model.
    """
    model_id: str
    formula: str
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float
    f_statistic: float
    f_p_value: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    fitted_values: List[float] = field(default_factory=list)
    residuals: List[float] = field(default_factory=list)
    sample_size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model results to a dictionary for JSON serialization."""
        return {
            'model_id': self.model_id,
            'formula': self.formula,
            'coefficients': self.coefficients,
            'p_values': self.p_values,
            'r_squared': self.r_squared,
            'adjusted_r_squared': self.adjusted_r_squared,
            'f_statistic': self.f_statistic,
            'f_p_value': self.f_p_value,
            'diagnostics': self.diagnostics,
            'sample_size': self.sample_size
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the model results to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegressionModel':
        """Create a RegressionModel instance from a dictionary."""
        return cls(
            model_id=data['model_id'],
            formula=data['formula'],
            coefficients=data['coefficients'],
            p_values=data['p_values'],
            r_squared=data['r_squared'],
            adjusted_r_squared=data['adjusted_r_squared'],
            f_statistic=data['f_statistic'],
            f_p_value=data['f_p_value'],
            diagnostics=data.get('diagnostics', {}),
            fitted_values=data.get('fitted_values', []),
            residuals=data.get('residuals', []),
            sample_size=data.get('sample_size', 0)
        )