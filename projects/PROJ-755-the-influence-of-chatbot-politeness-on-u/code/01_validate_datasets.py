"""
T016: Validate All Datasets for US1

Validates that the downloaded datasets (HCI_P2, Persona-Chat, EmpatheticDialogues)
contain the required columns: 'quality_rating', 'user_id', 'dialogue_id'.

Logic:
1. Loads the raw data files created by T015 from data/raw/{source}/raw_data.parquet.
2. Checks for the existence of required columns.
3. If 'quality_rating' is missing, logs exclusion of that source and updates
   data/raw/validation_status.json with status "excluded".
4. If ALL sources are excluded, raises a RuntimeError to abort the pipeline.
5. If at least one source is valid, updates validation_status.json with status "valid".

Dependencies: T015 (Download)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validation.log')
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['quality_rating', 'user_id', 'dialogue_id']
SOURCES = ['hci_p2', 'persona_chat', 'empathetic_dialogues']
DATA_RAW_DIR = Path('data/raw')
VALIDATION_STATUS_PATH = DATA_RAW_DIR / 'validation_status.json'

def load_validation_status() -> Dict[str, Any]:
    """Load existing validation status or initialize a new one."""
    if VALIDATION_STATUS_PATH.exists():
        with open(VALIDATION_STATUS_PATH, 'r') as f:
            return json.load(f)
    return {
        "status": "pending",
        "sources": {},
        "abort_reason": None
    }

def save_validation_status(status_data: Dict[str, Any]) -> None:
    """Save the validation status to JSON."""
    VALIDATION_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_STATUS_PATH, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Validation status saved to {VALIDATION_STATUS_PATH}")

def validate_source(source_name: str) -> Dict[str, Any]:
    """
    Validate a single source dataset.
    
    Returns a dict with:
      - status: 'valid' | 'excluded'
      - missing_columns: list of missing required columns
      - row_count: number of rows (if valid)
      - error: error message if loading failed
    """
    raw_data_path = DATA_RAW_DIR / source_name / 'raw_data.parquet'
    
    if not raw_data_path.exists():
        logger.warning(f"Raw data file not found for {source_name}: {raw_data_path}")
        return {
            "status": "excluded",
            "missing_columns": REQUIRED_COLUMNS,
            "row_count": 0,
            "error": "Raw data file not found"
        }

    try:
        df = pd.read_parquet(raw_data_path)
    except Exception as e:
        logger.error(f"Failed to load parquet for {source_name}: {e}")
        return {
            "status": "excluded",
            "missing_columns": REQUIRED_COLUMNS,
            "row_count": 0,
            "error": str(e)
        }

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_cols:
        logger.warning(f"Source {source_name} is missing required columns: {missing_cols}")
        # Specifically check for quality_rating for exclusion logic
        if 'quality_rating' in missing_cols:
            logger.error(f"CRITICAL: Source {source_name} lacks 'quality_rating'. Excluding source.")
            return {
                "status": "excluded",
                "missing_columns": missing_cols,
                "row_count": len(df),
                "error": f"Missing required column(s): {missing_cols}"
            }
        else:
            # If quality_rating exists but others don't, we might still exclude or warn
            # Based on T016 spec: "If quality_rating missing, log exclusion... Do NOT attempt to derive"
            # If other columns missing, we also exclude as schema is invalid
            return {
                "status": "excluded",
                "missing_columns": missing_cols,
                "row_count": len(df),
                "error": f"Missing required column(s): {missing_cols}"
            }

    logger.info(f"Source {source_name} is valid. Rows: {len(df)}, Columns: {list(df.columns)}")
    return {
        "status": "valid",
        "missing_columns": [],
        "row_count": len(df),
        "error": None
    }

def main():
    logger.info("Starting T016: Validate All Datasets")
    
    status_data = load_validation_status()
    valid_sources_count = 0
    excluded_sources = []
    
    for source in SOURCES:
        logger.info(f"Validating source: {source}")
        result = validate_source(source)
        
        status_data["sources"][source] = {
            "status": result["status"],
            "missing_columns": result["missing_columns"],
            "row_count": result["row_count"],
            "error": result["error"]
        }
        
        if result["status"] == "valid":
            valid_sources_count += 1
        else:
            excluded_sources.append(source)
            logger.warning(f"Source {source} excluded: {result['error']}")

    # Check abort condition
    if valid_sources_count == 0:
        error_msg = "NO_VALID_DATA_SOURCE: All sources (HCI_P2, Persona-Chat, EmpatheticDialogues) are excluded or failed to load."
        logger.critical(error_msg)
        status_data["status"] = "aborted"
        status_data["abort_reason"] = error_msg
        save_validation_status(status_data)
        raise RuntimeError(error_msg)
    
    # If we reach here, at least one source is valid
    status_data["status"] = "valid"
    status_data["valid_sources_count"] = valid_sources_count
    status_data["excluded_sources"] = excluded_sources
    
    logger.info(f"Validation complete. {valid_sources_count} valid source(s).")
    logger.info(f"Excluded sources: {excluded_sources}")
    
    save_validation_status(status_data)
    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    main()