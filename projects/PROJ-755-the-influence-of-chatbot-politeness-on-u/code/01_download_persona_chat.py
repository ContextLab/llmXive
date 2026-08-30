"""
Task T015b: Download Persona-Chat dataset from Hugging Face Hub.

This script fetches the Persona-Chat dataset, verifies the presence of required
fields (user_id, dialogue_id, quality_rating or proxy), saves the raw data
to data/raw/persona_chat/, and generates checksums and a manifest.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from datasets import load_dataset
from utils.data_integrity import compute_directory_checksum, generate_manifest
from utils.schema_validator import load_schema, validate_dataset_schema_wrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "download_persona_chat.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "Persona-Chat"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "persona_chat"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

# Required fields for validation
REQUIRED_FIELDS = ["user_id", "dialogue_id"]
# Persona-Chat may not have explicit 'quality_rating', we check for proxy or log warning
QUALITY_PROXY_FIELDS = ["quality_rating", "rating", "score", "sentiment"]


def ensure_directories():
    """Create necessary output directories."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_RAW_DIR / "raw_files").mkdir(parents=True, exist_ok=True)
    PROJECT_ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {DATA_RAW_DIR}")


def load_dataset_with_check(dataset_name: str) -> Any:
    """
    Load dataset from Hugging Face Hub with error handling.
    Returns the dataset object or raises an exception if failed.
    """
    logger.info(f"Attempting to load dataset: {dataset_name}")
    try:
        # Persona-Chat is on Hugging Face Hub
        # Using streaming=False to download full dataset for local storage
        # If memory is an issue, streaming=True can be used with chunked processing
        ds = load_dataset(dataset_name, split="train") # Assuming train split is the main one
        logger.info(f"Successfully loaded dataset '{dataset_name}'. Rows: {len(ds)}")
        return ds
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise


def validate_and_preprocess(dataset: Any) -> List[Dict[str, Any]]:
    """
    Validate dataset schema and preprocess if necessary.
    Checks for required fields and quality rating proxy.
    """
    logger.info("Validating dataset schema...")

    # Convert to pandas for easier validation if needed, or check dict structure
    # Assuming HuggingFace Dataset object
    columns = dataset.column_names
    logger.info(f"Dataset columns: {columns}")

    # Check required fields
    missing_fields = [f for f in REQUIRED_FIELDS if f not in columns]
    if missing_fields:
        raise ValueError(f"Missing required fields in Persona-Chat dataset: {missing_fields}")

    # Check for quality rating proxy
    quality_field = None
    for field in QUALITY_PROXY_FIELDS:
        if field in columns:
            quality_field = field
            logger.info(f"Found quality proxy field: {quality_field}")
            break

    if not quality_field:
        logger.warning("No explicit quality rating field found. Proceeding without quality score for now.")
        logger.warning("This dataset might need manual mapping or exclusion in later filtering steps.")
    else:
        # If a quality field exists, ensure it's numeric or can be mapped
        # For now, we just note its presence. T019 will handle filtering logic.
        pass

    # Return list of dicts for saving to parquet/json
    # Using to_pandas() then to_dict('records') is standard
    try:
        import pandas as pd
        df = dataset.to_pandas()
        # Ensure required columns are strings if they aren't (for safety)
        for col in REQUIRED_FIELDS:
            if not pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].astype(str)
        
        # Add source dataset identifier
        df['source_dataset'] = 'persona_chat'
        
        records = df.to_dict('records')
        logger.info(f"Preprocessed {len(records)} records.")
        return records
    except Exception as e:
        logger.error(f"Error converting dataset to records: {e}")
        raise


def save_raw_data(records: List[Dict[str, Any]], output_dir: Path):
    """Save raw data to parquet format."""
    import pandas as pd
    logger.info(f"Saving raw data to {output_dir}...")
    
    df = pd.DataFrame(records)
    output_file = output_dir / "persona_chat_raw.parquet"
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to {output_file}")
    
    # Also save a small sample as JSON for quick inspection
    sample_file = output_dir / "sample.json"
    sample_df = df.head(10)
    sample_df.to_json(sample_file, orient="records", indent=2)
    logger.info(f"Saved sample to {sample_file}")


def generate_checksums_and_manifest(data_dir: Path):
    """Generate checksums and manifest for the downloaded data."""
    logger.info("Generating checksums and manifest...")
    
    manifest_path = data_dir / "manifest.json"
    checksum = compute_directory_checksum(data_dir)
    
    manifest = {
        "dataset": DATASET_NAME,
        "source": f"hf://datasets/{DATASET_NAME}",
        "checksum": checksum,
        "files": [],
        "download_timestamp": str(Path(__file__).stat().st_mtime) # Approximate
    }
    
    # List files in the directory
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            file_info = {
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
                "checksum": compute_directory_checksum(file_path) # Simplified for single file
            }
            manifest["files"].append(file_info)
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to {manifest_path}")


def save_validation_report(data_dir: Path, quality_field: Optional[str], missing_fields: List[str]):
    """Save a validation report detailing what was found."""
    report = {
        "dataset": DATASET_NAME,
        "status": "success" if not missing_fields else "partial",
        "required_fields_present": len(missing_fields) == 0,
        "missing_required_fields": missing_fields,
        "quality_field_found": quality_field,
        "total_rows_processed": len(list(data_dir.glob("*.parquet"))[0].read_parquet()) if list(data_dir.glob("*.parquet")) else 0 # Placeholder, actual count in main
    }
    
    # Actually get row count from the saved file if possible
    try:
        import pandas as pd
        parquet_files = list(data_dir.glob("*.parquet"))
        if parquet_files:
            df = pd.read_parquet(parquet_files[0])
            report["total_rows_processed"] = len(df)
    except Exception as e:
        logger.warning(f"Could not determine row count for report: {e}")

    report_path = data_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {report_path}")


def main():
    """Main execution function."""
    logger.info("Starting Persona-Chat dataset download (Task T015b)...")
    
    ensure_directories()
    
    try:
        # 1. Load
        ds = load_dataset_with_check(DATASET_NAME)
        
        # 2. Validate and Preprocess
        records = validate_and_preprocess(ds)
        
        # 3. Save Raw Data
        save_raw_data(records, DATA_RAW_DIR)
        
        # 4. Generate Checksums
        generate_checksums_and_manifest(DATA_RAW_DIR)
        
        # 5. Generate Validation Report
        # Re-check fields for report
        import pandas as pd
        df = pd.read_parquet(DATA_RAW_DIR / "persona_chat_raw.parquet")
        cols = df.columns.tolist()
        missing = [f for f in REQUIRED_FIELDS if f not in cols]
        quality_field = None
        for f in QUALITY_PROXY_FIELDS:
            if f in cols:
                quality_field = f
                break
        
        save_validation_report(DATA_RAW_DIR, quality_field, missing)
        
        logger.info("Persona-Chat download and validation completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()