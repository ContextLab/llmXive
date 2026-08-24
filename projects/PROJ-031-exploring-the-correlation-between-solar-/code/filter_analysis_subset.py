"""
Module to filter non-recurrent storms from the aligned dataset.

This module implements T016b: Filter non-recurrent storms to create
a derived analysis subset for statistical modeling.

Dependencies:
    - code/align.py (load_aligned_events, write_aligned_events)
    - data/processed/aligned_events.csv (input)
    - data/processed/analysis_subset.csv (output)
    - data/source_manifest.yaml (update)
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from sibling module align.py as per API surface
from align import load_aligned_events, write_aligned_events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories(output_path: Path) -> None:
    """Ensure the directory for the output file exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def filter_non_recurrent_storms(df: Any) -> Any:
    """
    Filter the DataFrame to retain only non-recurrent storms.
    
    This implements the logic for T016b:
    - Reads the `is_recurrent` flag (added in T016).
    - Keeps rows where `is_recurrent` is False or missing (treating missing as non-recurrent).
    - Drops rows where `is_recurrent` is explicitly True.
    
    Args:
        df: pandas DataFrame containing aligned events with `is_recurrent` column.
        
    Returns:
        Filtered pandas DataFrame.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    # Ensure the column exists; if not, assume all are non-recurrent
    if 'is_recurrent' not in df.columns:
        logger.warning("Column 'is_recurrent' not found. Assuming all events are non-recurrent.")
        return df.copy()

    # Filter: Keep rows where is_recurrent is False or NaN.
    # We drop rows where is_recurrent is True.
    # Note: In pandas, boolean indexing with NaN usually keeps the row if we use ~ (not).
    # We want to keep if NOT (is_recurrent == True).
    # So: mask = ~ (df['is_recurrent'] == True)
    # This keeps False and NaN.
    mask = ~ (df['is_recurrent'] == True)
    filtered_df = df[mask].copy()
    
    logger.info(f"Filtered dataset: {len(df)} -> {len(filtered_df)} rows.")
    recurrent_count = (df['is_recurrent'] == True).sum()
    logger.info(f"Removed {recurrent_count} recurrent events.")
    
    return filtered_df

def write_subset(filtered_df: Any, output_path: Path) -> None:
    """
    Write the filtered DataFrame to CSV.
    
    Args:
        filtered_df: Filtered pandas DataFrame.
        output_path: Path to write the CSV file.
    """
    ensure_directories(output_path)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Wrote analysis subset to {output_path}")

def update_manifest(manifest_path: Path, output_path: Path) -> None:
    """
    Update the source manifest with the new derived file info.
    
    Args:
        manifest_path: Path to source_manifest.yaml.
        output_path: Path to the newly created analysis_subset.csv.
    """
    import yaml
    
    if not manifest_path.exists():
        logger.warning(f"Manifest file not found at {manifest_path}. Skipping update.")
        return

    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f) or {}

    # Calculate a simple checksum or just record the file
    import hashlib
    with open(output_path, 'rb') as f:
        content = f.read()
        checksum = hashlib.sha256(content).hexdigest()

    manifest['analysis_subset'] = {
        'path': str(output_path),
        'checksum': checksum,
        'created_at': str(__import__('datetime').datetime.now().isoformat()),
        'description': 'Filtered dataset containing only non-recurrent storms for analysis.'
    }

    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    
    logger.info(f"Updated manifest at {manifest_path}")

def main(args: Optional[List[str]] = None) -> None:
    """
    Main entry point for the filter script.
    
    Usage:
        python code/filter_analysis_subset.py --input data/processed/aligned_events.csv --output data/processed/analysis_subset.csv
    """
    parser = argparse.ArgumentParser(description="Filter non-recurrent storms from aligned events.")
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/processed/aligned_events.csv',
        help='Path to the input aligned events CSV.'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/processed/analysis_subset.csv',
        help='Path to the output analysis subset CSV.'
    )
    parser.add_argument(
        '--manifest', '-m',
        type=str,
        default='data/source_manifest.yaml',
        help='Path to the source manifest YAML.'
    )
    
    parsed_args = parser.parse_args(args)
    
    input_path = Path(parsed_args.input)
    output_path = Path(parsed_args.output)
    manifest_path = Path(parsed_args.manifest)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading aligned events from {input_path}...")
    df = load_aligned_events(input_path)

    logger.info("Filtering non-recurrent storms...")
    filtered_df = filter_non_recurrent_storms(df)

    logger.info(f"Writing subset to {output_path}...")
    write_subset(filtered_df, output_path)

    logger.info("Updating manifest...")
    update_manifest(manifest_path, output_path)

    logger.info("Task T016b completed successfully.")

if __name__ == '__main__':
    main()
