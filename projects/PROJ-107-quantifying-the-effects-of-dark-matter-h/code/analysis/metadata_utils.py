"""
Metadata utilities for adding the associational_only flag to output datasets.

This module provides functions to load, modify, and save metadata files
with the associational_only=true flag for all output datasets.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import csv

# Configure logging
logger = logging.getLogger(__name__)

def load_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load metadata from a YAML file.
    
    Args:
        metadata_path: Path to the metadata.yaml file
        
    Returns:
        Dictionary containing metadata
    """
    path = Path(metadata_path)
    if not path.exists():
        logger.warning(f"Metadata file not found: {metadata_path}. Creating new metadata.")
        return {
            "version": "1.0.0",
            "datasets": {},
            "pipeline_info": {
                "associational_only": False
            }
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_metadata(metadata: Dict[str, Any], metadata_path: str) -> None:
    """
    Save metadata to a YAML file.
    
    Args:
        metadata: Dictionary containing metadata
        metadata_path: Path to save the metadata.yaml file
    """
    path = Path(metadata_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Metadata saved to {metadata_path}")

def add_associational_only_flag_to_dataset(
    metadata: Dict[str, Any],
    dataset_name: str,
    file_path: str
) -> Dict[str, Any]:
    """
    Add or update the associational_only=true flag for a specific dataset.
    
    Args:
        metadata: Current metadata dictionary
        dataset_name: Name of the dataset
        file_path: Path to the dataset file
        
    Returns:
        Updated metadata dictionary
    """
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    # Ensure pipeline_info exists
    if "pipeline_info" not in metadata:
        metadata["pipeline_info"] = {}
    
    # Set the global flag
    metadata["pipeline_info"]["associational_only"] = True
    
    # Add/update dataset entry
    metadata["datasets"][dataset_name] = {
        "path": file_path,
        "associational_only": True,
        "description": "Output dataset with associational-only flag (correlation does not imply causation)"
    }
    
    logger.info(f"Added associational_only=true flag to dataset: {dataset_name}")
    return metadata

def add_associational_only_flag_to_csv(
    csv_path: str,
    flag_name: str = "associational_only",
    flag_value: str = "true"
) -> None:
    """
    Add a metadata flag column to a CSV file.
    
    This function reads a CSV file, adds a new column with the associational_only flag,
    and writes the updated CSV back to disk.
    
    Args:
        csv_path: Path to the CSV file
        flag_name: Name of the flag column
        flag_value: Value to set for the flag
    """
    path = Path(csv_path)
    if not path.exists():
        logger.warning(f"CSV file not found: {csv_path}. Skipping flag addition.")
        return
    
    # Read the CSV
    df = pd.read_csv(csv_path)
    
    # Add the flag column
    df[flag_name] = flag_value
    
    # Write back to CSV
    df.to_csv(csv_path, index=False)
    logger.info(f"Added {flag_name}={flag_value} column to {csv_path}")

def flag_all_output_datasets(
    metadata_path: str,
    output_files: List[str]
) -> Dict[str, Any]:
    """
    Add associational_only=true flag to all output datasets.
    
    Args:
        metadata_path: Path to the metadata.yaml file
        output_files: List of output file paths to flag
        
    Returns:
        Updated metadata dictionary
    """
    metadata = load_metadata(metadata_path)
    
    for file_path in output_files:
        if not Path(file_path).exists():
            logger.warning(f"Output file not found: {file_path}. Skipping.")
            continue
        
        # Extract dataset name from file path
        dataset_name = Path(file_path).stem
        
        # Add flag to metadata
        metadata = add_associational_only_flag_to_dataset(
            metadata,
            dataset_name,
            file_path
        )
        
        # Add flag column to CSV if applicable
        if file_path.endswith('.csv'):
            add_associational_only_flag_to_csv(file_path)
    
    # Save updated metadata
    save_metadata(metadata, metadata_path)
    
    return metadata

def main():
    """
    Main function to add associational_only flag to all output datasets.
    
    This function is designed to be run after T017, T025, T030, and T038
    generate their respective output files.
    """
    # Define output files that need the flag
    output_files = [
        "data/processed/halo_shapes.csv",
        "data/processed/statistical_results.csv",
        "data/processed/sensitivity_report.csv",
        "data/processed/millennium_results.csv",
        "data/processed/alignment_angles.csv"
    ]
    
    # Metadata path
    metadata_path = "data/metadata.yaml"
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Resolve full paths
    output_files = [str(project_root / f) for f in output_files]
    metadata_path = str(project_root / metadata_path)
    
    logger.info(f"Adding associational_only=true flag to {len(output_files)} output datasets")
    logger.info(f"Metadata will be updated at: {metadata_path}")
    
    try:
        metadata = flag_all_output_datasets(metadata_path, output_files)
        logger.info("Successfully added associational_only=true flag to all output datasets")
        
        # Log the updated metadata
        logger.info(f"Global flag set: {metadata.get('pipeline_info', {}).get('associational_only', False)}")
        logger.info(f"Number of flagged datasets: {len(metadata.get('datasets', {}))}")
        
    except Exception as e:
        logger.error(f"Error adding associational_only flag: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    import logging as basic_logging
    basic_logging.basicConfig(
        level=basic_logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
