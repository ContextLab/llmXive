import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generates the dataset schema based on the project specifications.
    Includes required fields: participant_id, age, stimulus_type,
    perseverative_errors, categories_completed, and optional MMSE.
    """
    schema = {
        "type": "object",
        "properties": {
            "participant_id": {
                "type": "string",
                "description": "Unique identifier for the participant",
                "required": True
            },
            "age": {
                "type": "integer",
                "description": "Age of the participant in years",
                "minimum": 65,
                "required": True
            },
            "stimulus_type": {
                "type": "string",
                "description": "Type of stimulus presented (nostalgia or control)",
                "enum": ["nostalgia", "control"],
                "required": True
            },
            "perseverative_errors": {
                "type": "integer",
                "description": "Number of perseverative errors made in the task",
                "minimum": 0,
                "required": True
            },
            "categories_completed": {
                "type": "integer",
                "description": "Number of categories successfully completed",
                "minimum": 0,
                "required": True
            },
            "MMSE": {
                "type": ["integer", "null"],
                "description": "Mini-Mental State Examination score (optional)",
                "minimum": 0,
                "maximum": 30,
                "required": False
            }
        },
        "required_fields": ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"],
        "optional_fields": ["MMSE"]
    }
    return schema

def generate_output_schema() -> Dict[str, Any]:
    """
    Generates the output schema for analysis results.
    """
    schema = {
        "type": "object",
        "properties": {
            "statistical_test": {
                "type": "string",
                "description": "Name of the statistical test performed",
                "required": True
            },
            "p_value": {
                "type": "number",
                "description": "Raw p-value from the test",
                "required": True
            },
            "p_value_corrected": {
                "type": "number",
                "description": "Bonferroni-corrected p-value",
                "required": True
            },
            "effect_size": {
                "type": "number",
                "description": "Cohen's d effect size",
                "required": True
            },
            "effect_size_ci": {
                "type": "object",
                "description": "95% Confidence Interval for effect size",
                "properties": {
                    "lower": {"type": "number"},
                    "upper": {"type": "number"}
                },
                "required": True
            },
            "power": {
                "type": "number",
                "description": "Calculated statistical power",
                "required": True
            },
            "mdes": {
                "type": "number",
                "description": "Minimum Detectable Effect Size",
                "required": True
            },
            "sensitivity_flags": {
                "type": "object",
                "description": "Flags indicating sensitivity to threshold choices",
                "required": True
            }
        },
        "required_fields": [
            "statistical_test", "p_value", "p_value_corrected",
            "effect_size", "effect_size_ci", "power", "mdes", "sensitivity_flags"
        ]
    }
    return schema

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the schema dictionary to a YAML file.
    """
    with open(output_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    log_info(f"Schema written to {output_path}")

def main() -> None:
    """
    Main entry point for generating contract schemas.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    setup_logging()

    # Ensure contracts directory exists
    contracts_dir = Path("contracts")
    contracts_dir.mkdir(exist_ok=True)

    # Generate and write dataset schema
    dataset_schema = generate_dataset_schema()
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    write_schema(dataset_schema, dataset_schema_path)

    # Validate required fields exist in dataset schema
    required_fields = ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"]
    optional_fields = ["MMSE"]
    
    schema_props = dataset_schema.get("properties", {})
    missing_required = [f for f in required_fields if f not in schema_props]
    if missing_required:
        log_error(f"Missing required fields in dataset schema: {missing_required}")
        raise ValueError(f"Schema validation failed: missing fields {missing_required}")
    
    if "MMSE" not in schema_props:
        log_warning("MMSE field is missing from schema (expected to be optional)")
    else:
        log_info("MMSE field present in schema (optional)")

    # Generate and write output schema
    output_schema = generate_output_schema()
    output_schema_path = contracts_dir / "output.schema.yaml"
    write_schema(output_schema, output_schema_path)

    log_info("Contract schemas generated successfully.")

if __name__ == "__main__":
    main()
