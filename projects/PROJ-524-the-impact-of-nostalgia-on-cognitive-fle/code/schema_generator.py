import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generate the dataset schema based on the Data Model (T020b).
    Defines fields: participant_id, age, stimulus_type, perseverative_errors,
    categories_completed, and optional MMSE.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NostalgiaCognitiveFlexibilityDataset",
        "description": "Schema for the WCST/Nostalgia study dataset.",
        "type": "object",
        "properties": {
            "participant_id": {
                "type": "string",
                "description": "Unique identifier for the participant."
            },
            "age": {
                "type": "integer",
                "description": "Age of the participant in years.",
                "minimum": 0
            },
            "stimulus_type": {
                "type": "string",
                "description": "Type of stimulus presented (e.g., 'nostalgia', 'control').",
                "enum": ["nostalgia", "control"]
            },
            "perseverative_errors": {
                "type": "integer",
                "description": "Number of perseverative errors on the WCST.",
                "minimum": 0
            },
            "categories_completed": {
                "type": "integer",
                "description": "Number of categories completed on the WCST.",
                "minimum": 0
            },
            "MMSE": {
                "type": ["integer", "null"],
                "description": "Mini-Mental State Examination score. Optional field.",
                "minimum": 0,
                "maximum": 30
            }
        },
        "required": ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"]
    }
    return schema

def generate_output_schema() -> Dict[str, Any]:
    """
    Generate the output schema for analysis results.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NostalgiaCognitiveFlexibilityOutput",
        "description": "Schema for statistical analysis output.",
        "type": "object",
        "properties": {
            "analysis_date": {
                "type": "string",
                "description": "ISO 8601 timestamp of the analysis."
            },
            "sample_sizes": {
                "type": "object",
                "properties": {
                    "nostalgia_group": {"type": "integer"},
                    "control_group": {"type": "integer"}
                },
                "required": ["nostalgia_group", "control_group"]
            },
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string"},
                        "test_type": {"type": "string"},
                        "statistic": {"type": "number"},
                        "p_value": {"type": "number"},
                        "p_value_corrected": {"type": "number"},
                        "effect_size_cohen_d": {"type": "number"},
                        "ci_lower": {"type": "number"},
                        "ci_upper": {"type": "number"},
                        "significant": {"type": "boolean"}
                    },
                    "required": ["metric", "test_type", "statistic", "p_value"]
                }
            },
            "power_analysis": {
                "type": "object",
                "properties": {
                    "achieved_power": {"type": "number"},
                    "minimum_detectable_effect": {"type": "number"}
                }
            }
        },
        "required": ["analysis_date", "sample_sizes", "results"]
    }
    return schema

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Write a schema dictionary to a YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    log_info(f"Schema written to {output_path}")

def main() -> None:
    """
    Main entry point for T020a: Generate Contracts.
    """
    setup_logging()
    log_info(f"Starting T020a: Generate Contracts at {get_timestamp()}")

    contracts_dir = Path("contracts")
    contracts_dir.mkdir(parents=True, exist_ok=True)

    # Generate and write dataset schema
    dataset_schema = generate_dataset_schema()
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    write_schema(dataset_schema, dataset_schema_path)

    # Generate and write output schema
    output_schema = generate_output_schema()
    output_schema_path = contracts_dir / "output.schema.yaml"
    write_schema(output_schema, output_schema_path)

    # Validation check (log only, as per task description)
    required_fields = ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"]
    optional_fields = ["MMSE"]
    
    schema_props = dataset_schema["properties"]
    missing_required = [f for f in required_fields if f not in schema_props]
    
    if missing_required:
        log_error(f"Validation failed: Missing required fields in schema: {missing_required}")
        return
    
    if "MMSE" not in schema_props:
        log_warning("Validation warning: Optional field 'MMSE' not found in schema.")
    else:
        # Check if it allows null
        mmse_def = schema_props["MMSE"]
        if isinstance(mmse_def["type"], list) and "null" in mmse_def["type"]:
            log_info("Validation passed: 'MMSE' is correctly defined as optional.")
        else:
            log_warning("Validation warning: 'MMSE' defined but type does not explicitly include 'null'.")

    log_info("T020a completed successfully.")

if __name__ == "__main__":
    main()
