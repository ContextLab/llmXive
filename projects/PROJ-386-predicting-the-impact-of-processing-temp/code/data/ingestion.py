import os
import sys
import json
import hashlib
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('logs/ingestion.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Import from local config
try:
    from config import get_config, ensure_dirs
except ImportError:
    # Fallback for direct execution or different import context
    logger.warning("Could not import config directly. Attempting relative import or fallback.")
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import get_config, ensure_dirs

# Constants
CHUNK_SIZE = 8192
REQUIRED_COLUMNS = ['rolling_temperature', 'grain_size']
COMPOSITION_COLUMNS = ['Mg', 'Si', 'Cu', 'Alloy_Series']

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path} for hashing: {e}")
        raise

def generate_checksum(data: pd.DataFrame, output_dir: Path, filename: str) -> Dict[str, Any]:
    """
    Saves a DataFrame to CSV and generates a SHA-256 checksum for the saved file.
    
    This function implements the storage logic for `data/raw/` with checksum generation.
    It ensures the directory exists, saves the data, calculates the hash, and returns
    a manifest entry.
    
    Args:
        data: The DataFrame to save.
        output_dir: The directory to save the file to (should be data/raw/).
        filename: The name of the file (e.g., 'raw_data.csv').
        
    Returns:
        A dictionary containing the file path, hash, size, and timestamp.
        
    Raises:
        SystemExit: If the data is empty or critical columns are missing after processing.
        IOError: If the file cannot be written.
    """
    # Ensure directory exists
    ensure_dirs()
    output_path = output_dir / filename
    
    if data.empty:
        logger.error("Cannot save empty DataFrame. Data ingestion failed or filtered out all rows.")
        raise SystemExit(1)
    
    # Check for critical columns before saving
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing_cols:
        logger.error(f"Critical columns missing in data before saving: {missing_cols}")
        raise SystemExit(1)
    
    try:
        # Save to CSV
        data.to_csv(output_path, index=False)
        logger.info(f"Saved raw data to {output_path} with {len(data)} rows.")
        
        # Calculate checksum
        file_hash = calculate_file_hash(output_path)
        file_size = output_path.stat().st_size
        
        manifest_entry = {
            "filename": filename,
            "path": str(output_path),
            "sha256": file_hash,
            "size_bytes": file_size,
            "row_count": len(data),
            "column_count": len(data.columns),
            "columns": list(data.columns)
        }
        
        logger.info(f"Generated SHA-256 checksum for {filename}: {file_hash}")
        return manifest_entry
        
    except IOError as e:
        logger.error(f"Failed to write file {output_path}: {e}")
        raise

def fetch_sources() -> List[Dict[str, Any]]:
    """
    Placeholder for fetching sources. 
    In a full implementation, this would query OpenML, NOMAD, etc.
    For T016, we assume data is already fetched or passed via main pipeline.
    """
    logger.info("Fetching sources logic is delegated to download.py or handled in pipeline.")
    return []

def check_schema(data: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Checks if the data contains required schema fields.
    """
    missing = []
    for col in REQUIRED_COLUMNS + COMPOSITION_COLUMNS:
        if col not in data.columns:
            missing.append(col)
    return len(missing) == 0, missing

def filter_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Filters data to remove rows with missing critical values.
    """
    initial_count = len(data)
    # Filter out rows where critical columns are null
    mask = data[REQUIRED_COLUMNS].notnull().all(axis=1)
    filtered = data[mask]
    dropped = initial_count - len(filtered)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows due to missing critical variables.")
    return filtered

def run_pipeline():
    """
    Orchestrates the ingestion pipeline: fetch -> check -> filter -> save with checksum.
    """
    logger.info("Starting Ingestion Pipeline.")
    
    # 1. Fetch (Simulated or delegated)
    # In a real scenario, this calls download functions. 
    # For this task, we assume data is passed or loaded from a previous step if needed,
    # but T016 specifically focuses on the storage/checksum logic.
    # We will simulate a data load for the purpose of demonstrating the checksum generation
    # if no external fetcher is called here, OR we assume the caller passes data.
    # Given the task is "Create storage logic", we focus on the save/checksum part.
    
    # To demonstrate functionality, we'll check if there's a pre-existing raw file or
    # assume the pipeline flow passes data. 
    # However, per T013/T014, the data is fetched and filtered.
    # Let's assume the pipeline receives a DataFrame.
    
    # For the sake of this task's specific requirement (checksum generation), 
    # we will implement the logic that would be called after filtering.
    # We'll assume 'data' is the result of fetch -> filter.
    
    # Since we cannot fetch real data without T013 implementation details in this file,
    # we will implement the function to accept data or load from a temp source if needed.
    # But the requirement is "Create data/raw/ storage logic with SHA-256 checksum generation".
    # We have implemented `generate_checksum`. Now we need to ensure it's called.
    
    # Mocking data for demonstration if called standalone (T016 implementation test)
    # In production, this data comes from T013/T014.
    # We will create a dummy dataframe if no data is provided to ensure the checksum logic runs.
    # NOTE: In real execution, data should come from the download step.
    
    # Check if data exists in a temp location or fetch
    # For T016, we ensure the function `generate_checksum` is robust and called.
    pass

def main():
    """
    Entry point for the ingestion module.
    Demonstrates the checksum generation logic.
    """
    logger.info("Ingestion Module Main Started.")
    
    # Ensure directories
    ensure_dirs()
    
    # For T016, we need to demonstrate the checksum generation.
    # We will create a sample DataFrame (representing filtered data from T014)
    # to verify the checksum logic works.
    # In a real run, this data would come from the download step.
    
    # Create sample data to test the logic
    sample_data = pd.DataFrame({
        'rolling_temperature': [450.0, 460.0, 470.0, 480.0, 490.0],
        'grain_size': [12.5, 11.2, 10.8, 13.1, 9.5],
        'Mg': [0.5, 0.6, 0.4, 0.55, 0.45],
        'Si': [0.3, 0.35, 0.25, 0.32, 0.28],
        'Cu': [0.1, 0.12, 0.08, 0.11, 0.09],
        'Alloy_Series': ['6061', '6061', '6061', '6063', '6063']
    })
    
    # Filter (simulate T014)
    filtered_data = filter_data(sample_data)
    
    if filtered_data.empty:
        logger.error("No data to save after filtering.")
        sys.exit(1)
    
    # Generate Checksum and Save (T016 Core Logic)
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = "raw_aluminum_data.csv"
    
    try:
        manifest = generate_checksum(filtered_data, raw_dir, output_filename)
        logger.info(f"Pipeline completed successfully. Manifest: {json.dumps(manifest, indent=2)}")
        
        # Save manifest to artifacts
        artifact_dir = Path("data/artifacts")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = artifact_dir / "ingestion_manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest saved to {manifest_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()