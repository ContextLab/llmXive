import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure results directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_dataset_schema() -> Dict[str, Any]:
    """
    Generate the schema for the processed dataset.
    Columns: composition, target properties, descriptors, imbalance scores
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Processed Dataset Schema",
        "type": "object",
        "properties": {
            "composition": {
                "type": "string",
                "description": "Chemical formula of the material"
            },
            "target_properties": {
                "type": "object",
                "description": "Target property values (e.g., formation_energy, band_gap)",
                "additionalProperties": {
                    "type": "number"
                }
            },
            "descriptors": {
                "type": "array",
                "description": "Magpie compositional descriptors (L2-normalized)",
                "items": {
                    "type": "number"
                }
            },
            "imbalance_scores": {
                "type": "object",
                "description": "Calculated imbalance scores per property",
                "properties": {
                    "target_imbalance": {
                        "type": "number",
                        "description": "Gini coefficient of target property"
                    },
                    "compositional_imbalance": {
                        "type": "number",
                        "description": "Gini coefficient of cluster assignment counts"
                    }
                }
            }
        },
        "required": ["composition", "target_properties", "descriptors", "imbalance_scores"]
    }
    return schema

def save_dataset_schema(schema: Dict[str, Any], output_path: str = None) -> str:
    """
    Save the dataset schema to a JSON file.
    """
    if output_path is None:
        output_path = "contracts/dataset.schema.yaml"
    
    # Ensure contracts directory exists
    contracts_dir = Path("contracts")
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)
    
    logger.info(f"Dataset schema saved to {output_path}")
    return output_path

def generate_resampling_schema() -> Dict[str, Any]:
    """
    Generate the schema for resampled datasets.
    Columns: bin_id, sample_count, CV, real_data_flag, synthetic_flag
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Resampling Schema",
        "type": "object",
        "properties": {
            "bin_id": {
                "type": "integer",
                "description": "Identifier for the bin in the resampled dataset"
            },
            "sample_count": {
                "type": "integer",
                "description": "Number of samples in this bin"
            },
            "CV": {
                "type": "number",
                "description": "Coefficient of Variation for this bin (std/mean)",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "real_data_flag": {
                "type": "boolean",
                "description": "True if this bin contains only real data"
            },
            "synthetic_flag": {
                "type": "boolean",
                "description": "True if this bin contains synthetic data (e.g., SMOTE)"
            },
            "synthetic_ratio": {
                "type": "number",
                "description": "Ratio of synthetic data in this bin (0.0 to 1.0)",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "bin_range": {
                "type": "object",
                "description": "Range of target values for this bin",
                "properties": {
                    "min": {"type": "number"},
                    "max": {"type": "number"}
                }
            }
        },
        "required": ["bin_id", "sample_count", "CV", "real_data_flag", "synthetic_flag"]
    }
    return schema

def save_resampling_schema(schema: Dict[str, Any], output_path: str = None) -> str:
    """
    Save the resampling schema to a JSON file.
    """
    if output_path is None:
        output_path = "contracts/resampling.schema.yaml"
    
    # Ensure contracts directory exists
    contracts_dir = Path("contracts")
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)
    
    logger.info(f"Resampling schema saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to generate and save all schemas.
    """
    logger.info("Starting schema generation...")
    
    # Generate and save dataset schema
    dataset_schema = generate_dataset_schema()
    save_dataset_schema(dataset_schema)
    
    # Generate and save resampling schema (T010c specific)
    resampling_schema = generate_resampling_schema()
    save_resampling_schema(resampling_schema)
    
    logger.info("All schemas generated and saved successfully.")

if __name__ == "__main__":
    main()
