import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from sibling modules based on API surface
from src.utils.config import load_config, get_config_value
from src.utils.logging import setup_logger, get_logger

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def fetch_dataset_from_hf() -> Path:
    """
    Fetch QM9-TS dataset from HuggingFace.
    This function assumes T015 has already downloaded the data.
    It locates the raw data file in the standard directory.
    """
    data_dir = get_project_root() / "data" / "raw"
    if not data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found at {data_dir}")
    
    # Look for common data formats
    dataset_files = list(data_dir.glob("*.parquet")) + list(data_dir.glob("*.csv")) + list(data_dir.glob("*.json"))
    if not dataset_files:
        raise FileNotFoundError(f"No dataset files found in {data_dir}")
    
    # Return the first found file (assumes single consolidated dataset)
    return dataset_files[0]

def load_and_count_reactions(data_path: Path) -> Tuple[int, List[Dict]]:
    """
    Load the dataset and count the total number of reactions.
    Returns count and the list of reaction records.
    """
    import pandas as pd
    
    if data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.json':
        with open(data_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                raise ValueError("JSON data must be a list of records")
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    return len(df), df.to_dict('records')

def filter_transition_metals(records: List[Dict], metals: List[str] = ["Pd", "Ni", "Cu"]) -> Tuple[int, List[Dict]]:
    """
    Filter reactions for specific transition metals (Pd, Ni, Cu).
    Returns the count of valid reactions and the filtered list.
    """
    filtered = []
    for record in records:
        # Assuming the record has a 'metal_center' field as per schema
        metal = record.get('metal_center', '')
        if metal in metals:
            filtered.append(record)
    
    return len(filtered), filtered

def handle_scarcity(count: int, threshold: int, output_path: Path) -> Dict[str, Any]:
    """
    Check if data count is below threshold (T016b logic).
    If count < threshold, creates a scarcity flag JSON file.
    Schema: { "count": <int>, "status": "scarcity", "threshold": <int> }
    If count >= threshold, logs info and does not write scarcity file.
    """
    status = {
        "count": count,
        "status": "sufficient",
        "threshold": threshold
    }
    
    if count < threshold:
        status["status"] = "scarcity"
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(status, f, indent=2)
        logging.warning(f"Data scarcity detected: {count} < {threshold}. Flag written to {output_path}")
    else:
        logging.info(f"Data sufficient: {count} >= {threshold}. No scarcity flag written.")
    
    return status

def run_ingestion() -> Dict[str, Any]:
    """
    Main ingestion pipeline:
    1. Fetch dataset (T015)
    2. Count reactions
    3. Filter for Pd, Ni, Cu (T016)
    4. Check scarcity (T016b)
    """
    logger = get_logger("ingest")
    logger.info("Starting data ingestion pipeline...")
    
    # 1. Fetch/Verify dataset
    try:
        data_path = fetch_dataset_from_hf()
        logger.info(f"Dataset found at: {data_path}")
    except FileNotFoundError as e:
        logger.error(f"Dataset not found: {e}")
        raise
    
    # 2. Load and count
    total_count, records = load_and_count_reactions(data_path)
    logger.info(f"Total reactions loaded: {total_count}")
    
    # 3. Filter for transition metals
    metals = ["Pd", "Ni", "Cu"]
    valid_count, filtered_records = filter_transition_metals(records, metals)
    logger.info(f"Valid reactions (Pd/Ni/Cu): {valid_count}")
    
    # 4. Handle scarcity (T016b)
    config = load_config()
    threshold = get_config_value(config, "THRESHOLD_DATA_SCARCITY", default=120)
    
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "data_scarcity_flag.json"
    
    result = handle_scarcity(valid_count, threshold, output_path)
    
    logger.info(f"Ingestion complete. Status: {result['status']}")
    return result

def main():
    """Entry point for the script."""
    setup_logger("ingest", level=logging.INFO)
    try:
        result = run_ingestion()
        print(json.dumps(result, indent=2))
    except Exception as e:
        logging.exception("Ingestion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()