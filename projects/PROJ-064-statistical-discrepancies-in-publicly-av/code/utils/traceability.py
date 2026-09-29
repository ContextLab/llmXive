"""
Traceability Map Generator

This module implements the generation of `traceability_map.json` to link
output metrics to source data rows, satisfying the reproducibility and
audit requirements of the project.

Schema requirements:
- metric_id: Unique identifier for the metric/row
- source_file: Path to the source data file
- source_row: Original row index or identifier in the source
- code_block: Identifier of the code block/function that generated the metric
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from ..logger import get_logger
from ..exceptions import ConfigurationError, ReproducibilityError

logger = get_logger(__name__)


def load_processed_data(processed_path: str) -> pd.DataFrame:
    """
    Load the processed discrepancy data from the specified path.

    Args:
        processed_path: Path to the processed CSV/JSON file.

    Returns:
        DataFrame containing processed metrics.

    Raises:
        ConfigurationError: If the file does not exist or cannot be read.
    """
    path = Path(processed_path)
    if not path.exists():
        raise ConfigurationError(f"Processed data file not found: {path}")

    logger.info(f"Loading processed data from {path}")
    
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        df = pd.read_json(path)
    else:
        raise ConfigurationError(f"Unsupported file format: {path.suffix}")

    if df.empty:
        raise ReproducibilityError("Processed data is empty. Ensure the pipeline ran successfully.")
    
    return df


def load_source_metadata(raw_data_dir: str) -> Dict[str, Any]:
    """
    Load metadata about source files to map back to original rows.
    
    This function scans the raw data directory to establish a mapping
    between source files and their content hashes/identifiers.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        Dictionary mapping filenames to metadata (hash, row count, etc.).
    """
    raw_path = Path(raw_data_dir)
    if not raw_path.exists():
        logger.warning(f"Raw data directory not found: {raw_path}. Traceability may be incomplete.")
        return {}

    metadata = {}
    for file in raw_path.iterdir():
        if file.suffix in ['.csv', '.json']:
            # Compute a hash of the file to ensure we are tracking the exact version
            with open(file, 'rb') as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
            
            metadata[file.name] = {
                'hash': content_hash,
                'path': str(file),
                'size': file.stat().st_size
            }
    
    return metadata


def map_metrics_to_sources(
    processed_df: pd.DataFrame,
    source_metadata: Dict[str, Any],
    code_block_id: str = "T017_discrepancy_calc"
) -> List[Dict[str, Any]]:
    """
    Map processed metrics back to their source rows.

    This function attempts to reconstruct the lineage of each metric in the
    processed DataFrame by linking it to the source file and row.

    Args:
        processed_df: DataFrame of processed metrics.
        source_metadata: Metadata about source files.
        code_block_id: Identifier for the code block that generated the metrics.

    Returns:
        List of dictionaries representing the traceability entries.
    """
    traceability_entries = []
    
    # Determine the source file based on the 'source_file' column if present,
    # or default to the first available raw file if not.
    source_file_col = 'source_file' if 'source_file' in processed_df.columns else None
    
    # If no source_file column, we assume a single source or need to infer
    # For robustness, we will try to infer from context or use a generic mapping
    
    for idx, row in processed_df.iterrows():
        entry = {
            "metric_id": f"metric_{idx}_{hash(str(row))[:8]}",
            "source_file": "unknown" if not source_file_col else str(row.get(source_file_col, "unknown")),
            "source_row": str(row.get('source_row_id', idx)),
            "code_block": code_block_id,
            "metrics_snapshot": {
                k: v for k, v in row.items() 
                if k in ['precinct_sum', 'county_reported', 'discrepancy_abs', 'discrepancy_pct', 'missing_data']
            }
        }
    
        # Fallback for source_file if not in row but in metadata
        if entry["source_file"] == "unknown" and source_metadata:
            # In a real scenario, we would have a join key. Here we assume 
            # the first file if no specific mapping exists, but log a warning.
            if len(source_metadata) == 1:
                entry["source_file"] = list(source_metadata.keys())[0]
            else:
                logger.warning(f"Row {idx} has no source_file and multiple raw files exist. Mapping ambiguous.")
        
        traceability_entries.append(entry)

    return traceability_entries


def generate_traceability_map(
    processed_path: str,
    raw_data_dir: str,
    output_path: str,
    code_block_id: str = "T017_discrepancy_calc"
) -> None:
    """
    Main entry point to generate the traceability map.

    This function orchestrates the loading of data, metadata, and the generation
    of the final JSON artifact.

    Args:
        processed_path: Path to the processed data file.
        raw_data_dir: Path to the raw data directory.
        output_path: Path where the traceability_map.json will be written.
        code_block_id: Identifier for the code block generating the metrics.
    """
    logger.info(f"Generating traceability map: {output_path}")
    
    # Load data
    df = load_processed_data(processed_path)
    metadata = load_source_metadata(raw_data_dir)
    
    # Map metrics
    traceability_entries = map_metrics_to_sources(df, metadata, code_block_id)
    
    # Construct final structure
    traceability_map = {
        "version": "1.0",
        "generated_at": pd.Timestamp.now().isoformat(),
        "code_block_reference": code_block_id,
        "total_records": len(traceability_entries),
        "entries": traceability_entries
    }

    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to disk
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(traceability_map, f, indent=2, default=str)
    
    logger.info(f"Traceability map successfully written to {output_path}")


def main() -> None:
    """
    CLI entry point for the traceability map generator.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate traceability map for processed election data.")
    parser.add_argument(
        "--processed", 
        type=str, 
        default="data/processed/discrepancies.csv",
        help="Path to the processed discrepancy data file."
    )
    parser.add_argument(
        "--raw", 
        type=str, 
        default="data/raw",
        help="Path to the raw data directory."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/traceability_map.json",
        help="Path for the output traceability map JSON file."
    )
    parser.add_argument(
        "--code-block", 
        type=str, 
        default="T017_discrepancy_calc",
        help="Identifier for the code block generating the metrics."
    )

    args = parser.parse_args()

    try:
        generate_traceability_map(
            processed_path=args.processed,
            raw_data_dir=args.raw,
            output_path=args.output,
            code_block_id=args.code_block
        )
    except Exception as e:
        logger.error(f"Failed to generate traceability map: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()