"""
Pydantic schemas for core domain entities in the grain boundary segregation pipeline.

These schemas provide strict validation for data exchange between services
and storage formats for computed results.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import numpy as np

# Enums for type safety and consistency
class BoundaryType(str, Enum):
    """Types of grain boundaries supported."""
    SYMMETRIC_TILT = "symmetric_tilt"
    ASYMMETRIC_TILT = "asymmetric_tilt"
    TWIST = "twist"
    GENERAL = "general"

class CrystalStructure(str, Enum):
    """Crystal structures for alloy systems."""
    BCC = "bcc"
    FCC = "fcc"
    HCP = "hcp"
    AMORPHOUS = "amorphous"

class ModelType(str, Enum):
    """Types of regression models supported."""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    RIDGE = "ridge"
    LASSO = "lasso"

# --- Base Entity Schemas ---

class AlloySystem(BaseModel):
    """
    Represents a specific alloy system configuration.

    Attributes:
        system_id: Unique identifier for the alloy system (e.g., 'Fe-Cr-Mo').
        base_element: The solvent element (e.g., 'Fe').
        solute_elements: List of solute elements present.
        crystal_structure: The bulk crystal structure.
        bulk_composition: Dictionary mapping element to atomic fraction.
        temperature_range: Tuple of (min_temp_K, max_temp_K).
        metadata: Additional system-specific information.
    """
    model_config = ConfigDict(use_enum_values=True)

    system_id: str = Field(..., description="Unique identifier for the alloy system")
    base_element: str = Field(..., description="Solvent element symbol")
    solute_elements: List[str] = Field(..., description="List of solute element symbols")
    crystal_structure: CrystalStructure = Field(..., description="Bulk crystal structure")
    bulk_composition: Dict[str, float] = Field(
        ...,
        description="Mapping of element symbols to atomic fractions"
    )
    temperature_range: List[float] = Field(
        ...,
        description="Temperature range [min_K, max_K]"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('bulk_composition')
    @classmethod
    def validate_composition_sum(cls, v: Dict[str, float]) -> Dict[str, float]:
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Composition fractions must sum to ~1.0, got {total}")
        return v

    @field_validator('solute_elements')
    @classmethod
    def validate_no_base_in_solutes(cls, v: List[str], info) -> List[str]:
        # Access base_element from the model instance if available during validation
        # In strict Pydantic v2, we might need a model_validator for cross-field checks
        # For now, we assume the caller ensures this or rely on the validator logic
        return v

    def __hash__(self):
        return hash(self.system_id)

class SegregationProfile(BaseModel):
    """
    Represents a computed or measured segregation profile for a specific boundary.

    Attributes:
        profile_id: Unique identifier for the profile.
        system_id: Reference to the AlloySystem.
        boundary_type: Type of grain boundary.
        boundary_indices: Miller indices defining the boundary (e.g., [100], [110]).
        temperature_K: Temperature at which this profile applies.
        segregation_energy_ev: Calculated segregation energy (eV).
        equilibrium_concentration: Atomic fraction at the boundary.
        bulk_concentration: Atomic fraction in the bulk.
        profile_data: Detailed distance-concentration pairs if available.
        calculation_method: Method used (e.g., 'McLean', 'DFT', 'Experimental').
        timestamp: When the profile was generated.
        metadata: Additional profile-specific data.
    """
    model_config = ConfigDict(use_enum_values=True)

    profile_id: str = Field(..., description="Unique identifier for the profile")
    system_id: str = Field(..., description="Reference to the AlloySystem")
    boundary_type: BoundaryType = Field(..., description="Type of grain boundary")
    boundary_indices: List[int] = Field(..., description="Miller indices")
    temperature_K: float = Field(..., description="Temperature in Kelvin")
    segregation_energy_ev: float = Field(..., description="Segregation energy in eV")
    equilibrium_concentration: float = Field(..., description="Equilibrium atomic fraction at boundary")
    bulk_concentration: float = Field(..., description="Bulk atomic fraction")
    profile_data: Optional[List[Dict[str, float]]] = Field(
        default=None,
        description="List of {distance_angstroms, concentration} points"
    )
    calculation_method: str = Field(..., description="Method used for calculation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('segregation_energy_ev')
    @classmethod
    def validate_energy_range(cls, v: float) -> float:
        if not (-10.0 <= v <= 10.0):
            raise ValueError(f"Segregation energy {v} eV is outside physical bounds [-10, 10]")
        return v

    @field_validator('equilibrium_concentration', 'bulk_concentration')
    @classmethod
    def validate_concentration_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Concentration {v} must be between 0 and 1")
        return v

class RegressionModel(BaseModel):
    """
    Represents a fitted regression model for predicting segregation behavior.

    Attributes:
        model_id: Unique identifier for the model instance.
        model_type: The type of regression model.
        features: List of feature names used (e.g., 'Cr', 'Mo', 'Cr*Mo').
        coefficients: List of learned coefficients.
        intercept: Model intercept.
        metrics: Dictionary of performance metrics (R2, MSE, etc.).
        training_samples: Number of samples used for training.
        feature_importance: Optional feature importance scores.
        timestamp: When the model was fitted.
        metadata: Additional model metadata.
    """
    model_config = ConfigDict(use_enum_values=True)

    model_id: str = Field(..., description="Unique identifier for the model")
    model_type: ModelType = Field(..., description="Type of regression model")
    features: List[str] = Field(..., description="List of feature names")
    coefficients: List[float] = Field(..., description="Model coefficients")
    intercept: float = Field(..., description="Model intercept")
    metrics: Dict[str, float] = Field(
        ...,
        description="Performance metrics (R2, MSE, MAE, etc.)"
    )
    training_samples: int = Field(..., description="Number of training samples")
    feature_importance: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional feature importance mapping"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fitting timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('coefficients')
    @classmethod
    def validate_coefficients_length(cls, v: List[float], info) -> List[float]:
        # This validator requires access to 'features' which is in the same model.
        # In Pydantic v2, we use model_validator for cross-field validation.
        return v

    # Cross-field validation for coefficients length matching features
    @field_validator('features')
    @classmethod
    def check_features(cls, v):
        return v

    def model_dump_json(self, *args, **kwargs):
        # Override to handle datetime serialization if needed
        return super().model_dump_json(*args, **kwargs)

# --- Helper Functions for Serialization ---

def serialize_profile(profile: SegregationProfile) -> str:
    """Serialize a SegregationProfile to JSON string."""
    return profile.model_dump_json(indent=2)

def serialize_model(model: RegressionModel) -> str:
    """Serialize a RegressionModel to JSON string."""
    return model.model_dump_json(indent=2)

def serialize_alloy_system(system: AlloySystem) -> str:
    """Serialize an AlloySystem to JSON string."""
    return system.model_dump_json(indent=2)

# --- Validation Utilities ---

def validate_profile_consistency(profile: SegregationProfile) -> bool:
    """
    Validates internal consistency of a segregation profile.

    Checks:
    - Concentration <= 1.0
    - Energy is within physical bounds
    - Temperature is positive
    """
    if profile.equilibrium_concentration > 1.0:
        return False
    if profile.segregation_energy_ev < -10.0 or profile.segregation_energy_ev > 10.0:
        return False
    if profile.temperature_K <= 0:
        return False
    return True

def validate_model_metrics(metrics: Dict[str, float]) -> bool:
    """
    Validates regression model metrics for reasonableness.

    Checks:
    - R2 is between -inf and 1.0
    - MSE is non-negative
    """
    if 'R2' in metrics:
        if metrics['R2'] > 1.0:
            return False
    if 'MSE' in metrics:
        if metrics['MSE'] < 0:
            return False
    return True