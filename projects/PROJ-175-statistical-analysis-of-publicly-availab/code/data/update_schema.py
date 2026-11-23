import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_amendment_log(amendment_path: str) -> dict:
    """
    Load the amendment log JSON file.
    
    Args:
        amendment_path: Path to the amendment log JSON file.
        
    Returns:
        Dictionary containing the amendment log data.
        
    Raises:
        FileNotFoundError: If the amendment log file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(amendment_path):
        raise FileNotFoundError(f"Amendment log not found at {amendment_path}. Run T012d_ratification_gate first.")
    
    with open(amendment_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_schema(schema_path: str) -> dict:
    """
    Load the existing schema YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary representation of the schema (parsed as JSON-compatible dict).
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file is not valid YAML/JSON.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}. Run T007a_schema_dataset first.")
    
    # Since we are dealing with YAML, we need to handle it appropriately.
    # For simplicity, we assume the YAML is simple enough to be parsed as a dict structure
    # In a real scenario, you might want to use PyYAML or ruamel.yaml
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if PyYAML is not installed, try to parse manually or raise error
        raise ImportError("PyYAML is required to parse schema files. Install it via requirements.txt.")
    except Exception as e:
        raise ValueError(f"Failed to parse schema file: {e}")

def update_schema(schema: dict, methodology: str, proxy_source: str) -> dict:
    """
    Update the schema based on the ratified methodology.
    
    Args:
        schema: The original schema dictionary.
        methodology: The methodology string from the amendment log.
        proxy_source: The proxy source string from the amendment log.
        
    Returns:
        Updated schema dictionary.
    """
    logger.info(f"Updating schema for methodology: {methodology}, proxy_source: {proxy_source}")
    
    # Navigate to the IngredientPair definition
    # Assuming the schema structure has a 'definitions' or 'properties' section
    if 'definitions' in schema:
        ingredient_pair_def = schema['definitions'].get('IngredientPair', {})
    elif 'properties' in schema:
        ingredient_pair_def = schema['properties']
    else:
        # Fallback: try to find 'IngredientPair' directly
        ingredient_pair_def = schema.get('IngredientPair', {})
    
    # Update flavor_similarity definition based on methodology
    if methodology == "Correlational Analysis":
        flavor_similarity_def = {
            "type": "number",
            "description": "Recipe1M embedding cosine similarity",
            "computed_from": "sentence-transformers/all-MiniLM-L6-v2",
            "proxy_source": proxy_source
        }
        logger.info("Setting flavor_similarity to 'Recipe1M embedding cosine similarity' for Correlational Analysis")
    elif methodology == "Causal Independence":
        flavor_similarity_def = {
            "type": "number",
            "description": "FlavorDB chemical vectors cosine similarity",
            "computed_from": "flavordb_chemical_matrix",
            "proxy_source": None
        }
        logger.info("Setting flavor_similarity to 'FlavorDB chemical vectors' for Causal Independence")
    else:
        logger.warning(f"Unknown methodology '{methodology}'. Leaving flavor_similarity unchanged.")
        return schema
    
    # Ensure IngredientPair exists in the schema
    if 'definitions' in schema:
        schema['definitions']['IngredientPair'] = ingredient_pair_def
    elif 'properties' in schema:
        schema['properties']['IngredientPair'] = ingredient_pair_def
    else:
        schema['IngredientPair'] = ingredient_pair_def
    
    # Specifically update the flavor_similarity field within IngredientPair
    if 'properties' in ingredient_pair_def:
        ingredient_pair_def['properties']['flavor_similarity'] = flavor_similarity_def
    else:
        # If properties are defined directly in IngredientPair
        ingredient_pair_def['flavor_similarity'] = flavor_similarity_def
    
    return schema

def save_schema(schema: dict, schema_path: str) -> None:
    """
    Save the updated schema to a YAML file.
    
    Args:
        schema: The updated schema dictionary.
        schema_path: Path to save the schema YAML file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(schema_path), exist_ok=True)
    
    try:
        import yaml
        with open(schema_path, 'w', encoding='utf-8') as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Schema saved to {schema_path}")
    except ImportError:
        # Fallback if PyYAML is not installed
        raise ImportError("PyYAML is required to save schema files. Install it via requirements.txt.")
    except Exception as e:
        logger.error(f"Failed to save schema file: {e}")
        raise

def main():
    """
    Main function to execute the schema update task.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    amendment_log_path = base_dir / "data" / "amendment_log.json"
    schema_path = base_dir / "specs" / "001-statistical-analysis-of-recipe-data" / "contracts" / "dataset.schema.yaml"
    
    logger.info("Starting T007b: Update Schema for Ratified Path")
    
    try:
        # 1. Load Amendment Log
        amendment_log = load_amendment_log(str(amendment_log_path))
        
        # Verify status is RATIFIED
        if amendment_log.get('status') != 'RATIFIED':
            raise RuntimeError(f"Amendment log status is '{amendment_log.get('status')}', expected 'RATIFIED'. Cannot update schema.")
        
        methodology = amendment_log.get('methodology')
        proxy_source = amendment_log.get('proxy_source')
        
        if not methodology:
            raise RuntimeError("Methodology not found in amendment log.")
        
        # 2. Load Existing Schema
        schema = load_schema(str(schema_path))
        
        # 3. Update Schema
        updated_schema = update_schema(schema, methodology, proxy_source)
        
        # 4. Save Updated Schema
        save_schema(updated_schema, str(schema_path))
        
        logger.info("T007b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
