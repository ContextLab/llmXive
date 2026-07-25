"""
Pydantic models for Model Output and Results.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModelOutput(BaseModel):
    """
    Container for model training results and predictions.
    """
    model_config = ConfigDict(from_attributes=True)

    run_id: str = Field(..., description="Unique identifier for this model run")
    model_type: str = Field(..., description="Type of model (e.g., PGLS, Random Forest)")
    species_ids: List[str] = Field(..., description="List of species included in the training set")
    target_metabolite: str = Field(..., description="Target metabolite or class being predicted")
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Metrics like R2, RMSE, MAE"
    )
    feature_importance: Optional[Dict[str, float]] = Field(
        None,
        description="Mapping of BGC types to importance scores"
    )
    coefficients: Optional[Dict[str, float]] = Field(
        None,
        description="Model coefficients if applicable (e.g., for linear models)"
    )
    phylogenetic_correction_applied: bool = Field(
        False,
        description="Whether phylogenetic correction was used"
    )
    cv_folds: Optional[int] = Field(None, description="Number of CV folds if used")
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Final hyperparameters used"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    artifact_path: Optional[str] = Field(None, description="Path to saved model artifact")
    summary: Optional[str] = Field(None, description="Human-readable summary of results")
