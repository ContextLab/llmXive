import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import validate_json_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_pr_data(raw_data_path: str) -> List[Dict[str, Any]]:
    """
    Load the raw PR data from a JSON file.
    
    Args:
        raw_data_path: Path to the raw PR data JSON file.
        
    Returns:
        List of dictionaries containing PR data.
    """
    path = Path(raw_data_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw PR data file not found: {raw_data_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} PR records from {raw_data_path}")
    return data

def load_repo_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load repository metadata from a JSON file.
    
    Args:
        metadata_path: Path to the repo metadata JSON file.
        
    Returns:
        Dictionary containing repository metadata.
    """
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Repo metadata file not found: {metadata_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded repo metadata from {metadata_path}")
    return data

def save_processed_data(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save processed PR data to a CSV file with schema validation.
    
    Args:
        data: List of dictionaries containing processed PR data.
        output_path: Path to the output CSV file.
        
    Raises:
        ValueError: If schema validation fails.
    """
    if not data:
        logger.warning("No data to save. Output file will be empty.")
        # Create an empty file to ensure path exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("")
        return

    # Define the expected schema for processed data
    schema = {
        "type": "object",
        "properties": {
            "pr_id": {"type": "string"},
            "repo_name": {"type": "string"},
            "created_at": {"type": "string"},
            "merged_at": {"type": "string"},
            "turnaround_hours": {"type": "number"},
            "is_ai_assisted": {"type": "boolean"},
            "lines_changed": {"type": "number"},
            "author": {"type": "string"}
        },
        "required": ["pr_id", "repo_name", "turnaround_hours", "is_ai_assisted"]
    }

    # Validate first record against schema
    first_record = data[0]
    if not validate_json_schema(first_record, schema):
        raise ValueError("Schema validation failed for processed data")

    logger.info(f"Validated schema for {len(data)} records")

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    import csv

    fieldnames = [
        "pr_id", "repo_name", "created_at", "merged_at", 
        "turnaround_hours", "is_ai_assisted", "lines_changed", "author"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Ensure all required fields are present, use defaults if missing
            row = {field: record.get(field, "") for field in fieldnames}
            writer.writerow(row)

    logger.info(f"Saved processed data to {output_path}")

def save_raw_data(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save raw PR data to a JSON file.
    
    Args:
        data: List of dictionaries containing raw PR data.
        output_path: Path to the output JSON file.
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    logger.info(f"Saved raw data to {output_path}")

def main():
    """
    Main function to load raw data, process it, and save to CSV.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "pr_data.json"
    metadata_path = project_root / "data" / "processed" / "repo_metadata.json"
    output_path = project_root / "data" / "processed" / "pr_turnaround.csv"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Raw data path: {raw_data_path}")
    logger.info(f"Output path: {output_path}")

    try:
        # Load raw data
        raw_data = load_raw_pr_data(str(raw_data_path))
        
        # Load metadata (for reference, though not strictly needed for CSV conversion)
        try:
            metadata = load_repo_metadata(str(metadata_path))
            logger.info("Repo metadata loaded successfully")
        except FileNotFoundError:
            logger.warning("Repo metadata not found, proceeding without it")
            metadata = {}

        # Save processed data to CSV
        save_processed_data(raw_data, str(output_path))
        
        logger.info("Processing complete!")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
