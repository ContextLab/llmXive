"""
Pydantic models for Model Output and Results.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime


class ModelOutput(BaseModel):
    """
    Model representing the output of a predictive model.
    """
    model_config = ConfigDict(populate_by_name=True)

    model_id: str = Field(..., description="Unique identifier for the model run")
    model_type: str = Field(..., description="Type of model (e.g., 'PGLS', 'Random Forest')")
    species_id: Optional[str] = Field(None, description="Species ID if prediction is per-species")
    predicted_metabolite_class: Optional[str] = Field(None, description="Predicted metabolite class")
    predicted_abundance: Optional[float] = Field(None, ge=0.0, description="Predicted abundance value")
    prediction_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the prediction"
    )
    features_used: Optional[List[str]] = Field(
        default_factory=list,
        description="List of features (BGC types) used in the prediction"
    )
    feature_importance: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Mapping of feature names to importance scores"
    )
    model_metrics: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Overall model metrics (e.g., R2, RMSE)"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of prediction")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json()
