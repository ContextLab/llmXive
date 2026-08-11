"""
Schema Generator Module for PROJ-524
Generates YAML schema files for dataset and output structures.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Import from project utilities
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import ensure_dirs, get_config

# Define schema content as dictionaries
DATASET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "WCST Aging Dataset Schema",
    "description": "Schema for the raw and processed dataset containing WCST performance metrics and nostalgia stimulus conditions for aging adults.",
    "type": "object",
    "required": [
        "participant_id",
        "age",
        "stimulus_type",
        "perseverative_errors",
        "categories_completed"
    ],
    "properties": {
        "participant_id": {
            "type": "string",
            "description": "Unique identifier for the participant",
            "pattern": "^[A-Z0-9]{6,12}$"
        },
        "age": {
            "type": "integer",
            "description": "Age of the participant in years",
            "minimum": 65
        },
        "stimulus_type": {
            "type": "string",
            "description": "Type of stimulus presented (nostalgia or control)",
            "enum": ["nostalgia", "control"]
        },
        "perseverative_errors": {
            "type": "integer",
            "description": "Number of perseverative errors made on the Wisconsin Card Sorting Test",
            "minimum": 0
        },
        "categories_completed": {
            "type": "integer",
            "description": "Number of categories successfully completed on the WCST",
            "minimum": 0
        },
        "MMSE": {
            "type": "integer",
            "description": "Mini-Mental State Examination score (optional field for cognitive screening)",
            "minimum": 0,
            "maximum": 30,
            "nullable": True
        },
        "response_time_ms": {
            "type": "integer",
            "description": "Average response time in milliseconds (optional)",
            "nullable": True
        },
        "trial_count": {
            "type": "integer",
            "description": "Total number of trials presented (optional)",
            "minimum": 0,
            "nullable": True
        }
    },
    "additionalProperties": False,
    "metadata": {
        "version": "1.0.0",
        "generated_at": get_timestamp(),
        "source": "spec.md Input/Output Schema"
    }
}

OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Statistical Analysis Output Schema",
    "description": "Schema for the statistical analysis output including t-test results, effect sizes, and power analysis.",
    "type": "object",
    "required": [
        "analysis_metadata",
        "group_statistics",
        "hypothesis_tests",
        "effect_sizes",
        "power_analysis"
    ],
    "properties": {
        "analysis_metadata": {
            "type": "object",
            "required": ["timestamp", "dataset_version", "analysis_type"],
            "properties": {
                "timestamp": {"type": "string", "format": "date-time"},
                "dataset_version": {"type": "string"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["welch_t_test", "bonferroni_corrected", "effect_size_analysis", "power_analysis"]
                },
                "software_version": {"type": "string"},
                "python_version": {"type": "string"}
            }
        },
        "group_statistics": {
            "type": "object",
            "required": ["nostalgia", "control"],
            "properties": {
                "nostalgia": {
                    "type": "object",
                    "required": ["n", "mean_perseverative_errors", "mean_categories_completed", "std_perseverative_errors", "std_categories_completed"],
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
                    "required": ["n", "mean_perseverative_errors", "mean_categories_completed", "std_perseverative_errors", "std_categories_completed"],
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
        "hypothesis_tests": {
            "type": "object",
            "required": ["perseverative_errors", "categories_completed"],
            "properties": {
                "perseverative_errors": {
                    "type": "object",
                    "required": ["t_statistic", "p_value", "degrees_of_freedom", "corrected_p_value", "significant"],
                    "properties": {
                        "t_statistic": {"type": "number"},
                        "p_value": {"type": "number"},
                        "degrees_of_freedom": {"type": "number"},
                        "corrected_p_value": {"type": "number"},
                        "significant": {"type": "boolean"},
                        "method": {"type": "string", "enum": ["welch_independent_samples"]}
                    }
                },
                "categories_completed": {
                    "type": "object",
                    "required": ["t_statistic", "p_value", "degrees_of_freedom", "corrected_p_value", "significant"],
                    "properties": {
                        "t_statistic": {"type": "number"},
                        "p_value": {"type": "number"},
                        "degrees_of_freedom": {"type": "number"},
                        "corrected_p_value": {"type": "number"},
                        "significant": {"type": "boolean"},
                        "method": {"type": "string", "enum": ["welch_independent_samples", "bonferroni_corrected"]}
                    }
                }
            }
        },
        "effect_sizes": {
            "type": "object",
            "required": ["perseverative_errors", "categories_completed"],
            "properties": {
                "perseverative_errors": {
                    "type": "object",
                    "required": ["cohen_d", "ci_lower", "ci_upper"],
                    "properties": {
                        "cohen_d": {"type": "number"},
                        "ci_lower": {"type": "number"},
                        "ci_upper": {"type": "number"},
                        "confidence_level": {"type": "number", "default": 0.95}
                    }
                },
                "categories_completed": {
                    "type": "object",
                    "required": ["cohen_d", "ci_lower", "ci_upper"],
                    "properties": {
                        "cohen_d": {"type": "number"},
                        "ci_lower": {"type": "number"},
                        "ci_upper": {"type": "number"},
                        "confidence_level": {"type": "number", "default": 0.95}
                    }
                }
            }
        },
        "power_analysis": {
            "type": "object",
            "required": ["achieved_power", "minimum_detectable_effect"],
            "properties": {
                "achieved_power": {
                    "type": "object",
                    "required": ["perseverative_errors", "categories_completed"],
                    "properties": {
                        "perseverative_errors": {"type": "number"},
                        "categories_completed": {"type": "number"}
                    }
                },
                "minimum_detectable_effect": {
                    "type": "object",
                    "required": ["perseverative_errors", "categories_completed"],
                    "properties": {
                        "perseverative_errors": {"type": "number"},
                        "categories_completed": {"type": "number"},
                        "power_level": {"type": "number", "default": 0.80}
                    }
                }
            }
        },
        "sensitivity_analysis": {
            "type": "object",
            "required": ["threshold_sweep", "borderline_status"],
            "properties": {
                "threshold_sweep": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "threshold": {"type": "number"},
                            "significant_pe": {"type": "boolean"},
                            "significant_cc": {"type": "boolean"}
                        }
                    }
                },
                "borderline_status": {
                    "type": "object",
                    "properties": {
                        "is_sensitive_to_threshold": {"type": "boolean"},
                        "borderline_range": {"type": "string"}
                    }
                }
            }
        }
    },
    "additionalProperties": False,
    "metadata": {
        "version": "1.0.0",
        "generated_at": get_timestamp(),
        "source": "spec.md Input/Output Schema"
    }
}

def generate_dataset_schema() -> Dict[str, Any]:
    """Generate the dataset schema dictionary."""
    return DATASET_SCHEMA

def generate_output_schema() -> Dict[str, Any]:
    """Generate the output schema dictionary."""
    return OUTPUT_SCHEMA

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """Write a schema dictionary to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    log_info(f"Schema written to: {output_path}")

def main() -> None:
    """Main entry point for schema generation."""
    # Setup logging
    log_level = get_config().get('log_level', 'INFO')
    setup_logging(level=log_level)
    
    # Ensure directories exist
    config = get_config()
    contracts_dir = Path(config.get('contracts_dir', 'contracts'))
    ensure_dirs([contracts_dir])
    
    # Generate and write dataset schema
    dataset_schema = generate_dataset_schema()
    dataset_schema_path = contracts_dir / 'dataset.schema.yaml'
    write_schema(dataset_schema, dataset_schema_path)
    
    # Generate and write output schema
    output_schema = generate_output_schema()
    output_schema_path = contracts_dir / 'output.schema.yaml'
    write_schema(output_schema, output_schema_path)
    
    log_info("Schema generation completed successfully.")

if __name__ == "__main__":
    main()
