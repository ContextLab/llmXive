"""
T015: Implement download and verification for Persona-Chat dataset.

Fetches 'cardinal/canonical-persona-chat' from HuggingFace as a PRIMARY input.
Verifies schema fields, stores raw data, and generates checksums.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.data_integrity import compute_directory_checksum, generate_manifest
from utils.env_config import get_hf_token
from utils.schema_validator import validate_dataset_schema, load_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'download_persona_chat.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "cardinal/canonical-persona-chat"
REQUIRED_FIELDS = ["quality_rating", "user_id", "dialogue_id"]
RAW_DATA_DIR = project_root / "data" / "raw" / "persona_chat"
CHECKSUMS_FILE = RAW_DATA_DIR / "checksums.json"
MANIFEST_FILE = RAW_DATA_DIR / "manifest.json"
VALIDATION_REPORT_FILE = RAW_DATA_DIR / "validation_status.json"


def ensure_directories():
    """Create necessary directories for raw data and logs."""
    dirs = [
        RAW_DATA_DIR,
        project_root / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {[str(d) for d in dirs]}")


def load_dataset_with_check(dataset_id: str, split: str = "train") -> Any:
    """
    Load dataset from HuggingFace with error handling.
    
    Args:
        dataset_id: HuggingFace dataset identifier
        split: Dataset split to load
        
    Returns:
        Loaded dataset object
        
    Raises:
        RuntimeError: If dataset cannot be loaded or fields are missing
    """
    logger.info(f"Loading dataset: {dataset_id} (split: {split})")
    try:
        # Use HF token if available
        token = get_hf_token()
        dataset = load_dataset(
            dataset_id, 
            split=split, 
            token=token,
            trust_remote_code=True
        )
        logger.info(f"Successfully loaded {len(dataset)} records from {dataset_id}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {str(e)}")
        raise RuntimeError(f"Dataset loading failed: {str(e)}") from e


def validate_and_preprocess(dataset: Any) -> bool:
    """
    Validate dataset has required fields and basic integrity.
    
    Args:
        dataset: Loaded dataset object
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If required fields are missing
    """
    logger.info("Validating dataset schema...")
    
    # Check required fields
    columns = dataset.column_names
    missing_fields = [f for f in REQUIRED_FIELDS if f not in columns]
    
    if missing_fields:
        error_msg = f"Missing required fields: {missing_fields}. Available: {columns}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Schema validation passed. Required fields present: {REQUIRED_FIELDS}")
    
    # Optional: Validate against schema contract
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    if schema_path.exists():
        try:
            schema = load_schema(schema_path)
            # Basic validation check (schema validator might need adaptation for HF dataset format)
            logger.info("Schema contract validation attempted.")
        except Exception as e:
            logger.warning(f"Schema contract validation skipped/warned: {e}")
    
    return True


def save_raw_data(dataset: Any, output_dir: Path):
    """
    Save dataset to disk in a structured format.
    
    Args:
        dataset: Dataset to save
        output_dir: Directory to save data
    """
    logger.info(f"Saving raw data to {output_dir}")
    
    # Convert to pandas for easier saving and inspection
    df = dataset.to_pandas()
    
    # Save as parquet (efficient format)
    parquet_path = output_dir / "persona_chat_raw.parquet"
    df.to_parquet(parquet_path, index=False)
    logger.info(f"Saved {len(df)} records to {parquet_path}")
    
    # Save as JSON lines for human readability/debugging
    jsonl_path = output_dir / "persona_chat_raw.jsonl"
    df.to_json(jsonl_path, orient='records', lines=True)
    logger.info(f"Saved {len(df)} records to {jsonl_path}")


def generate_checksums_and_manifest(data_dir: Path):
    """Generate checksums and manifest for the downloaded data."""
    logger.info("Generating checksums and manifest...")
    
    # Generate file manifest
    manifest = generate_manifest(data_dir)
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {MANIFEST_FILE}")
    
    # Compute directory checksum
    checksum = compute_directory_checksum(data_dir)
    checksums = {
        "directory": str(data_dir),
        "checksum": checksum,
        "timestamp": str(Path(__file__).stat().st_mtime),
        "dataset_id": DATASET_ID
    }
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {CHECKSUMS_FILE}")


def save_validation_report(status: str, details: Dict[str, Any]):
    """Save validation status to file."""
    report = {
        "dataset": DATASET_ID,
        "status": status,
        "details": details,
        "timestamp": str(Path(__file__).stat().st_mtime)
    }
    with open(VALIDATION_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {VALIDATION_REPORT_FILE}")


def main():
    """Main execution function for T015."""
    logger.info("=" * 60)
    logger.info("Starting T015: Download Persona-Chat Dataset")
    logger.info("=" * 60)
    
    try:
        # 1. Ensure directories exist
        ensure_directories()
        
        # 2. Load dataset
        dataset = load_dataset_with_check(DATASET_ID)
        
        # 3. Validate schema
        validate_and_preprocess(dataset)
        
        # 4. Save raw data
        save_raw_data(dataset, RAW_DATA_DIR)
        
        # 5. Generate checksums and manifest
        generate_checksums_and_manifest(RAW_DATA_DIR)
        
        # 6. Save validation report
        save_validation_report("success", {
            "records_loaded": len(dataset),
            "fields_verified": REQUIRED_FIELDS,
            "output_files": [
                str(RAW_DATA_DIR / "persona_chat_raw.parquet"),
                str(RAW_DATA_DIR / "persona_chat_raw.jsonl")
            ]
        })
        
        logger.info("=" * 60)
        logger.info("T015 COMPLETED SUCCESSFULLY")
        logger.info(f"Data stored in: {RAW_DATA_DIR}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"T015 FAILED: {str(e)}")
        save_validation_report("failed", {"error": str(e)})
        raise


if __name__ == "__main__":
    main()