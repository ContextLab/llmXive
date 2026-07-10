"""
Pydantic model for ModelOutput results.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModelOutput(BaseModel):
    """
    Container for model training and evaluation results.

    Attributes:
        run_id: Unique identifier for this model run.
        model_type: Type of model (e.g., 'PGLS', 'RandomForest').
        r_squared: Coefficient of determination.
        adjusted_r_squared: Adjusted R-squared.
        feature_importance: Dictionary of feature names to importance scores.
        hyperparameters: Dictionary of used hyperparameters.
        timestamp: Timestamp of the run.
        metadata: Additional metadata (e.g., cross-validation scores, p-values).
    """
    model_config = ConfigDict(from_attributes=True)

    run_id: str = Field(..., description="Unique run identifier")
    model_type: str = Field(..., description="Model type")
    r_squared: Optional[float] = Field(None, description="R-squared score")
    adjusted_r_squared: Optional[float] = Field(None, description="Adjusted R-squared")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance scores")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    timestamp: datetime = Field(default_factory=datetime.now, description="Run timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    def is_significant(self, threshold: float = 0.0) -> bool:
        """Check if R-squared is above a threshold."""
        if self.r_squared is None:
            return False
        return self.r_squared > threshold
