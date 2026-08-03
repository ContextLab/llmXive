"""
Contract for Scene Graphs and Scene Descriptions.

This module defines the expected structure (contract) for scene data
used throughout the llmXive pipeline. It aligns with
specs/001-llmxive-interleave-structure-vs-modality/contracts/scene.schema.yaml.
"""

from typing import List, Dict, Any, Optional


class SceneContract:
    """
    Contract defining the structure of a Scene Graph.
    
    Expected fields:
    - objects: List of object dictionaries (id, name, attributes, bounding_box)
    - relationships: List of relationship dictionaries (subject_id, predicate, object_id)
    - attributes: Global scene attributes (optional)
    - metadata: Source information (optional)
    """
    
    REQUIRED_KEYS = ["objects", "relationships"]
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> None:
        """
        Validate that the input data conforms to the Scene Contract.
        
        Args:
            data: The dictionary to validate.
            
        Raises:
            ValueError: If the data does not conform to the contract.
        """
        if not isinstance(data, dict):
            raise ValueError("Scene data must be a dictionary.")
        
        for key in SceneContract.REQUIRED_KEYS:
            if key not in data:
                raise ValueError(f"Missing required key in Scene Contract: '{key}'")
        
        if not isinstance(data["objects"], list):
            raise ValueError("'objects' must be a list.")
        
        if not isinstance(data["relationships"], list):
            raise ValueError("'relationships' must be a list.")
        
        # Validate object structure
        for i, obj in enumerate(data["objects"]):
            if not isinstance(obj, dict):
                raise ValueError(f"Object at index {i} must be a dictionary.")
            if "id" not in obj or "name" not in obj:
                raise ValueError(f"Object at index {i} must have 'id' and 'name'.")
        
        # Validate relationship structure
        for i, rel in enumerate(data["relationships"]):
            if not isinstance(rel, dict):
                raise ValueError(f"Relationship at index {i} must be a dictionary.")
            required_rel_keys = ["subject_id", "predicate", "object_id"]
            for key in required_rel_keys:
                if key not in rel:
                    raise ValueError(f"Relationship at index {i} missing key: '{key}'")
    
    @staticmethod
    def get_example() -> Dict[str, Any]:
        """Return an example conforming to the contract."""
        return {
            "objects": [
                {"id": 1, "name": "person", "attributes": {"clothing": "blue shirt"}},
                {"id": 2, "name": "ball", "attributes": {"color": "red"}}
            ],
            "relationships": [
                {"subject_id": 1, "predicate": "holding", "object_id": 2}
            ],
            "attributes": {"scene_type": "outdoor"},
            "metadata": {"source": "WISE"}
        }
