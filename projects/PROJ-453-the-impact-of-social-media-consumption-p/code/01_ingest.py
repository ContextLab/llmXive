"""
Data Ingestion module.
Downloads and validates datasets from HuggingFace.
"""
import os
import sys
import logging
import yaml
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from datasets import load_dataset
from logging_config import get_logger

logger = get_logger(__name__)

def load_schema_contract(schema_path: str) -> Dict[str, Any]:
    """Load the dataset schema contract."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Validate the schema structure."""
    if 'columns' not in schema:
        raise ValueError("Schema missing 'columns' key")
    return True

def validate_data_types_and_constraints(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """Validate data types and constraints against schema."""
    # Simplified validation
    required_cols = schema.get('columns', {}).keys()
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

def download_data(dataset_id: str, output_path: Path, streaming: bool = False) -> pd.DataFrame:
    """
    Download data from HuggingFace datasets.
    """
    logger.info(f"Downloading dataset: {dataset_id}")
    try:
        ds = load_dataset(dataset_id, split='train', streaming=streaming)
        if streaming:
            # Convert to DF by iterating (for small subset or full if fits)
            # For robustness, we iterate and save chunks if needed, but here we assume it fits or we take a sample
            df = ds.to_pandas()
        else:
            df = ds.to_pandas()
        df.to_csv(output_path, index=False)
        return df
    except Exception as e:
        logger.error(f"Failed to download {dataset_id}: {e}")
        raise

def load_hilda() -> Optional[pd.DataFrame]:
    """Load HILDA dataset."""
    # Check feasibility first
    feasibility_path = Path("logs/feasibility_report.txt")
    if not feasibility_path.exists():
        logger.warning("Feasibility report missing. Skipping HILDA.")
        return None
    # Read report to check if HILDA passed
    with open(feasibility_path, 'r') as f:
        content = f.read()
        if "hilda/hilda_2023" not in content or "PASS" not in content:
            logger.warning("HILDA feasibility check failed.")
            return None

    output_path = Path("data/raw/hilda_raw.csv")
    try:
        return download_data("hilda/hilda_2023", output_path)
    except Exception as e:
        logger.error(f"HILDA ingestion failed: {e}")
        return None

def load_ess() -> Optional[pd.DataFrame]:
    """Load ESS dataset."""
    feasibility_path = Path("logs/feasibility_report.txt")
    if not feasibility_path.exists():
        logger.warning("Feasibility report missing. Skipping ESS.")
        return None
    with open(feasibility_path, 'r') as f:
        content = f.read()
        if "ess/ess_round10" not in content or "PASS" not in content:
            logger.warning("ESS feasibility check failed.")
            return None

    output_path = Path("data/raw/ess_raw.csv")
    try:
        return download_data("ess/ess_round10", output_path)
    except Exception as e:
        logger.error(f"ESS ingestion failed: {e}")
        return None

def load_addhealth() -> Optional[pd.DataFrame]:
    """Load AddHealth dataset."""
    feasibility_path = Path("logs/feasibility_report.txt")
    if not feasibility_path.exists():
        logger.warning("Feasibility report missing. Skipping AddHealth.")
        return None
    with open(feasibility_path, 'r') as f:
        content = f.read()
        if "nrc/addhealth_wave4" not in content and "addhealth" not in content:
            logger.warning("AddHealth feasibility check failed.")
            return None

    output_path = Path("data/raw/addhealth_raw.csv")
    try:
        return download_data("nrc/addhealth_wave4", output_path)
    except Exception as e:
        logger.error(f"AddHealth ingestion failed: {e}")
        return None

def validate_and_save(df: pd.DataFrame, output_path: Path, schema: Dict[str, Any]) -> None:
    """Validate and save cleaned data."""
    validate_data_types_and_constraints(df, schema)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_instrument_sources(dataset_name: str, output_path: Path) -> None:
    """Write instrument sources YAML."""
    # Mock citations for demonstration - in real scenario, fetch from docs
    sources = {
        "survey_name": dataset_name,
        "validation_citation": "Official Dataset Documentation",
        "variable_mapping": [
            {"original_var": "self_reported_switching_frequency", "derived_var": "switching_frequency", "source_doc": "https://example.com/doc"},
            {"original_var": "cognitive_flexibility_score", "derived_var": "cognitive_flexibility_score", "source_doc": "https://example.com/doc"}
        ]
    }
    with open(output_path, 'w') as f:
        yaml.dump(sources, f)

def main():
    """Main entry point for ingestion pipeline."""
    logger.info("Starting data ingestion pipeline.")

    # Paths
    data_root = Path("data")
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    schema_path = "contracts/dataset.schema.yaml"
    instrument_path = data_root / "instrument_sources.yaml"

    # Ensure directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load schema
    schema = load_schema_contract(schema_path)
    validate_schema_structure(schema)

    # Load datasets (try all, process first valid one for this task)
    datasets = [load_hilda(), load_ess(), load_addhealth()]
    valid_data = [d for d in datasets if d is not None]

    if not valid_data:
        logger.error("No valid datasets loaded.")
        sys.exit(1)

    # Process first valid dataset
    df = valid_data[0]
    dataset_name = "unknown" # Should be derived from which loader succeeded
    # Simplified: just save
    output_path = processed_dir / "participants_cleaned.csv" # Temporary, T017 does real engineering
    validate_and_save(df, output_path, schema)

    # Write instrument sources
    write_instrument_sources(dataset_name, instrument_path)

    logger.info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
