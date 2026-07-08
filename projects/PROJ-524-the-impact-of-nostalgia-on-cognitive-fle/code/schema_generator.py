"""
Schema Generator for llmXive Project.

This module generates JSON Schema definitions for the dataset and output artifacts
based on the project's plan.md entities and requirements.

It ensures consistency between the data model and the validation logic used
in ingestion and analysis pipelines.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Import existing utilities
from utils import setup_logging, log_info, log_warning, get_timestamp
from config import ensure_dirs, get_config

logger = setup_logging("schema_generator")

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generates the JSON Schema for the cleaned dataset.
    
    Defines structure for participant data, metadata, and exclusion tracking
    as per the project's data model.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Dataset Schema for Nostalgia and Cognitive Flexibility Study",
        "description": "Schema defining the structure and constraints for the cleaned dataset used in the study.",
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "version": {"type": "string", "description": "Schema version"},
                    "generated_at": {"type": "string", "format": "date-time", "description": "Timestamp of dataset generation"},
                    "source": {"type": "string", "description": "Original data source (e.g., OpenML ID, URL)"},
                    "checksum": {"type": "string", "description": "SHA-256 checksum of the raw source data"},
                    "mmse_available": {"type": "boolean", "description": "Flag indicating if MMSE column was present in raw data (from T013b)"},
                    "exclusion_counts": {
                        "type": "object",
                        "properties": {
                            "total_raw": {"type": "integer"},
                            "excluded_missing_age": {"type": "integer"},
                            "excluded_missing_birth_year": {"type": "integer"},
                            "excluded_missing_score": {"type": "integer"},
                            "excluded_stimulus_null": {"type": "integer"},
                            "total_excluded": {"type": "integer"}
                        }
                    }
                }
            },
            "participants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["participant_id", "stimulus_type", "age", "perseverative_errors", "categories_completed"],
                    "properties": {
                        "participant_id": {"type": "string", "description": "Unique identifier for the participant"},
                        "stimulus_type": {
                            "type": "string",
                            "enum": ["nostalgia", "control"],
                            "description": "Condition assigned to the participant"
                        },
                        "age": {
                            "type": "integer",
                            "minimum": 65,
                            "description": "Age of participant (must be >= 65)"
                        },
                        "birth_year": {"type": "integer", "description": "Optional birth year if age was derived"},
                        "perseverative_errors": {"type": "number", "description": "Number of perseverative errors on WCST"},
                        "categories_completed": {"type": "integer", "description": "Number of categories completed on WCST"},
                        "mmse_score": {
                            "type": "integer",
                            "nullable": True,
                            "minimum": 0,
                            "maximum": 30,
                            "description": "Mini-Mental State Examination score (optional, used for robustness checks)"
                        },
                        "cognitive_score": {"type": "number", "description": "Derived cognitive flexibility metric"},
                        "exclusion_reason": {"type": "string", "nullable": True, "description": "Reason for exclusion if applicable"}
                    }
                }
            }
        },
        "required": ["metadata", "participants"]
    }
    return schema

def generate_output_schema() -> Dict[str, Any]:
    """
    Generates the JSON Schema for statistical analysis outputs.
    
    Defines structure for statistical reports, sensitivity analysis,
    citation verification, and final report summaries.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Output Schema for Statistical Analysis Results",
        "description": "Schema defining the structure for statistical reports, sensitivity analysis, and final outputs.",
        "type": "object",
        "properties": {
            "statistical_report": {
                "type": "object",
                "description": "Results from Welch's t-test and effect size calculations",
                "properties": {
                    "analysis_timestamp": {"type": "string", "format": "date-time"},
                    "dataset_info": {
                        "type": "object",
                        "properties": {
                            "n_nostalgia": {"type": "integer"},
                            "n_control": {"type": "integer"},
                            "n_total": {"type": "integer"},
                            "mmse_filter_applied": {"type": "boolean"}
                        }
                    },
                    "comparisons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "metric": {"type": "string", "enum": ["perseverative_errors", "categories_completed"]},
                                "test_type": {"type": "string", "const": "Welch's t-test"},
                                "t_statistic": {"type": "number"},
                                "degrees_of_freedom": {"type": "number"},
                                "p_value": {"type": "number"},
                                "p_value_corrected": {"type": "number", "description": "Bonferroni corrected p-value"},
                                "effect_size": {
                                    "type": "object",
                                    "properties": {
                                        "cohens_d": {"type": "number"},
                                        "ci_95_lower": {"type": "number"},
                                        "ci_95_upper": {"type": "number"}
                                    }
                                },
                                "significance": {"type": "boolean"}
                            }
                        }
                    },
                    "power_analysis": {
                        "type": "object",
                        "properties": {
                            "observed_power": {"type": "number"},
                            "minimum_detectable_effect_size": {"type": "number", "description": "MDES at alpha=0.05, power=0.80"},
                            "alpha_level": {"type": "number", "const": 0.05},
                            "target_power": {"type": "number", "const": 0.80}
                        }
                    }
                }
            },
            "sensitivity_report": {
                "type": "object",
                "description": "Results from sensitivity analysis across thresholds",
                "properties": {
                    "thresholds_tested": {"type": "array", "items": {"type": "number"}, "description": "List of alpha thresholds tested (e.g., 0.01, 0.05, 0.1)"},
                    "results_by_metric": {
                        "type": "object",
                        "properties": {
                            "perseverative_errors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "threshold": {"type": "number"},
                                        "is_significant": {"type": "boolean"},
                                        "p_value": {"type": "number"}
                                    }
                                }
                            },
                            "categories_completed": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "threshold": {"type": "number"},
                                        "is_significant": {"type": "boolean"},
                                        "p_value": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "robustness_flags": {
                        "type": "object",
                        "properties": {
                            "sensitive_to_threshold": {"type": "boolean", "description": "True if p-value is borderline (≈ 0.05)"},
                            "mmse_impact": {"type": "string", "description": "Description of impact when MMSE filter is applied"}
                        }
                    }
                }
            },
            "citations": {
                "type": "object",
                "description": "Verification status of source citations",
                "properties": {
                    "source_study": {
                        "type": "object",
                        "properties": {
                            "doi": {"type": "string"},
                            "title_overlap_score": {"type": "number", "description": "Overlap score with primary source"},
                            "validated": {"type": "boolean"},
                            "stimuli_verified": {"type": "boolean", "description": "Verification of stimuli content from source"}
                        }
                    }
                }
            },
            "final_report": {
                "type": "object",
                "description": "Aggregated summary for paper generation",
                "properties": {
                    "conclusion": {"type": "string"},
                    "validity_status": {"type": "string", "enum": ["validated", "partial", "simulation_only"]},
                    "limitations": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "required": ["statistical_report", "sensitivity_report", "final_report"]
    }
    return schema

def write_schema(schema: Dict[str, Any], filepath: Path) -> None:
    """Writes a schema dictionary to a YAML file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    logger.info(f"Schema written to {filepath}")

def main() -> None:
    """Main entry point to generate contract schemas."""
    logger.info("Starting schema generation for contracts...")
    
    # Ensure contracts directory exists
    contracts_dir = Path("contracts")
    ensure_dirs([contracts_dir])
    
    # Generate and write dataset schema
    dataset_schema = generate_dataset_schema()
    dataset_path = contracts_dir / "dataset.schema.yaml"
    write_schema(dataset_schema, dataset_path)
    
    # Generate and write output schema
    output_schema = generate_output_schema()
    output_path = contracts_dir / "output.schema.yaml"
    write_schema(output_schema, output_path)
    
    logger.info("Schema generation complete.")

if __name__ == "__main__":
    main()
