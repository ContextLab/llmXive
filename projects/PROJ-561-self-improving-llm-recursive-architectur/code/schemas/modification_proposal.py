"""
Schema definitions for architectural modification proposals.

This module defines the Pydantic model for modification proposals,
ensuring strict validation of the JSON structure required for the
recursive self-improvement loop.
"""
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Optional, List
import json


class ModificationProposal(BaseModel):
    """
    Represents a proposed architectural modification to the model.
    
    Attributes:
        modification_type: The type of modification ('layer_add' or 'head_count_change').
        magnitude: The integer magnitude of the change (e.g., number of layers to add).
        rationale: A string explaining the reasoning behind the proposal.
        estimated_param_count: The estimated total parameter count after modification.
    """
    modification_type: Literal['layer_add', 'head_count_change'] = Field(
        ...,
        description="Type of architectural modification"
    )
    magnitude: int = Field(
        ...,
        gt=0,
        description="Magnitude of the change (must be positive)"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Reasoning for the proposed change"
    )
    estimated_param_count: int = Field(
        ...,
        gt=0,
        description="Estimated parameter count after modification"
    )

    @field_validator('rationale')
    @classmethod
    def rationale_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rationale cannot be empty or whitespace only")
        return v


def validate_modification_json(json_str: str) -> ModificationProposal:
    """
    Validates a JSON string against the ModificationProposal schema.
    
    Args:
        json_str: A JSON string representing the proposal.
        
    Returns:
        A validated ModificationProposal instance.
        
    Raises:
        ValidationError: If the JSON is invalid or does not match the schema.
        json.JSONDecodeError: If the input string is not valid JSON.
    """
    data = json.loads(json_str)
    return ModificationProposal(**data)
