"""
Base data schemas and validation helpers for the molecular reactivity pipeline.

Defines Pydantic models for:
- ReactionRecord: Raw/processed reaction data
- FeatureVector: Extracted molecular features
- ModelResult: Prediction outputs and metadata
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
import re

# Regex for basic SMILES validation (not exhaustive, but catches obvious errors)
SMILES_PATTERN = r'^[A-Za-z0-9@%$\[\]().=+#\\/-]+$'


class ReactionRecord(BaseModel):
    """Schema for a single reaction record."""
    reaction_id: str = Field(..., description="Unique identifier for the reaction")
    smiles_reactants: str = Field(..., description="SMILES string of reactants")
    smiles_products: str = Field(..., description="SMILES string of products")
    reaction_type: Optional[str] = Field(None, description="Classified reaction type (SN1, SN2, Diels-Alder)")
    yield_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Experimental yield percentage")
    success_flag: Optional[bool] = Field(None, description="Binary success indicator if yield is missing")
    source_url: Optional[str] = Field(None, description="Source URL or dataset ID")
    raw_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Original raw data fields")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of processing")

    @field_validator('smiles_reactants', 'smiles_products')
    @classmethod
    def validate_smiles(cls, v: str) -> str:
        """Validate that the SMILES string contains only valid characters."""
        if not v or not re.match(SMILES_PATTERN, v):
            raise ValueError(f"Invalid SMILES format: {v}")
        return v

    @field_validator('reaction_type')
    @classmethod
    def validate_reaction_type(cls, v: Optional[str]) -> Optional[str]:
        """Ensure reaction type is one of the expected classes if present."""
        if v is not None:
            valid_types = {"SN1", "SN2", "Diels-Alder"}
            if v not in valid_types:
                raise ValueError(f"Invalid reaction type '{v}'. Must be one of {valid_types}")
        return v

    @model_validator(mode='after')
    def check_target_variable(self) -> 'ReactionRecord':
        """Ensure at least one target variable (yield or success) is present."""
        if self.yield_pct is None and self.success_flag is None:
            raise ValueError("Either 'yield_pct' or 'success_flag' must be provided.")
        return self


class FeatureVector(BaseModel):
    """Schema for a feature vector derived from a reaction."""
    reaction_id: str = Field(..., description="Reference to the source reaction")
    features: Dict[str, float] = Field(..., description="Dictionary of feature name to value")
    molecular_weight: Optional[float] = Field(None, ge=0.0, description="Calculated molecular weight")
    atom_count: Optional[int] = Field(None, ge=0, description="Total number of atoms")
    bond_count: Optional[int] = Field(None, ge=0, description="Total number of bonds")
    topological_indices: Optional[Dict[str, float]] = Field(default_factory=dict, description="Topological indices (e.g., Wiener index)")
    extracted_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of feature extraction")

    @field_validator('features')
    @classmethod
    def validate_features_dict(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure all feature values are numeric."""
        for k, val in v.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"Feature '{k}' must be numeric, got {type(val)}")
        return v


class ModelResult(BaseModel):
    """Schema for a model prediction result."""
    reaction_id: str = Field(..., description="Reference to the source reaction")
    predicted_value: float = Field(..., description="Model prediction (e.g., yield probability)")
    actual_value: Optional[float] = Field(None, description="Actual observed value for evaluation")
    prediction_class: Optional[str] = Field(None, description="Discrete class prediction if applicable")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model confidence in prediction")
    model_version: str = Field(..., description="Version identifier of the trained model")
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of prediction")

    @field_validator('confidence_score')
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Ensure confidence is between 0 and 1."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError(f"Confidence score must be between 0 and 1, got {v}")
        return v


def validate_reaction_batch(records: List[Dict[str, Any]]) -> List[ReactionRecord]:
    """
    Validate a batch of raw dictionaries into ReactionRecord objects.
    
    Args:
        records: List of dictionaries representing raw reaction data.
        
    Returns:
        List of validated ReactionRecord objects.
        
    Raises:
        ValueError: If any record fails validation.
    """
    validated = []
    errors = []
    for i, rec in enumerate(records):
        try:
            validated.append(ReactionRecord(**rec))
        except Exception as e:
            errors.append(f"Record {i} failed validation: {e}")
    
    if errors:
        raise ValueError(f"Batch validation failed with {len(errors)} errors:\n" + "\n".join(errors))
    
    return validated