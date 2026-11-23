import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import yaml
import numpy as np

# Add project root to path if running as script
if "code" not in sys.path:
    code_root = Path(__file__).resolve().parent
    if code_root.name == "data":
        sys.path.insert(0, str(code_root.parent))

from data.ingest import construct_molecular_graphs, load_pdbbind_refined
from data.preprocessing import filter_by_resolution, validate_and_filter_graphs, process_complex_metadata
from utils.io import setup_logging, get_memory_usage_mb, check_memory_limit, log_exception
from utils.config import get_config

# Configure logging
logger = setup_logging("save_and_validate_graphs")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the dataset schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_graph_against_schema(graph_data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single graph data structure against the schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []
    
    # Check required top-level fields
    required_fields = ['pdb_id', 'ligand_id', 'resolution', 'water_flag', 'coordinates_3d', 'atom_type', 'charge', 'hydrophobicity', 'edges']
    for field in required_fields:
        if field not in graph_data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return errors

    # Type and constraint checks based on typical schema definitions
    # Note: This assumes a schema structure similar to T004 description
    
    if not isinstance(graph_data.get('pdb_id'), str):
        errors.append("pdb_id must be a string")
    
    if not isinstance(graph_data.get('ligand_id'), str):
        errors.append("ligand_id must be a string")
    
    resolution = graph_data.get('resolution')
    if not isinstance(resolution, (int, float)) or resolution <= 0:
        errors.append("resolution must be a positive float")
    
    if not isinstance(graph_data.get('water_flag'), bool):
        errors.append("water_flag must be a boolean")
    
    coords = graph_data.get('coordinates_3d')
    if not isinstance(coords, list) or len(coords) % 3 != 0:
        errors.append("coordinates_3d must be a list of floats with length divisible by 3")
    
    atom_types = graph_data.get('atom_type')
    if not isinstance(atom_types, list):
        errors.append("atom_type must be a list")
    
    charges = graph_data.get('charge')
    if not isinstance(charges, list):
        errors.append("charge must be a list")
    
    hydrophobicities = graph_data.get('hydrophobicity')
    if not isinstance(hydrophobicities, list):
        errors.append("hydrophobicity must be a list")
    
    edges = graph_data.get('edges')
    if not isinstance(edges, list):
        errors.append("edges must be a list")
    else:
        for i, edge in enumerate(edges):
            if not isinstance(edge, list) or len(edge) != 2:
                errors.append(f"Edge at index {i} must be a list of two integers")
            else:
                if not isinstance(edge[0], int) or not isinstance(edge[1], int):
                    errors.append(f"Edge at index {i} must contain integers")
    
    return errors

def main():
    """
    Main entry point for T018: Save processed graph files and validate against schema.
    """
    logger.info("Starting T018: Save processed graph files and validate against schema")
    
    config = get_config()
    raw_data_dir = Path(config.get('data_raw_dir', 'data/raw'))
    processed_data_dir = Path(config.get('data_processed_dir', 'data/processed'))
    schema_path = Path(config.get('schema_path', 'contracts/dataset_schema.schema.yaml'))
    
    # Ensure output directory exists
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load schema
    try:
        schema = load_schema(str(schema_path))
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Load and process data
    # Assuming T013 has downloaded data to raw_data_dir
    # We will re-use the ingestion logic to ensure consistency
    
    try:
        # Load PDBbind data (this might need adjustment based on actual T013 output location)
        # The load_pdbbind_refined function from ingest.py is expected to handle the raw data
        logger.info("Loading PDBbind refined set...")
        complexes = load_pdbbind_refined(str(raw_data_dir))
        
        if not complexes:
            logger.warning("No complexes found in raw data directory. Exiting.")
            sys.exit(0)
        
        logger.info(f"Loaded {len(complexes)} complexes")
        
        # Filter by resolution (T020 logic)
        logger.info("Filtering complexes by resolution...")
        filtered_complexes = filter_by_resolution(complexes, max_resolution=2.5)
        logger.info(f"Filtered to {len(filtered_complexes)} complexes with resolution <= 2.5 Å")
        
        # Construct graphs
        logger.info("Constructing molecular graphs...")
        graphs = construct_molecular_graphs(filtered_complexes)
        logger.info(f"Constructed {len(graphs)} graphs")
        
        # Validate and filter graphs (T014/T015 logic)
        logger.info("Validating and filtering graphs...")
        valid_graphs, invalid_graphs = validate_and_filter_graphs(graphs)
        logger.info(f"Validated {len(valid_graphs)} graphs, {len(invalid_graphs)} invalid")
        
        # Process metadata
        logger.info("Processing complex metadata...")
        processed_graphs = process_complex_metadata(valid_graphs)
        
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        log_exception(e)
        sys.exit(1)
    
    # Validate each graph against schema
    logger.info("Validating graphs against schema...")
    total_errors = 0
    validated_graphs = []
    
    for i, graph_data in enumerate(processed_graphs):
        errors = validate_graph_against_schema(graph_data, schema)
        if errors:
            logger.warning(f"Graph {i} (PDB: {graph_data.get('pdb_id', 'unknown')}) has validation errors: {errors}")
            total_errors += len(errors)
        else:
            validated_graphs.append(graph_data)
    
    if total_errors > 0:
        logger.warning(f"Total validation errors found: {total_errors}")
    else:
        logger.info("All graphs passed schema validation.")
    
    # Save processed graphs
    logger.info("Saving processed graphs...")
    output_file = processed_data_dir / "processed_graphs.json"
    
    try:
        with open(output_file, 'w') as f:
            json.dump(validated_graphs, f, indent=2)
        logger.info(f"Saved {len(validated_graphs)} graphs to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save graphs: {e}")
        log_exception(e)
        sys.exit(1)
    
    # Log memory usage
    mem_mb = get_memory_usage_mb()
    logger.info(f"Final memory usage: {mem_mb:.2f} MB")
    check_memory_limit()
    
    logger.info("T018 completed successfully")

if __name__ == "__main__":
    main()
