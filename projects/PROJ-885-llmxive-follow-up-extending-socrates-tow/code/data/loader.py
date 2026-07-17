"""
Data validation utilities for enforcing schema compliance on generated trajectories.

This module provides validation logic to ensure that generated conflict trajectories
strictly adhere to the defined schema before they are written to disk or used in experiments.

It validates:
- Required fields presence
- Field types and enum values
- Structural integrity of nested objects
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import is_dataclass, asdict
from enum import Enum

# Import existing entities from the project API surface
from models.entities import (
    ConflictTrajectory,
    SocioCognitiveState,
    EmotionalReactivityLevel,
    CulturalIdentityDiversity,
    SocioCognitiveStateType
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


def _validate_enum_field(value: Any, expected_type: type, field_name: str) -> None:
    """
    Validates that a field value is an instance of the expected Enum type.
    
    Args:
        value: The value to validate.
        expected_type: The expected Enum class.
        field_name: The name of the field for error reporting.
        
    Raises:
        ValidationError: If the value is not a valid member of the expected Enum.
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__} ({value!r})"
        )


def _validate_required_field(value: Any, field_name: str) -> None:
    """
    Validates that a required field is not None or empty.
    
    Args:
        value: The value to validate.
        field_name: The name of the field for error reporting.
        
    Raises:
        ValidationError: If the value is None or empty.
    """
    if value is None:
        raise ValidationError(f"Required field '{field_name}' is missing or None")
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"Required field '{field_name}' cannot be empty")


def validate_socio_cognitive_state(state: SocioCognitiveState) -> None:
    """
    Validates a SocioCognitiveState object against its schema.
    
    Args:
        state: The state object to validate.
        
    Raises:
        ValidationError: If the state fails any validation checks.
    """
    if not isinstance(state, SocioCognitiveState):
        raise ValidationError(f"Expected SocioCognitiveState, got {type(state).__name__}")
    
    # Validate state_type enum
    _validate_enum_field(state.state_type, SocioCognitiveStateType, "state_type")
    
    # Validate confidence score range
    if not (0.0 <= state.confidence <= 1.0):
        raise ValidationError(
            f"Field 'confidence' must be between 0.0 and 1.0, got {state.confidence}"
        )
    
    # Validate instructions list
    if not isinstance(state.instructions, list):
        raise ValidationError(f"Field 'instructions' must be a list, got {type(state.instructions).__name__}")


def validate_conflict_trajectory(trajectory: ConflictTrajectory) -> None:
    """
    Validates a ConflictTrajectory object against its schema.
    
    This function enforces strict schema compliance for generated trajectories,
    checking all required fields, types, and enum values.
    
    Args:
        trajectory: The trajectory object to validate.
        
    Raises:
        ValidationError: If the trajectory fails any validation checks.
    """
    if not isinstance(trajectory, ConflictTrajectory):
        raise ValidationError(f"Expected ConflictTrajectory, got {type(trajectory).__name__}")
    
    # Validate ID (should be a string or UUID-like)
    _validate_required_field(trajectory.trajectory_id, "trajectory_id")
    
    # Validate metadata fields
    _validate_required_field(trajectory.metadata, "metadata")
    
    if not isinstance(trajectory.metadata, dict):
        raise ValidationError(f"Field 'metadata' must be a dict, got {type(trajectory.metadata).__name__}")
    
    # Validate specific metadata fields if present
    if "emotional_reactivity" in trajectory.metadata:
        _validate_enum_field(
            trajectory.metadata["emotional_reactivity"], 
            EmotionalReactivityLevel, 
            "metadata.emotional_reactivity"
        )
    
    if "cultural_identity" in trajectory.metadata:
        _validate_enum_field(
            trajectory.metadata["cultural_identity"], 
            CulturalIdentityDiversity, 
            "metadata.cultural_identity"
        )
    
    # Validate turns list
    if not isinstance(trajectory.turns, list):
        raise ValidationError(f"Field 'turns' must be a list, got {type(trajectory.turns).__name__}")
    
    if len(trajectory.turns) == 0:
        raise ValidationError("Field 'turns' cannot be an empty list")
    
    # Validate each turn
    for idx, turn in enumerate(trajectory.turns):
        if not isinstance(turn, dict):
            raise ValidationError(
                f"Turn at index {idx} must be a dict, got {type(turn).__name__}"
            )
        
        # Check required turn fields
        required_turn_fields = {"turn_id", "speaker", "text", "timestamp"}
        missing_fields = required_turn_fields - set(turn.keys())
        if missing_fields:
            raise ValidationError(
                f"Turn at index {idx} missing required fields: {missing_fields}"
            )
        
        # Validate turn_id format (should be non-empty string)
        _validate_required_field(turn["turn_id"], f"turn[{idx}].turn_id")
        
        # Validate speaker
        _validate_required_field(turn["speaker"], f"turn[{idx}].speaker")
        
        # Validate text content
        _validate_required_field(turn["text"], f"turn[{idx}].text")


def validate_trajectory_batch(trajectories: List[ConflictTrajectory]) -> Tuple[int, List[str]]:
    """
    Validates a batch of trajectories and returns summary statistics.
    
    Args:
        trajectories: List of trajectory objects to validate.
        
    Returns:
        A tuple containing:
            - count of valid trajectories
            - list of error messages for invalid trajectories
            
    Raises:
        ValidationError: If the input is not a list.
    """
    if not isinstance(trajectories, list):
        raise ValidationError(f"Expected list of trajectories, got {type(trajectories).__name__}")
    
    valid_count = 0
    errors = []
    
    for idx, trajectory in enumerate(trajectories):
        try:
            validate_conflict_trajectory(trajectory)
            valid_count += 1
        except ValidationError as e:
            errors.append(f"Trajectory {idx}: {str(e)}")
            logger.warning(f"Validation failed for trajectory {idx}: {e}")
    
    if errors:
        logger.error(f"Validation failed for {len(errors)} out of {len(trajectories)} trajectories")
    
    return valid_count, errors


def validate_dict_schema(data: Dict[str, Any], schema: Dict[str, type]) -> None:
    """
    Validates a dictionary against a simple type schema.
    
    Args:
        data: The dictionary to validate.
        schema: A mapping of field names to expected types.
        
    Raises:
        ValidationError: If the data does not match the schema.
    """
    for field_name, expected_type in schema.items():
        if field_name not in data:
            raise ValidationError(f"Missing required field: {field_name}")
        
        value = data[field_name]
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )


def main() -> None:
    """
    Entry point for standalone validation testing.
    
    This function creates sample trajectory data and validates it to demonstrate
    the validation utilities.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a sample valid trajectory for testing
    sample_trajectory = ConflictTrajectory(
        trajectory_id="test-001",
        metadata={
            "emotional_reactivity": EmotionalReactivityLevel.HIGH,
            "cultural_identity": CulturalIdentityDiversity.DIVERSE,
            "source": "synthetic"
        },
        turns=[
            {
                "turn_id": "t1",
                "speaker": "participant_A",
                "text": "I feel strongly about this issue.",
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "turn_id": "t2",
                "speaker": "participant_B",
                "text": "I understand your perspective.",
                "timestamp": "2024-01-01T10:01:00Z"
            }
        ],
        socio_cognitive_states=[
            SocioCognitiveState(
                state_type=SocioCognitiveStateType.DEESCALATION,
                confidence=0.85,
                instructions=["de-escalate", "validate"]
            )
        ]
    )
    
    try:
        validate_conflict_trajectory(sample_trajectory)
        logger.info("Sample trajectory validation passed successfully.")
    except ValidationError as e:
        logger.error(f"Sample trajectory validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
