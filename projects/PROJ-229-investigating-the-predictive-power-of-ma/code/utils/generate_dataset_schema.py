"""
Utility to generate the dataset schema dynamically based on the target decision.

This module reads `data/results/target_decision.json` to determine the target variable
and generates a valid YAML schema at `contracts/dataset.schema.yaml`.
"""
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from code.utils.logger import get_pipeline_logger

logger = get_pipeline_logger(__name__)

TARGET_DECISION_PATH = Path("data/results/target_decision.json")
SCHEMA_OUTPUT_PATH = Path("contracts/dataset.schema.yaml")

def load_target_decision() -> Dict[str, Any]:
    """
    Load the target decision from the JSON file.
    
    Returns:
        Dict containing the target decision data.
        
    Raises:
        FileNotFoundError: If the target decision file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not TARGET_DECISION_PATH.exists():
        raise FileNotFoundError(
            f"Target decision file not found: {TARGET_DECISION_PATH}. "
            "Please run T006a first."
        )
    
    with open(TARGET_DECISION_PATH, "r") as f:
        return json.load(f)

def generate_schema(target_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the dataset schema based on the target decision.
    
    Args:
        target_decision: Dictionary containing the target decision data.
        
    Returns:
        Dictionary representing the complete schema.
    """
    target_var = target_decision.get("target", "melting_point")
    
    # Define common fields expected in the dataset
    common_fields = [
        {
            "name": "material_id",
            "type": "string",
            "description": "Unique identifier for the material (e.g., Materials Project ID)",
            "required": True
        },
        {
            "name": "composition",
            "type": "string",
            "description": "Chemical composition of the material",
            "required": True
        },
        {
            "name": "structure_type",
            "type": "string",
            "description": "Crystal structure type",
            "required": False
        },
        {
            "name": "melting_point",
            "type": "number",
            "description": "Melting point in Kelvin",
            "required": False
        },
        {
            "name": "latent_heat",
            "type": "number",
            "description": "Latent heat of fusion in kJ/kg",
            "required": False
        },
        {
            "name": "atomic_number_avg",
            "type": "number",
            "description": "Average atomic number of constituent elements",
            "required": False
        },
        {
            "name": "electronegativity_avg",
            "type": "number",
            "description": "Average electronegativity of constituent elements",
            "required": False
        },
        {
            "name": "atomic_radius_avg",
            "type": "number",
            "description": "Average atomic radius of constituent elements",
            "required": False
        }
    ]
    
    # Ensure the target variable is marked as required
    for field in common_fields:
        if field["name"] == target_var:
            field["required"] = True
            field["description"] = f"{target_var.replace('_', ' ').title()} (Target Variable)"
            break
    
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Phase-Change Materials Dataset Schema",
        "description": "Schema for the processed PCM dataset used in predictive modeling. Target field dynamically set based on target_decision.json.",
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Schema version"
                    },
                    "generated_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp of schema generation"
                    },
                    "target_variable": {
                        "type": "string",
                        "description": "The target variable selected by the consistency check",
                        "enum": ["melting_point", "latent_heat"]
                    },
                    "source": {
                        "type": "string",
                        "description": "Data source identifier"
                    }
                },
                "required": ["version", "target_variable", "source"]
            },
            "fields": {
                "type": "array",
                "description": "List of field definitions in the dataset",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["integer", "number", "string", "boolean"]
                        },
                        "description": {"type": "string"},
                        "required": {
                            "type": "boolean",
                            "default": False
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "examples": {
                "type": "array",
                "description": "Example records conforming to the schema",
                "items": {"type": "object"}
            }
        },
        "required": ["metadata", "fields"],
        "additionalProperties": False
    }
    
    # Populate metadata
    schema["properties"]["metadata"]["properties"]["target_variable"]["enum"] = [target_var]
    schema["properties"]["metadata"]["properties"]["target_variable"]["description"] = f"The target variable selected: {target_var}"
    
    # Populate fields
    schema["properties"]["fields"]["items"] = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["integer", "number", "string", "boolean"]},
            "description": {"type": "string"},
            "required": {"type": "boolean", "default": False}
        },
        "required": ["name", "type"]
    }
    
    return schema

def validate_schema(schema: Dict[str, Any]) -> bool:
    """
    Validate that the generated schema is non-empty and structurally valid.
    
    Args:
        schema: The schema dictionary to validate.
        
    Returns:
        True if valid, raises ValueError if invalid.
    """
    if not schema:
        raise ValueError("Generated schema is empty.")
    
    required_keys = ["$schema", "title", "description", "type", "properties", "required"]
    for key in required_keys:
        if key not in schema:
            raise ValueError(f"Schema missing required key: {key}")
    
    if "metadata" not in schema["properties"]:
        raise ValueError("Schema missing 'metadata' property.")
    
    if "fields" not in schema["properties"]:
        raise ValueError("Schema missing 'fields' property.")
    
    target_var = schema["properties"]["metadata"]["properties"]["target_variable"]
    if "enum" not in target_var or not target_var["enum"]:
        raise ValueError("Target variable must have a non-empty enum list.")
    
    logger.info("Schema validation passed.")
    return True

def save_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Save the schema to a YAML file.
    
    Args:
        schema: The schema dictionary to save.
        output_path: Path to the output YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Schema saved to {output_path}")

def main() -> None:
    """
    Main entry point to generate and save the dataset schema.
    """
    try:
        logger.info("Loading target decision...")
        target_decision = load_target_decision()
        
        logger.info(f"Target variable determined: {target_decision.get('target')}")
        
        logger.info("Generating schema...")
        schema = generate_schema(target_decision)
        
        logger.info("Validating schema...")
        validate_schema(schema)
        
        logger.info("Saving schema...")
        save_schema(schema, SCHEMA_OUTPUT_PATH)
        
        logger.info("Task T007 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in target decision file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during schema generation: {e}")
        raise

if __name__ == "__main__":
    main()