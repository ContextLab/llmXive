import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Ensure logging is configured before use
setup_logging()

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generates the schema for the input dataset based on the data model.
    Validates that required fields are present.
    """
    log_info("Generating dataset schema based on data model...")
    
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NostalgiaCognitiveFlexibilityDataset",
        "description": "Schema for the input dataset containing participant and cognitive metrics.",
        "type": "object",
        "properties": {
            "participant_id": {
                "type": "string",
                "description": "Unique identifier for the participant."
            },
            "age": {
                "type": "integer",
                "description": "Age of the participant in years.",
                "minimum": 65
            },
            "stimulus_type": {
                "type": "string",
                "enum": ["nostalgia", "control"],
                "description": "Type of stimulus presented to the participant."
            },
            "perseverative_errors": {
                "type": "number",
                "description": "Number of perseverative errors in the WCST.",
                "minimum": 0
            },
            "categories_completed": {
                "type": "number",
                "description": "Number of categories completed in the WCST.",
                "minimum": 0
            },
            "MMSE": {
                "type": ["number", "null"],
                "description": "Mini-Mental State Examination score (optional).",
                "minimum": 0,
                "maximum": 30
            }
        },
        "required": ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"]
    }
    
    log_info("Dataset schema generated successfully.")
    return schema

def generate_output_schema() -> Dict[str, Any]:
    """
    Generates the schema for the output analysis results.
    """
    log_info("Generating output schema for analysis results...")

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "NostalgiaCognitiveFlexibilityAnalysisReport",
        "description": "Schema for the statistical analysis output report.",
        "type": "object",
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "generated_at": {"type": "string", "format": "date-time"},
                    "version": {"type": "string"},
                    "source_file": {"type": "string"}
                }
            },
            "descriptive_statistics": {
                "type": "object",
                "properties": {
                    "nostalgia": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer"},
                            "mean_perseverative_errors": {"type": "number"},
                            "mean_categories_completed": {"type": "number"},
                            "std_perseverative_errors": {"type": "number"},
                            "std_categories_completed": {"type": "number"}
                        }
                    },
                    "control": {
                        "type": "object",
                        "properties": {
                            "n": {"type": "integer"},
                            "mean_perseverative_errors": {"type": "number"},
                            "mean_categories_completed": {"type": "number"},
                            "std_perseverative_errors": {"type": "number"},
                            "std_categories_completed": {"type": "number"}
                        }
                    }
                }
            },
            "statistical_tests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string"},
                        "test_type": {"type": "string"},
                        "statistic": {"type": "number"},
                        "p_value": {"type": "number"},
                        "p_value_corrected": {"type": "number"},
                        "effect_size": {"type": "number"},
                        "ci_lower": {"type": "number"},
                        "ci_upper": {"type": "number"}
                    }
                }
            },
            "power_analysis": {
                "type": "object",
                "properties": {
                    "achieved_power": {"type": "number"},
                    "min_detectable_effect_size": {"type": "number"}
                }
            },
            "sensitivity_analysis": {
                "type": "object",
                "properties": {
                    "thresholds_tested": {"type": "array", "items": {"type": "number"}},
                    "significance_stability": {"type": "boolean"}
                }
            }
        },
        "required": ["meta", "descriptive_statistics", "statistical_tests"]
    }

    log_info("Output schema generated successfully.")
    return schema

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the schema dictionary to a YAML file.
    """
    log_info(f"Writing schema to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    log_info(f"Schema written to {output_path}")

def main():
    """
    Main entry point to generate and save contracts.
    """
    log_info("Starting contract generation for T020a...")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    contracts_dir = project_root / "contracts"
    
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    output_schema_path = contracts_dir / "output.schema.yaml"
    
    # Generate schemas
    dataset_schema = generate_dataset_schema()
    output_schema = generate_output_schema()
    
    # Write schemas
    write_schema(dataset_schema, dataset_schema_path)
    write_schema(output_schema, output_schema_path)
    
    log_info("Contract generation completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
