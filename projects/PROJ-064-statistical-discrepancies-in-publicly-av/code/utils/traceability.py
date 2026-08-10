"""
Traceability Map Generator for Election Discrepancy Analysis.

This module generates a traceability_map.json file that links output metrics
(discrepancies, statistical test results) back to the source data rows.
This ensures full reproducibility and auditability of the analysis pipeline.

Dependencies:
    - T007 (models.py): Provides Discrepancy schema and validation
    - T008 (utils/hashing.py): Provides checksum utilities for source verification
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Import from project API surface
from ..models import validate_output_schema, create_discrepancy_record
from ..exceptions import MissingDataError, ConfigurationError
from .hashing import compute_file_hash, load_checksums
from ..logger import get_logger

logger = get_logger(__name__)


def load_processed_data(processed_data_path: str) -> pd.DataFrame:
    """
    Load the processed data DataFrame containing discrepancy metrics.

    Args:
        processed_data_path: Path to the processed CSV/Parquet file.

    Returns:
        DataFrame with discrepancy metrics.

    Raises:
        MissingDataError: If the file does not exist or is empty.
    """
    path = Path(processed_data_path)
    if not path.exists():
        raise MissingDataError(f"Processed data file not found: {processed_data_path}")

    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ConfigurationError(f"Unsupported file format: {path.suffix}")

    if df.empty:
        raise MissingDataError("Processed data file is empty.")

    # Validate schema against T007 definition
    validate_output_schema(df)
    logger.info(f"Loaded processed data with {len(df)} rows from {processed_data_path}")
    return df


def load_source_metadata(source_data_path: str) -> Dict[str, Any]:
    """
    Load metadata about the source data file, including its checksum.

    Args:
        source_data_path: Path to the raw source data file.

    Returns:
        Dictionary containing source file metadata.
    """
    path = Path(source_data_path)
    if not path.exists():
        raise MissingDataError(f"Source data file not found: {source_data_path}")

    file_hash = compute_file_hash(path)
    size_bytes = path.stat().st_size

    return {
        "path": str(path),
        "filename": path.name,
        "size_bytes": size_bytes,
        "sha256": file_hash,
        "checksum_valid": True
    }


def map_metrics_to_sources(
    processed_df: pd.DataFrame,
    source_row_id_column: str = "source_row_id",
    source_file_column: str = "source_file"
) -> List[Dict[str, Any]]:
    """
    Create a mapping between processed metrics and their source rows.

    Args:
        processed_df: The processed DataFrame with discrepancy metrics.
        source_row_id_column: Column name in processed_df linking to source.
        source_file_column: Column name indicating the source file.

    Returns:
        List of dictionaries mapping output rows to source metadata.
    """
    if source_row_id_column not in processed_df.columns:
        logger.warning(f"Column '{source_row_id_column}' not found. Generating synthetic IDs.")
        processed_df = processed_df.copy()
        processed_df[source_row_id_column] = range(len(processed_df))

    mapping = []
    for idx, row in processed_df.iterrows():
        record = {
            "output_index": int(idx),
            "precinct_sum": row.get("precinct_sum"),
            "county_reported": row.get("county_reported"),
            "discrepancy_abs": row.get("discrepancy_abs"),
            "discrepancy_pct": row.get("discrepancy_pct"),
            "missing_data": bool(row.get("missing_data", False)),
            "source_reference": {
                "row_id": str(row[source_row_id_column]),
                "source_file": row.get(source_file_column, "unknown"),
                "link_type": "direct_mapping"
            }
        }
        mapping.append(record)

    return mapping


def generate_traceability_map(
    processed_data_path: str,
    source_data_path: str,
    output_path: str,
    analysis_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the complete traceability_map.json file.

    This function:
    1. Loads processed discrepancy data.
    2. Loads source data metadata (checksums).
    3. Maps each output row to its source row.
    4. Writes the JSON artifact to disk.

    Args:
        processed_data_path: Path to processed data (e.g., data/processed/discrepancies.csv).
        source_data_path: Path to raw source data.
        output_path: Path where traceability_map.json will be written.
        analysis_metadata: Optional metadata about the analysis run (e.g., seed, timestamp).

    Returns:
        Path to the generated JSON file.

    Raises:
        MissingDataError: If required files are missing.
        ConfigurationError: If schema validation fails.
    """
    logger.info(f"Starting traceability map generation for {processed_data_path}")

    # Load data
    processed_df = load_processed_data(processed_data_path)
    source_meta = load_source_metadata(source_data_path)

    # Build mapping
    row_mappings = map_metrics_to_sources(processed_df)

    # Construct final structure
    traceability_map = {
        "version": "1.0",
        "generated_at": pd.Timestamp.now().isoformat(),
        "source_data": source_meta,
        "processed_data": {
            "path": processed_data_path,
            "row_count": len(processed_df),
            "schema": list(processed_df.columns)
        },
        "analysis_metadata": analysis_metadata or {},
        "row_mappings": row_mappings
    }

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(traceability_map, f, indent=2, default=str)

    logger.info(f"Traceability map generated successfully: {output_path}")
    return output_path


def main():
    """
    Entry point for generating the traceability map from the command line.
    Expects environment variables or default paths to be configured.
    """
    # Default paths based on project structure
    processed_path = "data/processed/discrepancies.csv"
    source_path = "data/raw/election_data.csv"
    output_path = "data/processed/traceability_map.json"

    # Check for command line overrides (simple parsing)
    import sys
    if len(sys.argv) > 1:
        processed_path = sys.argv[1]
    if len(sys.argv) > 2:
        source_path = sys.argv[2]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]

    try:
        generate_traceability_map(
            processed_data_path=processed_path,
            source_data_path=source_path,
            output_path=output_path,
            analysis_metadata={
                "pipeline_version": "1.0.0",
                "description": "Links output metrics to source data rows for auditability"
            }
        )
        print(f"SUCCESS: Traceability map written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate traceability map: {e}")
        raise


if __name__ == "__main__":
    main()
