"""
Module for downloading bulk configurations from external sources (MP/OQMD).
Includes validation against dataset schema and citation verification.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import yaml

# Import from sibling modules
from ..validators import validate_citations
from ..config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Validate dataset entries against the provided schema.
    
    Args:
        data: List of dataset entries (dictionaries)
        schema: Schema definition loaded from YAML
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If validation fails
    """
    required_fields = schema.get('required', [])
    
    if not data:
        raise ValueError("Dataset is empty; cannot validate schema.")
        
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {i} is not a dictionary.")
            
        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            raise ValueError(
                f"Entry {i} missing required fields: {missing_fields}. "
                f"Required: {required_fields}"
            )
            
        # Validate types if defined in schema
        properties = schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in entry:
                expected_type = field_schema.get('type')
                value = entry[field]
                
                type_map = {
                    'string': str,
                    'integer': int,
                    'number': (int, float),
                    'boolean': bool,
                    'array': list,
                    'object': dict
                }
                
                if expected_type and expected_type in type_map:
                    if not isinstance(value, type_map[expected_type]):
                        raise ValueError(
                            f"Entry {i}, field '{field}': expected {expected_type}, "
                            f"got {type(value).__name__}"
                        )
    
    logger.info(f"Schema validation passed for {len(data)} entries.")
    return True

def download_bulk_configs(url: str, max_retries: int = MAX_RETRIES) -> Path:
    """
    Download bulk configurations from a URL after validating citations and schema.
    
    Args:
        url: URL to download data from
        max_retries: Maximum number of retry attempts
        
    Returns:
        Path to the downloaded data file
        
    Raises:
        ValueError: If citation validation fails or data is unavailable
        RuntimeError: If download fails after all retries
    """
    # Step 1: Validate citations (T004c requirement)
    metadata_path = Path('data/metadata.yaml')
    if not metadata_path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}. Skipping citation validation.")
    else:
        logger.info("Validating citations...")
        validate_citations(url, str(metadata_path))
        logger.info("Citation validation passed.")
    
    # Step 2: Load schema for validation
    schema_path = Path('contracts/dataset.schema.yaml')
    if not schema_path.exists():
        raise FileNotFoundError(f"Dataset schema not found: {schema_path}")
    
    schema = load_schema(schema_path)
    
    # Step 3: Download with retry logic
    output_path = Path('data/raw/bulk_configs.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries} for URL: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON data
            data = response.json()
            
            # Ensure data is a list
            if isinstance(data, dict):
                # Try to find a list in the response
                if 'data' in data:
                    data = data['data']
                elif 'results' in data:
                    data = data['results']
                else:
                    # Wrap single object in list
                    data = [data]
            
            if not isinstance(data, list):
                raise ValueError("Downloaded data is not a list or cannot be converted to list.")
            
            # Step 4: Validate against schema BEFORE GB construction
            logger.info("Validating downloaded data against dataset schema...")
            validate_dataset_schema(data, schema)
            logger.info("Schema validation successful. Proceeding with GB construction.")
            
            # Save data to file
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Successfully downloaded and validated data to {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                time.sleep(RETRY_DELAY)
            continue
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"Data processing error on attempt {attempt}: {str(e)}")
            raise  # Re-raise data errors immediately
    
    # All retries failed
    logger.error(f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries}")
    raise RuntimeError(f"Download failed after {max_retries} attempts. Last error: {last_error}")

def main():
    """Main entry point for testing."""
    config = get_config_summary()
    test_url = config.get('test_data_url', 'https://materialsproject.org/static/downloads/sample_data.json')
    
    try:
        result_path = download_bulk_configs(test_url)
        print(f"Download complete. Data saved to: {result_path}")
    except Exception as e:
        print(f"Download failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
