"""
Pydantic model for Model Output results.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime

class ModelOutput(BaseModel):
    """
    Container for model training results and predictions.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"
    )

    run_id: str = Field(..., description="Unique identifier for this model run")
    model_type: str = Field(..., description="Type of model (e.g., 'RandomForest', 'PGLS')")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of execution")
    
    # Performance Metrics
    r_squared: Optional[float] = Field(None, description="Coefficient of determination (R²)")
    adjusted_r_squared: Optional[float] = Field(None, description="Adjusted R²")
    mean_squared_error: Optional[float] = Field(None, description="Mean Squared Error")
    root_mean_squared_error: Optional[float] = Field(None, description="Root Mean Squared Error")
    mean_absolute_error: Optional[float] = Field(None, description="Mean Absolute Error")
    pearson_correlation: Optional[float] = Field(None, description="Pearson correlation coefficient")
    
    # Data Context
    n_samples: int = Field(..., ge=1, description="Number of samples used in training/evaluation")
    n_features: int = Field(..., ge=1, description="Number of features used")
    train_split_ratio: Optional[float] = Field(None, description="Ratio of training data (0.0-1.0)")
    
    # Feature Importance (if applicable)
    feature_importance: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Mapping of feature names to importance scores"
    )
    
    # Hyperparameters
    hyperparameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Dictionary of model hyperparameters"
    )
    
    # Phylogenetic Context (if applicable)
    phylogenetic_correction: Optional[bool] = Field(None, description="Whether phylogenetic correction was applied")
    lambda_param: Optional[float] = Field(None, description="Pagel's lambda if phylogenetic model")
    
    # Raw artifacts paths
    model_artifact_path: Optional[str] = Field(None, description="Path to saved model object")
    metrics_path: Optional[str] = Field(None, description="Path to metrics JSON file")
    
    # Metadata
    notes: Optional[str] = Field(None, description="Free-text notes about the run")
