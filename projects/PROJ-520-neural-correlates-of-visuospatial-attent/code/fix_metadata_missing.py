import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from config import get_config, get_paths
from logger import get_logger

logger = get_logger(__name__)

def generate_default_feature_metadata() -> Dict[str, Any]:
    """
    Generate default feature metadata with real data source information.
    This function is called when metadata.json is missing or incomplete.
    """
    config = get_config()
    paths = get_paths()
    
    # Ensure the output directory exists
    paths['processed'].mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'data_source_url': config.get('DATA_SOURCE_URL', 'https://openneuro.org/datasets/ds0001171'),
        'fetch_method': config.get('FETCH_METHOD', 'mne.datasets.openneuro.fetch'),
        'processing_date': None,  # Will be set when saved
        'version': '1.0.0',
        'description': 'Metadata for neural correlates of visuospatial attention study',
        'features': {
            'electrodes': ['P3', 'Pz', 'P4', 'F3', 'Fz', 'F4'],
            'bands': ['alpha', 'beta'],
            'epochs_duration': 2.0,  # seconds
            'sampling_rate': None  # Will be populated from data
        },
        'statistics': {
            'total_epochs': 0,
            'epochs_per_condition': {},
            'feature_count': 0
        },
        'validation': {
            'passed': False,
            'checks': []
        }
    }
    
    return metadata

def save_metadata(metadata: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """Save metadata to JSON file."""
    if output_path is None:
        paths = get_paths()
        output_path = paths['processed'] / 'metadata.json'
    else:
        output_path = Path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set processing date
    from datetime import datetime
    metadata['processing_date'] = datetime.now().isoformat()
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata saved to {output_path}")

def main():
    """Main entry point for fixing missing metadata."""
    logger.info("Starting metadata fix process")
    
    # Check if metadata already exists
    paths = get_paths()
    metadata_path = paths['processed'] / 'metadata.json'
    
    if metadata_path.exists():
        logger.info(f"Metadata already exists at {metadata_path}. Loading...")
        with open(metadata_path, 'r') as f:
            existing_metadata = json.load(f)
        
        # Check if required fields are present
        required_fields = ['data_source_url', 'fetch_method']
        missing_fields = [field for field in required_fields if field not in existing_metadata]
        
        if not missing_fields:
            logger.info("All required fields are present. No fix needed.")
            return
        else:
            logger.warning(f"Missing required fields: {missing_fields}. Updating...")
            # Update existing metadata with missing fields
            config = get_config()
            if 'data_source_url' not in existing_metadata:
                existing_metadata['data_source_url'] = config.get('DATA_SOURCE_URL')
            if 'fetch_method' not in existing_metadata:
                existing_metadata['fetch_method'] = config.get('FETCH_METHOD')
            save_metadata(existing_metadata)
    else:
        logger.info(f"Metadata file not found at {metadata_path}. Generating new metadata...")
        metadata = generate_default_feature_metadata()
        save_metadata(metadata)
    
    logger.info("Metadata fix process completed")

if __name__ == "__main__":
    main()
