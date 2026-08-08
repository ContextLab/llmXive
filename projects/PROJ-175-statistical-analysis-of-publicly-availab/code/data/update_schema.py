import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_amendment_log(log_path: str = "data/amendment_log.json") -> dict:
    """Load the amendment log to determine the active methodology."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Amendment log not found at {log_path}. Run T012d_ratification_gate first.")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    if data.get("status") != "RATIFIED":
        raise RuntimeError(f"Amendment log status is '{data.get('status')}'. Must be 'RATIFIED' to update schema.")
    
    return data

def load_schema(schema_path: str = "specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml") -> dict:
    """Load the current schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}. Run T007a first.")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def update_schema(schema: dict, methodology: str, proxy_source: str = None) -> dict:
    """
    Update the schema based on the ratified methodology.
    
    Logic:
    - If "Correlational Analysis", define `flavor_similarity` as "Recipe1M embedding cosine similarity".
    - If "Causal Independence", define `flavor_similarity` as "FlavorDB chemical vectors".
    """
    logger.info(f"Updating schema for methodology: {methodology}, proxy: {proxy_source}")
    
    # Ensure the fields section exists
    if "fields" not in schema:
        schema["fields"] = []
    
    # Find or create the flavor_similarity field definition
    flavor_sim_field = None
    for field in schema["fields"]:
        if field.get("name") == "flavor_similarity":
            flavor_sim_field = field
            break
    
    if not flavor_sim_field:
        flavor_sim_field = {"name": "flavor_similarity", "type": "float", "description": ""}
        schema["fields"].append(flavor_sim_field)
    
    # Update description based on methodology
    if methodology == "Correlational Analysis":
        flavor_sim_field["description"] = "Cosine similarity between ingredient embeddings from Recipe1M corpus."
        flavor_sim_field["source"] = "Recipe1M"
        flavor_sim_field["computation"] = "cosine_similarity(embedding_i, embedding_j)"
    elif methodology == "Causal Independence":
        flavor_sim_field["description"] = "Chemical vector similarity derived from FlavorDB."
        flavor_sim_field["source"] = "FlavorDB"
        flavor_sim_field["computation"] = "cosine_similarity(chemical_vector_i, chemical_vector_j)"
    else:
        raise ValueError(f"Unknown methodology: {methodology}")
    
    # Update metadata timestamp
    schema["metadata"] = schema.get("metadata", {})
    schema["metadata"]["last_updated"] = datetime.now().isoformat()
    schema["metadata"]["methodology"] = methodology
    schema["metadata"]["proxy_source"] = proxy_source
    
    return schema

def save_schema(schema: dict, schema_path: str = "specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml"):
    """Save the updated schema back to disk."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(schema_path), exist_ok=True)
    
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Schema saved to {schema_path}")

def main():
    """Main entry point for T007b."""
    try:
        # 1. Load Amendment Log
        amendment_log = load_amendment_log()
        methodology = amendment_log.get("methodology")
        proxy_source = amendment_log.get("proxy_source")
        
        logger.info(f"Amendment Log Status: {amendment_log.get('status')}")
        logger.info(f"Methodology: {methodology}")
        logger.info(f"Proxy Source: {proxy_source}")
        
        # 2. Load Current Schema
        schema_path = "specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml"
        schema = load_schema(schema_path)
        
        # 3. Update Schema
        updated_schema = update_schema(schema, methodology, proxy_source)
        
        # 4. Save Updated Schema
        save_schema(updated_schema, schema_path)
        
        print("T007b completed successfully: Schema updated.")
        
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
