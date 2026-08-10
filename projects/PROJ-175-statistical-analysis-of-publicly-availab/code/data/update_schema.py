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

def load_amendment_log() -> dict:
    """Load the amendment log from data/amendment_log.json."""
    path = Path("data/amendment_log.json")
    if not path.exists():
        raise FileNotFoundError(f"Amendment log not found at {path}. Run T012d_ratification_gate first.")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_schema(schema_path: Path) -> dict:
    """Load the dataset schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def update_schema(schema: dict, methodology: str) -> dict:
    """
    Update the dataset schema based on the ratified methodology.
    
    If methodology is "Correlational Analysis", update flavor_similarity 
    to "Recipe1M embedding cosine similarity".
    If methodology is "Causal Independence", update flavor_similarity 
    to "FlavorDB chemical vectors".
    """
    logger.info(f"Updating schema for methodology: {methodology}")
    
    # Navigate to the IngredientPair definition
    if 'fields' not in schema:
        raise ValueError("Schema missing 'fields' key")
    
    ingredient_pair_fields = None
    for field in schema['fields']:
        if field.get('name') == 'IngredientPair':
            ingredient_pair_fields = field
            break
    
    if not ingredient_pair_fields:
        raise ValueError("Schema missing 'IngredientPair' definition")
    
    if 'properties' not in ingredient_pair_fields:
        raise ValueError("IngredientPair definition missing 'properties'")
    
    flavor_sim_prop = ingredient_pair_fields['properties'].get('flavor_similarity')
    if not flavor_sim_prop:
        raise ValueError("IngredientPair missing 'flavor_similarity' property")
    
    # Update the description based on methodology
    if methodology == "Correlational Analysis":
        flavor_sim_prop['description'] = "Recipe1M embedding cosine similarity"
        flavor_sim_prop['type'] = "float"
        flavor_sim_prop['source'] = "Recipe1M embeddings"
        logger.info("Updated flavor_similarity to Recipe1M embedding cosine similarity")
    elif methodology == "Causal Independence":
        flavor_sim_prop['description'] = "FlavorDB chemical vectors"
        flavor_sim_prop['type'] = "float"
        flavor_sim_prop['source'] = "FlavorDB chemical matrix"
        logger.info("Updated flavor_similarity to FlavorDB chemical vectors")
    else:
        raise ValueError(f"Unknown methodology: {methodology}")
    
    return schema

def save_schema(schema: dict, schema_path: Path) -> None:
    """Save the updated schema to a YAML file."""
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Schema saved to {schema_path}")

def main():
    """Main entry point for T007b: Update Schema for Ratified Path."""
    logger.info("Starting T007b: Update Schema for Ratified Path")
    
    try:
        # Load amendment log
        amendment_log = load_amendment_log()
        
        # Check if amendment is ratified
        if amendment_log.get('status') != 'RATIFIED':
            raise RuntimeError(
                f"Amendment log status is '{amendment_log.get('status')}'. "
                "Must be 'RATIFIED' to proceed with schema update. "
                "Run T012d_ratification_gate first."
            )
        
        methodology = amendment_log.get('methodology')
        if not methodology:
            raise ValueError("Amendment log missing 'methodology' key")
        
        # Define schema path
        schema_path = Path("specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml")
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Dataset schema not found at {schema_path}. "
                "Run T007a_schema_dataset first to create the base schema."
            )
        
        # Load, update, and save schema
        schema = load_schema(schema_path)
        updated_schema = update_schema(schema, methodology)
        save_schema(updated_schema, schema_path)
        
        # Log completion
        logger.info("T007b completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"T007b failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
