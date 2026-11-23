import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import csv

from utils.config import get_project_root, get_data_processed_path, get_output_path

logger = logging.getLogger(__name__)

def load_metadata(metadata_path: Optional[str] = None) -> Dict[str, Any]:
    """Load metadata.yaml from the data directory."""
    if metadata_path is None:
        project_root = get_project_root()
        metadata_path = str(project_root / "data" / "metadata.yaml")
    
    path = Path(metadata_path)
    if not path.exists():
        logger.warning(f"Metadata file not found at {metadata_path}, creating new structure.")
        return {"datasets": {}, "version": "1.0", "flags": {}}
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_metadata(metadata: Dict[str, Any], metadata_path: Optional[str] = None) -> None:
    """Save metadata.yaml to the data directory."""
    if metadata_path is None:
        project_root = get_project_root()
        metadata_path = str(project_root / "data" / "metadata.yaml")
    
    path = Path(metadata_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def add_associational_only_flag_to_dataset(metadata: Dict[str, Any], dataset_name: str) -> Dict[str, Any]:
    """
    Add or update the 'associational_only' flag for a specific dataset in metadata.
    
    Args:
        metadata: The metadata dictionary.
        dataset_name: The name/key of the dataset (e.g., 'halo_shapes').
    
    Returns:
        The updated metadata dictionary.
    """
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    
    if dataset_name not in metadata["datasets"]:
        metadata["datasets"][dataset_name] = {}
    
    metadata["datasets"][dataset_name]["associational_only"] = True
    logger.info(f"Added associational_only=true flag to dataset: {dataset_name}")
    return metadata

def add_associational_only_flag_to_csv(csv_path: str) -> None:
    """
    Append 'associational_only' metadata to the CSV file itself as a comment or header extension.
    Since CSV doesn't support headers for metadata, we append a row at the end or modify the file.
    However, the task asks for the flag in the OUTPUT DATASETS. 
    Standard practice for CSV metadata is often a header comment or a separate sidecar file.
    Given the constraint to modify the artifact, we will add a comment row at the top if not present,
    or ensure the metadata.yaml reflects it. 
    
    To strictly follow "Add metadata flag ... to ALL output datasets", we will:
    1. Update the YAML metadata (primary source of truth).
    2. If the CSV is expected to carry the flag inline, we can prepend a comment line.
    
    Let's implement a robust approach: Update the metadata.yaml (done via flag_all_output_datasets)
    and ensure the CSV file has a header comment or a specific row indicating the flag.
    
    We will add a comment row at the very top of the CSV file: "# associational_only: true"
    """
    path = Path(csv_path)
    if not path.exists():
        logger.warning(f"Cannot add flag to non-existent CSV: {csv_path}")
        return

    # Read existing content
    with open(path, 'r') as f:
        lines = f.readlines()

    # Check if flag comment already exists at the top
    if lines and lines[0].strip().startswith("# associational_only"):
        logger.info(f"Flag already present in {csv_path}")
        return

    # Prepend the flag comment
    new_lines = ["# associational_only: true\n"] + lines
    
    with open(path, 'w') as f:
        f.writelines(new_lines)
    
    logger.info(f"Added associational_only flag comment to {csv_path}")

def flag_all_output_datasets() -> Dict[str, Any]:
    """
    Apply the associational_only=true flag to all required output datasets:
    - data/processed/halo_shapes.csv
    - data/processed/statistical_results.csv
    - data/processed/sensitivity_report.csv
    - data/processed/millennium_results.csv
    - data/processed/alignment_angles.csv
    
    Updates both the CSV files (inline comment) and the metadata.yaml.
    """
    project_root = get_project_root()
    processed_dir = get_data_processed_path()
    processed_path = Path(project_root) / processed_dir
    
    required_files = [
        "halo_shapes.csv",
        "statistical_results.csv",
        "sensitivity_report.csv",
        "millennium_results.csv",
        "alignment_angles.csv"
    ]
    
    metadata = load_metadata()
    dataset_keys = [
        "halo_shapes",
        "statistical_results",
        "sensitivity_report",
        "millennium_results",
        "alignment_angles"
    ]
    
    for i, filename in enumerate(required_files):
        file_path = processed_path / filename
        key = dataset_keys[i]
        
        if file_path.exists():
            # 1. Update CSV with comment
            add_associational_only_flag_to_csv(str(file_path))
            # 2. Update metadata
            metadata = add_associational_only_flag_to_dataset(metadata, key)
        else:
            logger.warning(f"Output file not found: {file_path}. Skipping inline flag.")
            # Still update metadata to indicate intent/requirement
            metadata = add_associational_only_flag_to_dataset(metadata, key)
    
    # Save updated metadata
    save_metadata(metadata)
    logger.info("Successfully flagged all output datasets as associational_only=true")
    return metadata

def main():
    """Entry point for running the flagging process."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting associational_only flagging for all output datasets...")
    
    try:
        flag_all_output_datasets()
        logger.info("Flagging completed successfully.")
    except Exception as e:
        logger.error(f"Failed to flag datasets: {e}")
        raise

if __name__ == "__main__":
    main()
