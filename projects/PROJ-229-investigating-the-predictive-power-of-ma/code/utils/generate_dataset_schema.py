"""
Utility to generate and validate the dataset schema dynamically based on target decision.
This module supports T007 (static schema creation) and T007a (runtime validation logic).
"""
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from code.utils.logger import get_pipeline_logger

logger = get_pipeline_logger(__name__)

def load_target_decision(decision_path: str = "data/results/target_decision.json") -> Dict[str, Any]:
    """
    Load the target decision file to determine the active target field.
    
    Args:
        decision_path: Path to the target_decision.json file.
        
    Returns:
        Dictionary containing the decision data.
        
    Raises:
        FileNotFoundError: If the decision file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(decision_path)
    if not path.exists():
        raise FileNotFoundError(f"Target decision file not found at {decision_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def generate_schema(target_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the dataset schema, dynamically setting the required target field.
    
    Args:
        target_decision: The loaded target decision dictionary.
        
    Returns:
        A complete JSON Schema dictionary for the dataset.
    """
    target_field = target_decision.get('target')
    if not target_field:
        raise ValueError("Target decision missing 'target' key.")
    
    rationale = target_decision.get('decision_rationale', 'No rationale provided.')
    
    # Define static properties
    properties = {
        "material_id": {
            "type": "string",
            "description": "Unique identifier from Materials Project (e.g., mp-1234)."
        },
        "composition": {
            "type": "string",
            "description": "Chemical composition string (e.g., 'Fe2O3')."
        },
        "elemental_count": {
            "type": "integer",
            "description": "Number of distinct elements in the composition."
        },
        "melting_point": {
            "type": ["number", "null"],
            "description": "Melting point in Kelvin. May be null if not available."
        },
        "latent_heat": {
            "type": ["number", "null"],
            "description": "Latent heat of fusion in J/g. May be null if not available."
        },
        "formation_energy": {
            "type": "number",
            "description": "Formation energy per atom in eV."
        },
        "density": {
            "type": "number",
            "description": "Density in g/cm^3."
        },
        "elemental_features": {
            "type": "object",
            "description": "Nested object containing elemental descriptors.",
            "additionalProperties": True
        },
        "graph_features": {
            "type": "array",
            "description": "Array of graph-based structural descriptors.",
            "items": {
                "type": "number"
            }
        }
    }
    
    # Construct required list: always include static fields + the dynamic target
    required_fields = [
        "material_id",
        "composition",
        "elemental_count",
        "formation_energy",
        "density",
        "elemental_features",
        "graph_features",
        target_field
    ]
    
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Phase-Change Material Dataset Schema",
        "description": f"Dynamic schema for PCM dataset. Target: {target_field}. Rationale: {rationale}",
        "type": "object",
        "required": required_fields,
        "properties": properties,
        "additionalProperties": False,
        "metadata": {
            "target_field": target_field,
            "decision_rationale": rationale,
            "generated_from": decision_path
        }
    }
    
    return schema

def save_schema(schema: Dict[str, Any], output_path: str = "contracts/dataset.schema.yaml") -> None:
    """
    Save the generated schema to a YAML file.
    
    Args:
        schema: The schema dictionary to save.
        output_path: Path to the output YAML file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Schema saved to {output_path}")

def validate_schema(schema: Dict[str, Any]) -> bool:
    """
    Perform basic structural validation of the schema.
    
    Args:
        schema: The schema dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(schema, dict):
        logger.error("Schema must be a dictionary.")
        return False
    
    required_keys = ["type", "required", "properties"]
    for key in required_keys:
        if key not in schema:
            logger.error(f"Schema missing required key: {key}")
            return False
    
    if schema["type"] != "object":
        logger.error("Schema type must be 'object'.")
        return False
    
    if not isinstance(schema["required"], list):
        logger.error("'required' must be a list of strings.")
        return False
    
    if not isinstance(schema["properties"], dict):
        logger.error("'properties' must be a dictionary.")
        return False
    
    logger.info("Schema validation passed.")
    return True

def main() -> None:
    """
    Main entry point to generate the dataset schema from the target decision.
    """
    try:
        decision_path = "data/results/target_decision.json"
        logger.info(f"Loading target decision from {decision_path}")
        decision = load_target_decision(decision_path)
        
        logger.info(f"Generating schema for target: {decision.get('target')}")
        schema = generate_schema(decision)
        
        logger.info("Validating generated schema")
        if not validate_schema(schema):
            raise RuntimeError("Generated schema failed validation.")
        
        output_path = "contracts/dataset.schema.yaml"
        logger.info(f"Saving schema to {output_path}")
        save_schema(schema, output_path)
        
        logger.info("Dataset schema generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in target decision: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating schema: {e}")
        raise

if __name__ == "__main__":
    main()
