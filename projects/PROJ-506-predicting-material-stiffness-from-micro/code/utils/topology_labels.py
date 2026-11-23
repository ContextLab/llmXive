"""
Topology Type Labels Utility Module

This module provides logic to assign `topology_type` labels ("random", "aligned", "percolating")
as INPUT parameters to the microstructure generator. These labels are NOT derived from the image
but are passed as arguments to ensure stratification keys are consistent with the generation process.

Purpose:
- Provide the stratification key required by FR-005.
- Ensure the generator accepts `topology_type` as an argument.
- Record the label in metadata for downstream validation and analysis.

Note:
This is distinct from T017b (topology_metrics.py), which calculates metrics like shape_factor
and connectivity FROM the image. This module handles the LABEL assignment based on generation
parameters.
"""

from typing import List, Literal, Dict, Any, Optional

# Valid topology types as defined in the project schema
TOPOLOGY_TYPES = ["random", "aligned", "percolating"]

def validate_topology_type(topology_type: str) -> bool:
    """
    Validate that a given topology type string is one of the allowed values.

    Args:
        topology_type: The topology type string to validate.

    Returns:
        True if valid, False otherwise.
    """
    return topology_type in TOPOLOGY_TYPES

def assign_topology_label(topology_type: str) -> str:
    """
    Assign and validate a topology type label.

    This function ensures the provided label is one of the valid types.
    It serves as the primary interface for the generator to set the label.

    Args:
        topology_type: The desired topology type ("random", "aligned", or "percolating").

    Returns:
        The validated topology type string.

    Raises:
        ValueError: If the provided topology_type is not in the allowed list.
    """
    if not validate_topology_type(topology_type):
        raise ValueError(
            f"Invalid topology_type '{topology_type}'. "
            f"Must be one of: {TOPOLOGY_TYPES}"
        )
    return topology_type

def get_topology_label_for_metadata(
    topology_type: str,
    seed: int,
    density: float
) -> Dict[str, Any]:
    """
    Construct a metadata dictionary entry for the topology label.

    This function is intended to be called by the data generation pipeline
    to record the specific topology type used for a given microstructure.

    Args:
        topology_type: The validated topology type string.
        seed: The random seed used for generation.
        density: The inclusion density used for generation.

    Returns:
        A dictionary containing the topology label and generation parameters.
    """
    # Ensure the label is valid before adding to metadata
    validated_label = assign_topology_label(topology_type)

    return {
        "topology_type": validated_label,
        "seed": seed,
        "inclusion_density": density,
        "is_stratification_key": True
    }

def get_valid_topology_types() -> List[str]:
    """
    Return the list of valid topology type labels.

    Returns:
        List of valid topology type strings.
    """
    return TOPOLOGY_TYPES.copy()
