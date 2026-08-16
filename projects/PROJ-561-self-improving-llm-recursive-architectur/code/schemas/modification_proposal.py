"""
Schema definitions for architectural modification proposals.
"""
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Optional, List
import json

ModificationType = Literal[
    'layer_add',
    'head_count_change',
    'hidden_size_change',
    'activation_change'
]

class ModificationProposal(BaseModel):
    """
    Pydantic model representing a proposed architectural modification to the LLM.
    
    Attributes:
        modification_type: The type of modification being proposed.
        magnitude: The integer magnitude of the change (e.g., number of layers to add).
        rationale: A string explaining the reasoning behind the proposal.
        estimated_param_count: The estimated total parameter count after modification.
    """
    modification_type: ModificationType = Field(
        ...,
        description="Type of modification: layer_add, head_count_change, hidden_size_change, or activation_change"
    )
    magnitude: int = Field(
        ...,
        gt=0,
        description="Magnitude of the change (must be a positive integer)"
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Rationale for the proposed modification"
    )
    estimated_param_count: int = Field(
        ...,
        gt=0,
        description="Estimated total parameter count after applying this modification"
    )

    @field_validator('modification_type')
    @classmethod
    def validate_modification_type(cls, v: str) -> ModificationType:
        if v not in ['layer_add', 'head_count_change', 'hidden_size_change', 'activation_change']:
            raise ValueError(f"Invalid modification_type: {v}. Must be one of 'layer_add', 'head_count_change', 'hidden_size_change', 'activation_change'.")
        return v

def validate_modification_json(json_string: str) -> ModificationProposal:
    """
    Validates a JSON string against the ModificationProposal schema.
    
    Args:
        json_string: A JSON string representing the proposal.
        
    Returns:
        A validated ModificationProposal instance.
        
    Raises:
        ValidationError: If the JSON is invalid or missing required fields.
        json.JSONDecodeError: If the input is not valid JSON.
    """
    data = json.loads(json_string)
    return ModificationProposal(**data)
