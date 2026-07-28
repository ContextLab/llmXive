"""
Schema definition for architectural modification proposals.

This module defines the Pydantic model `ModificationProposal` which serves as
the strict JSON schema for architectural changes proposed by the self-improving LLM.
It enforces type safety and validates inputs before they are processed by the
model modification logic.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
import json


class ModificationProposal(BaseModel):
    """
    Represents a structured proposal for modifying the LLM's architecture.

    Attributes:
        modification_type: The type of architectural change. Allowed values:
            - 'layer_add': Add N new transformer layers.
            - 'head_count_change': Modify the number of attention heads.
            - 'dim_change': Modify the hidden dimension (D_model).
        magnitude: The integer magnitude of the change (e.g., number of layers to add).
            Positive values indicate addition/increase. Negative values indicate removal/decrease.
        rationale: A string explaining the reasoning behind the proposed modification.
        estimated_param_count: The estimated change in parameter count (in millions) resulting from this modification.
    """
    modification_type: Literal["layer_add", "head_count_change", "dim_change"] = Field(
        ...,
        description="The type of architectural modification."
    )
    magnitude: int = Field(
        ...,
        ge=-100,
        le=100,
        description="The magnitude of the change (e.g., +2 layers, -4 heads)."
    )
    rationale: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="A detailed explanation of why this modification is proposed."
    )
    estimated_param_count: float = Field(
        ...,
        ge=0.0,
        description="Estimated parameter count increase in millions."
    )

    @field_validator('rationale')
    @classmethod
    def validate_rationale_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Rationale must be at least 10 characters long.")
        if len(v) > 500:
            raise ValueError("Rationale must not exceed 500 characters.")
        return v

    @classmethod
    def from_json_string(cls, json_str: str) -> 'ModificationProposal':
        """
        Parses a JSON string into a ModificationProposal instance.

        This method is used to validate raw JSON output from the LLM.
        It will raise a pydantic.ValidationError if the JSON is invalid
        or does not match the schema.

        Args:
            json_str: A JSON string representing the proposal.

        Returns:
            A validated ModificationProposal instance.

        Raises:
            ValueError: If the JSON is malformed.
            pydantic.ValidationError: If the JSON structure is valid but does not match the schema.
        """
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e


def validate_modification_json(json_str: str) -> bool:
    """
    Validates that a JSON string conforms to the ModificationProposal schema.

    Args:
        json_str: The JSON string to validate.

    Returns:
        True if the JSON is valid and conforms to the schema.

    Raises:
        ValueError: If the JSON is invalid or does not conform to the schema.
    """
    try:
        ModificationProposal.from_json_string(json_str)
        return True
    except (ValueError, Exception) as e:
        # Re-raise with a clear message for the caller
        raise ValueError(f"ModificationProposal validation failed: {e}") from e
