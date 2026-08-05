"""
T007b: Update Schema for Ratified Path.

Reads data/amendment_log.json to determine the active methodology.
Updates specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml
to define 'flavor_similarity' based on the ratified path:
- "Correlational Analysis" -> "Recipe1M embedding cosine similarity"
- "Causal Independence" -> "FlavorDB chemical vectors"

Constraint: Fails loudly if amendment log is missing or status is not "RATIFIED".
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AMENDMENT_LOG_PATH = PROJECT_ROOT / "data" / "amendment_log.json"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-statistical-analysis-of-recipe-data" / "contracts" / "dataset.schema.yaml"

def load_amendment_log() -> dict:
    """Load and validate the amendment log."""
    if not AMENDMENT_LOG_PATH.exists():
        raise FileNotFoundError(
            f"Amendment log not found at {AMENDMENT_LOG_PATH}. "
            "Run T012d_ratification_gate first."
        )
    
    with open(AMENDMENT_LOG_PATH, 'r') as f:
        log = json.load(f)
    
    if log.get('status') != 'RATIFIED':
        raise RuntimeError(
            f"Amendment log status is '{log.get('status')}', expected 'RATIFIED'. "
            "Pipeline halted until ratification is complete."
        )
    
    return log

def load_schema() -> dict:
    """Load the existing schema file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found at {SCHEMA_PATH}. "
            "Ensure T007a (Create base data schema definitions) has been completed."
        )
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def update_schema(schema: dict, methodology: str) -> dict:
    """Update the schema definition based on the methodology."""
    if 'properties' not in schema:
        raise ValueError("Schema missing 'properties' key.")
    
    if 'flavor_similarity' not in schema['properties']:
        logger.warning("flavor_similarity field not found in schema; adding it.")
        schema['properties']['flavor_similarity'] = {}

    if methodology == "Correlational Analysis":
        schema['properties']['flavor_similarity']['description'] = "Recipe1M embedding cosine similarity"
        schema['properties']['flavor_similarity']['type'] = "number"
        schema['properties']['flavor_similarity']['source'] = "Recipe1M"
        schema['properties']['flavor_similarity']['method'] = "cosine_similarity"
        logger.info("Updated schema for Correlational Analysis (Recipe1M embeddings).")
    elif methodology == "Causal Independence":
        schema['properties']['flavor_similarity']['description'] = "FlavorDB chemical vectors"
        schema['properties']['flavor_similarity']['type'] = "array"
        schema['properties']['flavor_similarity']['source'] = "FlavorDB"
        schema['properties']['flavor_similarity']['method'] = "chemical_vector_distance"
        logger.info("Updated schema for Causal Independence (FlavorDB chemical vectors).")
    else:
        raise ValueError(f"Unknown methodology: {methodology}. Expected 'Correlational Analysis' or 'Causal Independence'.")
    
    return schema

def save_schema(schema: dict) -> None:
    """Save the updated schema back to the file."""
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_PATH, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Schema saved to {SCHEMA_PATH}")

def main():
    try:
        logger.info("Starting T007b: Update Schema for Ratified Path")
        
        # 1. Load Amendment Log
        amendment_log = load_amendment_log()
        methodology = amendment_log.get('methodology')
        logger.info(f"Detected methodology: {methodology}")
        
        # 2. Load Existing Schema
        schema = load_schema()
        
        # 3. Update Schema
        updated_schema = update_schema(schema, methodology)
        
        # 4. Save Updated Schema
        save_schema(updated_schema)
        
        logger.info("T007b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
