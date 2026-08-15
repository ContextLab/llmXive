"""
Schema definitions for architectural modification proposals.
"""
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Optional, List
import json

ModificationType = Literal['layer_add', 'head_count_change']

class ModificationProposal(BaseModel):
    """
    Pydantic model representing a proposed architectural modification.
    
    Attributes:
        modification_type: Type of modification ('layer_add' or 'head_count_change').
        magnitude: Integer magnitude of the change (e.g., number of layers to add).
        rationale: Human-readable explanation for the proposal.
        estimated_param_count: Estimated number of parameters added/changed.
    """
    modification_type: ModificationType = Field(
        ...,
        description="Type of modification: 'layer_add' or 'head_count_change'"
    )
    magnitude: int = Field(
        ...,
        gt=0,
        description="Magnitude of the change (must be positive integer)"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Rationale for the proposed modification"
    )
    estimated_param_count: int = Field(
        ...,
        ge=0,
        description="Estimated parameter count change"
    )

    @field_validator('modification_type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['layer_add', 'head_count_change']:
            raise ValueError(f"modification_type must be 'layer_add' or 'head_count_change', got '{v}'")
        return v

    @field_validator('magnitude')
    @classmethod
    def validate_magnitude(cls, v):
        if v <= 0:
            raise ValueError(f"magnitude must be a positive integer, got {v}")
        return v

    @field_validator('estimated_param_count')
    @classmethod
    def validate_param_count(cls, v):
        if v < 0:
            raise ValueError(f"estimated_param_count must be non-negative, got {v}")
        return v

def validate_modification_json(json_str: str) -> ModificationProposal:
    """
    Validate a JSON string against the ModificationProposal schema.
    
    Args:
        json_str: JSON string to validate.
        
    Returns:
        Validated ModificationProposal instance.
        
    Raises:
        ValidationError: If the JSON is invalid or missing required fields.
        json.JSONDecodeError: If the string is not valid JSON.
    """
    try:
        data = json.loads(json_str)
        return ModificationProposal(**data)
    except json.JSONDecodeError:
        raise
    except ValidationError:
        raise
