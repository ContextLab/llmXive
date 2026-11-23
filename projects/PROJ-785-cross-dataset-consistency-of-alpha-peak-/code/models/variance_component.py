"""
Data model for Variance Component analysis results.
Matches the schema expected by contracts and used throughout the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class VarianceComponent:
    """
    Represents a variance component from a mixed-effects model.
    
    Attributes:
        component_name: Name of the variance component (e.g., 'dataset_source')
        variance_estimate: Estimated variance value
        proportion: Proportion of total variance (0.0 to 1.0)
        confidence_interval: Optional 95% CI tuple (lower, upper)
        p_value: Optional p-value from likelihood ratio test
        model_formula: The formula used to fit the model
        dataset_id: Source dataset (if applicable)
        created_at: Timestamp of analysis
    """
    component_name: str
    variance_estimate: float
    proportion: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    p_value: Optional[float] = None
    model_formula: Optional[str] = None
    dataset_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the component to a dictionary for serialization."""
        ci = None
        if self.confidence_interval:
            ci = list(self.confidence_interval)

        return {
            "component_name": self.component_name,
            "variance_estimate": self.variance_estimate,
            "proportion": self.proportion,
            "confidence_interval": ci,
            "p_value": self.p_value,
            "model_formula": self.model_formula,
            "dataset_id": self.dataset_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VarianceComponent":
        """Create a VarianceComponent instance from a dictionary."""
        ci = data.get("confidence_interval")
        if ci:
            ci = tuple(ci)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            component_name=data["component_name"],
            variance_estimate=data["variance_estimate"],
            proportion=data.get("proportion"),
            confidence_interval=ci,
            p_value=data.get("p_value"),
            model_formula=data.get("model_formula"),
            dataset_id=data.get("dataset_id"),
            created_at=created_at or datetime.utcnow(),
        )

@dataclass
class VarianceAnalysisResult:
    """
    Container for the full variance decomposition analysis.
    
    Attributes:
        components: List of VarianceComponent objects
        total_variance: Total variance explained by the model
        residual_variance: Residual variance
        model_fit_stats: Dictionary of model fit statistics (AIC, BIC, etc.)
        created_at: Timestamp of analysis
    """
    components: List[VarianceComponent] = field(default_factory=list)
    total_variance: Optional[float] = None
    residual_variance: Optional[float] = None
    model_fit_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis result to a dictionary."""
        return {
            "components": [c.to_dict() for c in self.components],
            "total_variance": self.total_variance,
            "residual_variance": self.residual_variance,
            "model_fit_stats": self.model_fit_stats,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VarianceAnalysisResult":
        """Create a VarianceAnalysisResult instance from a dictionary."""
        components = [
            VarianceComponent.from_dict(c) for c in data.get("components", [])
        ]
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            components=components,
            total_variance=data.get("total_variance"),
            residual_variance=data.get("residual_variance"),
            model_fit_stats=data.get("model_fit_stats", {}),
            created_at=created_at or datetime.utcnow(),
        )
