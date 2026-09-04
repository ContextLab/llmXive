"""
Real VR Log Parsing Module (Phase 6 / T041).

Parses raw VR interaction logs into the standardized format required by the pipeline.
Strictly fails if the source files are missing or malformed.
"""
from __future__ import annotations

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Import interface constants
try:
    from data.ingest_real import VR_LOG_SCHEMA_COLUMNS
except ImportError:
    raise ImportError(
        "Real log parsing requires the interface constants from data.ingest_real (T050)."
    )

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SchemaError(Exception):
    """Custom exception for schema validation errors."""
    pass

def parse_vr_logs_from_csv(input_path: str, output_path: Optional[str] = None) -> Path:
    """
    Parse VR logs from a CSV file into the standardized schema.
    
    Args:
        input_path: Path to the raw VR logs CSV.
        output_path: Path to save the parsed CSV.
    
    Returns:
        Path to the parsed file.
    
    Raises:
        FileNotFoundError: If input file is missing.
        SchemaError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"VR log source file not found: {input_path}")
    
    logger.info(f"Parsing VR logs from {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise SchemaError(f"Failed to read CSV: {str(e)}") from e
    
    # Validate schema
    missing_cols = [col for col in VR_LOG_SCHEMA_COLUMNS if col not in df.columns]
    if missing_cols:
        raise SchemaError(f"Missing required columns in VR logs: {missing_cols}")
    
    # Ensure output path
    if output_path is None:
        output_path = os.path.join("data", "processed", "parsed_vr_logs.csv")
    
    full_output = Path(output_path)
    full_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Standardize column names (lowercase, strip spaces)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Save
    df.to_csv(full_output, index=False)
    logger.info(f"Parsed VR logs saved to {full_output}")
    
    return full_output

def parse_vr_logs_from_json(input_path: str, output_path: Optional[str] = None) -> Path:
    """
    Parse VR logs from a JSON file into the standardized schema.
    
    Args:
        input_path: Path to the raw VR logs JSON.
        output_path: Path to save the parsed CSV.
    
    Returns:
        Path to the parsed file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"VR log source file not found: {input_path}")
    
    logger.info(f"Parsing VR logs from JSON: {input_path}")
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        raise SchemaError(f"Failed to read JSON: {str(e)}") from e
    
    # Normalize to list of dicts if nested
    if isinstance(data, dict):
        if 'logs' in data:
            data = data['logs']
        elif 'records' in data:
            data = data['records']
        else:
            data = [data]
    
    df = pd.DataFrame(data)
    
    # Validate schema
    missing_cols = [col for col in VR_LOG_SCHEMA_COLUMNS if col not in df.columns]
    if missing_cols:
        raise SchemaError(f"Missing required columns in VR logs (from JSON): {missing_cols}")
    
    if output_path is None:
        output_path = os.path.join("data", "processed", "parsed_vr_logs.csv")
    
    full_output = Path(output_path)
    full_output.parent.mkdir(parents=True, exist_ok=True)
    
    df.columns = [str(c).strip().lower() for c in df.columns]
    df.to_csv(full_output, index=False)
    
    logger.info(f"Parsed VR logs saved to {full_output}")
    return full_output

def main():
    """Main entry point for parsing real logs."""
    from code.config import validate_data_mode, get_path
    
    try:
        validate_data_mode()
    except (ValueError, ImportError) as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    if os.getenv('DATA_MODE') != 'real':
        logger.warning("DATA_MODE is not set to 'real'. Skipping real log parsing.")
        sys.exit(0)
    
    # Example usage - in a real pipeline, paths would come from config or CLI
    # This is a placeholder for the actual integration point
    logger.info("Real log parsing module loaded. Ready to parse from data/raw/*.csv or *.json")
    sys.exit(0)

if __name__ == "__main__":
    main()
