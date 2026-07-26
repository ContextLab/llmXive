import os
import yaml
from pathlib import Path
from typing import Dict, Any
from utils import setup_logging, log_info, log_warning, get_timestamp
from config import ensure_dirs, get_config

logger = None

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generates the schema definition for the input dataset based on plan.md entities.
    Defines expected columns, types, and constraints for the ingestion pipeline.
    """
    schema = {
        "schema_name": "nostalgia_cognitive_flexibility_dataset",
        "version": "1.0.0",
        "generated_at": get_timestamp(),
        "description": "Schema for raw and processed data regarding nostalgia and cognitive flexibility in aging adults.",
        "entities": {
            "participant": {
                "description": "Core participant demographic and screening data.",
                "fields": [
                    {"name": "participant_id", "type": "string", "required": True, "description": "Unique identifier for the participant."},
                    {"name": "age", "type": "integer", "required": True, "description": "Age in years. Filtered for >= 65."},
                    {"name": "birth_year", "type": "integer", "required": False, "description": "Fallback for age calculation if age is missing."},
                    {"name": "gender", "type": "string", "required": False, "description": "Gender of the participant."},
                    {"name": "education_years", "type": "integer", "required": False, "description": "Years of formal education."},
                    {"name": "MMSE", "type": "float", "required": False, "description": "Mini-Mental State Examination score. Used for cognitive impairment exclusion if available."}
                ]
            },
            "cognitive_task": {
                "description": "Results from the Wisconsin Card Sorting Test (WCST) or equivalent executive function tasks.",
                "fields": [
                    {"name": "stimulus_type", "type": "string", "required": True, "description": "Condition type: 'nostalgia' or 'control'."},
                    {"name": "perseverative_errors", "type": "integer", "required": True, "description": "Number of perseverative errors made."},
                    {"name": "categories_completed", "type": "integer", "required": True, "description": "Number of sorting categories successfully completed."},
                    {"name": "total_tries", "type": "integer", "required": False, "description": "Total number of trials attempted."},
                    {"name": "response_time_avg", "type": "float", "required": False, "description": "Average response time in seconds."}
                ]
            }
        },
        "constraints": {
            "age_min": 65,
            "stimulus_values": ["nostalgia", "control"],
            "required_columns": ["participant_id", "stimulus_type", "perseverative_errors", "categories_completed", "age"]
        }
    }
    return schema

def generate_output_schema() -> Dict[str, Any]:
    """
    Generates the schema definition for the analysis output (statistical report).
    Defines the structure for statistical results, effect sizes, and power analysis.
    """
    schema = {
        "schema_name": "nostalgia_cognitive_flexibility_output",
        "version": "1.0.0",
        "generated_at": get_timestamp(),
        "description": "Schema for statistical analysis results and reports.",
        "entities": {
            "statistical_comparison": {
                "description": "Results of the Welch's t-test between nostalgia and control groups.",
                "fields": [
                    {"name": "metric", "type": "string", "required": True, "description": "The cognitive metric being compared (e.g., perseverative_errors)."},
                    {"name": "group_nostalgia_mean", "type": "float", "required": True},
                    {"name": "group_nostalgia_std", "type": "float", "required": True},
                    {"name": "group_control_mean", "type": "float", "required": True},
                    {"name": "group_control_std", "type": "float", "required": True},
                    {"name": "t_statistic", "type": "float", "required": True},
                    {"name": "p_value", "type": "float", "required": True},
                    {"name": "p_value_corrected", "type": "float", "required": True, "description": "Bonferroni corrected p-value."},
                    {"name": "cohens_d", "type": "float", "required": True},
                    {"name": "cohens_d_ci_lower", "type": "float", "required": True},
                    {"name": "cohens_d_ci_upper", "type": "float", "required": True}
                ]
            },
            "power_analysis": {
                "description": "Post-hoc power analysis results.",
                "fields": [
                    {"name": "metric", "type": "string", "required": True},
                    {"name": "observed_power", "type": "float", "required": True},
                    {"name": "min_detectable_effect_size", "type": "float", "required": True},
                    {"name": "alpha_level", "type": "float", "required": True}
                ]
            },
            "summary": {
                "description": "High-level summary of the analysis.",
                "fields": [
                    {"name": "total_participants", "type": "integer", "required": True},
                    {"name": "nostalgia_count", "type": "integer", "required": True},
                    {"name": "control_count", "type": "integer", "required": True},
                    {"name": "exclusion_count", "type": "integer", "required": True},
                    {"name": "has_mmse_filter_applied", "type": "boolean", "required": True}
                ]
            }
        },
        "output_files": [
            "data/results/statistical_report.json",
            "data/results/sensitivity_report.json"
        ]
    }
    return schema

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Writes a schema dictionary to a YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    log_info(f"Schema written to {output_path}")

def main():
    """
    Main entry point to generate and save the schema files.
    """
    global logger
    logger = setup_logging("schema_generator")
    config = get_config()
    
    # Ensure contracts directory exists
    contracts_dir = Path(config.get('contracts_dir', 'contracts'))
    ensure_dirs([contracts_dir])
    
    # Generate Dataset Schema
    dataset_schema = generate_dataset_schema()
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    write_schema(dataset_schema, dataset_schema_path)
    
    # Generate Output Schema
    output_schema = generate_output_schema()
    output_schema_path = contracts_dir / "output.schema.yaml"
    write_schema(output_schema, output_schema_path)
    
    log_info("T007 Completed: Generated dataset.schema.yaml and output.schema.yaml")

if __name__ == "__main__":
    main()
