from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Literal, Optional, List
import json


class ModificationProposal(BaseModel):
    """
    Pydantic model representing a proposed architectural modification to the LLM.
    
    Fields:
        modification_type: The type of change ('layer_add' or 'head_count_change').
        magnitude: The integer magnitude of the change (e.g., number of layers to add, 
                   or change in number of attention heads).
        rationale: A string explaining the reasoning behind the proposal.
        estimated_param_count: The estimated number of parameters added/removed by this change.
    """
    modification_type: Literal['layer_add', 'head_count_change'] = Field(
        ..., 
        description="Type of architectural modification"
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
        description="Estimated parameter count change"
    )

    @field_validator('rationale')
    @classmethod
    def validate_rationale(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rationale cannot be empty or whitespace only")
        return v.strip()


def validate_modification_json(json_str: str) -> ModificationProposal:
    """
    Validates a JSON string against the ModificationProposal schema.
    
    Args:
        json_str: A JSON string representing the proposal.
        
    Returns:
        A validated ModificationProposal instance.
        
    Raises:
        ValidationError: If the JSON is invalid or does not match the schema.
        json.JSONDecodeError: If the input is not valid JSON.
    """
    try:
        data = json.loads(json_str)
        return ModificationProposal(**data)
    except json.JSONDecodeError:
        raise
    except ValidationError:
        raise
