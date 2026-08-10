"""
Feature Definition Module for Addressing von Neumann's Feature Definition Requirement.

This module defines atomic vs hierarchical feature units and maps them to specific
attention head groups. It provides the schema for mapping head_index to feature_group_id
and logic to tag attention heads with feature types.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Default feature definition schema mapping head indices to feature groups
# This represents the "atomic" feature units (individual heads) and their
# hierarchical grouping (feature groups)
DEFAULT_FEATURE_SCHEMA: Dict[str, str] = {
    "head_0": "group_A",  # e.g., Color features
    "head_1": "group_A",  # e.g., Color features (redundant/parallel)
    "head_2": "group_B",  # e.g., Motion features
    "head_3": "group_B",  # e.g., Motion features (redundant/parallel)
    "head_4": "group_C",  # e.g., Shape features
    "head_5": "group_C",  # e.g., Shape features (redundant/parallel)
    "head_6": "group_D",  # e.g., Depth features
    "head_7": "group_D",  # e.g., Depth features (redundant/parallel)
}

# Hierarchical feature group definitions
# Defines what each group represents in terms of semantic feature types
FEATURE_GROUP_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "group_A": {
        "name": "color",
        "description": "Features related to color perception",
        "atomic_units": ["head_0", "head_1"],
        "hierarchical_level": 1
    },
    "group_B": {
        "name": "motion",
        "description": "Features related to motion perception",
        "atomic_units": ["head_2", "head_3"],
        "hierarchical_level": 1
    },
    "group_C": {
        "name": "shape",
        "description": "Features related to shape perception",
        "atomic_units": ["head_4", "head_5"],
        "hierarchical_level": 1
    },
    "group_D": {
        "name": "depth",
        "description": "Features related to depth perception",
        "atomic_units": ["head_6", "head_7"],
        "hierarchical_level": 1
    }
}

def load_feature_schema(schema_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Load feature definition schema from a JSON file or return the default.

    Args:
        schema_path: Path to the feature definition schema JSON file.
                    If None, returns the default schema.

    Returns:
        Dictionary mapping head_index to feature_group_id
    """
    if schema_path is None:
        return DEFAULT_FEATURE_SCHEMA.copy()

    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Feature schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_feature_schema(schema: Dict[str, str], schema_path: Union[str, Path]) -> None:
    """
    Save feature definition schema to a JSON file.

    Args:
        schema: Dictionary mapping head_index to feature_group_id
        schema_path: Path where the schema will be saved
    """
    schema_path = Path(schema_path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)

def get_feature_group_for_head(head_index: Union[int, str], schema: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get the feature group ID for a specific attention head.

    Args:
        head_index: The attention head index (int or string like "head_0")
        schema: Feature definition schema. If None, uses default.

    Returns:
        Feature group ID if found, None otherwise
    """
    if schema is None:
        schema = DEFAULT_FEATURE_SCHEMA

    # Convert int to string format if needed
    if isinstance(head_index, int):
        head_key = f"head_{head_index}"
    else:
        head_key = str(head_index)

    return schema.get(head_key)

def get_atomic_units_for_group(group_id: str, schema: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Get all atomic units (head indices) that belong to a feature group.

    Args:
        group_id: The feature group ID
        schema: Feature definition schema. If None, uses default.

    Returns:
        List of head indices (as strings) belonging to this group
    """
    if schema is None:
        schema = DEFAULT_FEATURE_SCHEMA

    return [head for head, group in schema.items() if group == group_id]

def get_all_feature_groups(schema: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Get all unique feature group IDs in the schema.

    Args:
        schema: Feature definition schema. If None, uses default.

    Returns:
        List of unique feature group IDs
    """
    if schema is None:
        schema = DEFAULT_FEATURE_SCHEMA

    return list(set(schema.values()))

def tag_attention_heads_with_features(
    attention_weights: Dict[str, Any],
    schema: Optional[Dict[str, str]] = None,
    layer_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tag attention head weights with their feature group assignments.

    This function takes attention weights and enriches them with feature
    group information based on the schema.

    Args:
        attention_weights: Dictionary containing attention weights, expected
                          to have structure like:
                          {
                              "layer_{layer_id}": {
                                  "head_{head_id}": <weights_array>
                              }
                          }
        schema: Feature definition schema. If None, uses default.
        layer_id: Optional layer ID to filter specific layer

    Returns:
        Dictionary with the same structure but enriched with feature group info
    """
    if schema is None:
        schema = DEFAULT_FEATURE_SCHEMA

    tagged_weights = {}

    for layer_key, heads in attention_weights.items():
        # Filter by layer_id if specified
        if layer_id is not None and f"layer_{layer_id}" not in layer_key:
            continue

        tagged_heads = {}
        for head_key, weights in heads.items():
            feature_group = get_feature_group_for_head(head_key, schema)
            tagged_heads[head_key] = {
                "weights": weights,
                "feature_group": feature_group,
                "is_bound": feature_group is not None
            }

        tagged_weights[layer_key] = tagged_heads

    return tagged_weights

def create_feature_definition_schema(
    num_heads: int,
    num_groups: int = 4,
    heads_per_group: Optional[int] = None
) -> Dict[str, str]:
    """
    Create a feature definition schema with evenly distributed groups.

    Args:
        num_heads: Total number of attention heads
        num_groups: Number of feature groups to create
        heads_per_group: Optional override for heads per group

    Returns:
        Dictionary mapping head_index to feature_group_id
    """
    schema = {}

    if heads_per_group is None:
        heads_per_group = num_heads // num_groups

    for head_idx in range(num_heads):
        group_idx = (head_idx // heads_per_group) % num_groups
        head_key = f"head_{head_idx}"
        group_key = f"group_{chr(65 + group_idx)}"  # A, B, C, D...
        schema[head_key] = group_key

    return schema

def main():
    """
    Main function to generate and save the feature definition schema.
    """
    # Define output path
    output_dir = Path("data/final")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "feature_definition_schema.json"

    # Use default schema (can be customized based on model architecture)
    # For a standard DistilBERT with 12 heads, we might adjust the schema
    # Here we use a generic schema that can be adapted
    schema = DEFAULT_FEATURE_SCHEMA.copy()

    # If we need to adapt to a specific number of heads, we can create a new schema
    # For example, if the model has 12 heads:
    # schema = create_feature_definition_schema(num_heads=12, num_groups=4)

    # Save the schema
    save_feature_schema(schema, output_path)

    print(f"Feature definition schema saved to: {output_path}")
    print(f"Schema contains {len(schema)} head-to-group mappings")
    print(f"Feature groups: {set(schema.values())}")

    # Also print group definitions for reference
    print("\nFeature Group Definitions:")
    for group_id, definition in FEATURE_GROUP_DEFINITIONS.items():
        print(f"  {group_id}: {definition['name']} - {definition['description']}")

    return schema

if __name__ == "__main__":
    main()
