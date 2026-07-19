import csv
import gzip
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from src.utils.logging import get_logger, setup_logger
from src.utils.state_manager import register_artifact, update_stage_status
from src.modeling.config import load_config
from src.data.schemas import ReactionRecord, validate_reaction_record
from src.utils.chemistry import classify_batch, get_templates

# Ensure the logger is set up before any logging calls
logger = get_logger(__name__)

# Constants
USPTO_ZENODO_URL = "https://zenodo.org/record/3969375/files/uspto_mit_subset.jsonl.gz"
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
ERROR_LOG_FILE = "data/raw/malformed_smiles.log"
FILTERED_OUTPUT_FILE = "data/processed/filtered_reactions.csv"
CHECKSUM_FILE = "data/processed/filtered_reactions.csv.sha256"
PROVENANCE_FILE = "data/processed/filtered_reactions_provenance.json"

def download_uspto_data() -> Path:
    """
    Downloads the USPTO-MIT subset from Zenodo.
    Returns the path to the downloaded file.
    """
    import requests
    
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DATA_DIR / "uspto_mit_subset.jsonl.gz"

    if output_path.exists():
        logger.info(f"File {output_path} already exists. Skipping download.")
        return output_path

    logger.info(f"Downloading USPTO data from {USPTO_ZENODO_URL}...")
    try:
        response = requests.get(USPTO_ZENODO_URL, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Download complete: {output_path}")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise

def stream_jsonl_gz(file_path: Path):
    """
    Generator that yields parsed JSON objects from a gzipped JSONL file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {line_num}: {e}")
                continue

def parse_jsonl_line(data: Dict[str, Any]) -> Optional[ReactionRecord]:
    """
    Parses a raw JSON line into a ReactionRecord.
    Returns None if the record is invalid.
    """
    # Basic validation: ensure required fields exist
    if 'rxn_smiles' not in data:
        return None
    
    # Construct ReactionRecord
    # Assuming 'rxn_smiles' is the reaction SMILES string
    # We might need to extract reactants/products if the format is complex,
    # but for now we treat the whole string as the reaction.
    try:
        record = ReactionRecord(
            reaction_smiles=data.get('rxn_smiles', ''),
            reaction_type=None, # To be filled by classifier
            yield_pct=data.get('yield_pct'),
            success_flag=data.get('success_flag'),
            raw_data=data
        )
        return record
    except Exception as e:
        logger.warning(f"Error parsing record: {e}")
        return None

def process_chunk(chunk: List[Dict[str, Any]], config: Dict[str, Any]) -> pd.DataFrame:
    """
    Processes a chunk of raw data: classifies reactions, filters, and derives target.
    """
    templates = get_templates(config)
    
    processed_records = []
    malformed_count = 0

    for item in chunk:
        record = parse_jsonl_line(item)
        if record is None:
            malformed_count += 1
            continue

        # Classify reaction
        rxn_smiles = record.reaction_smiles
        classification = classify_reaction(rxn_smiles, templates)
        
        if classification is None:
            # Log malformed or non-matching SMILES
            with open(ERROR_LOG_FILE, 'a') as f:
                f.write(f"{rxn_smiles}\n")
            malformed_count += 1
            continue

        record.reaction_type = classification
        processed_records.append(record)

    if processed_records:
        df = pd.DataFrame([r.__dict__ for r in processed_records])
        # Derive target variable strictly as per spec
        # Use yield_pct if present, else success_flag (binary)
        if 'yield_pct' in df.columns and df['yield_pct'].notna().any():
            df['target'] = df['yield_pct'].fillna(0) # Assuming 0 yield for missing if needed, or drop
        else:
            # Convert success_flag to numeric if it exists
            if 'success_flag' in df.columns:
                df['target'] = df['success_flag'].astype(int)
            else:
                # If neither exists, we cannot proceed for regression/classification
                # Raise error or drop rows
                logger.error("No target variable (yield_pct or success_flag) found in data.")
                return pd.DataFrame()

        return df
    
    return pd.DataFrame()

def filter_by_class_sample_size(df: pd.DataFrame, min_samples: int = 1000) -> pd.DataFrame:
    """
    Filters the dataframe to keep only reaction types with >= min_samples rows.
    Logs warnings for removed classes.
    """
    if df.empty:
        return df

    counts = df['reaction_type'].value_counts()
    valid_types = counts[counts >= min_samples].index.tolist()
    
    removed_types = set(df['reaction_type'].unique()) - set(valid_types)
    for rt in removed_types:
        logger.warning(f"Removing class '{rt}' due to insufficient samples ({counts[rt]} < {min_samples}).")
    
    filtered_df = df[df['reaction_type'].isin(valid_types)]
    logger.info(f"Filtered dataset: {len(filtered_df)} rows remaining from {len(df)}.")
    return filtered_df

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_provenance(file_path: Path, checksum: str, config: Dict[str, Any], stats: Dict[str, Any]):
    """
    Saves provenance metadata for the filtered dataset.
    """
    provenance = {
        "file_path": str(file_path),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat(),
        "source_url": USPTO_ZENODO_URL,
        "config_used": {
            "templates": config.get('reaction_templates', {}),
            "min_samples": stats.get('min_samples', 1000)
        },
        "statistics": stats
    }
    
    with open(PROVENANCE_FILE, 'w') as f:
        json.dump(provenance, f, indent=2)
    logger.info(f"Provenance saved to {PROVENANCE_FILE}")

def ingest_and_filter(config_path: Optional[str] = None):
    """
    Main orchestration function for data ingestion and filtering.
    """
    setup_logger()
    
    # Load config
    config = load_config(config_path)
    
    # Download data
    data_path = download_uspto_data()
    
    # Process in chunks to handle memory limits
    chunk_size = 10000
    all_dataframes = []
    total_rows = 0
    
    logger.info("Starting batch processing...")
    start_time = time.time()
    
    # Stream and process
    buffer = []
    for item in stream_jsonl_gz(data_path):
        buffer.append(item)
        if len(buffer) >= chunk_size:
            df_chunk = process_chunk(buffer, config)
            if not df_chunk.empty:
                all_dataframes.append(df_chunk)
                total_rows += len(df_chunk)
            buffer = []
    
    # Process remaining
    if buffer:
        df_chunk = process_chunk(buffer, config)
        if not df_chunk.empty:
            all_dataframes.append(df_chunk)
            total_rows += len(df_chunk)
    
    if not all_dataframes:
        logger.error("No valid data processed. Exiting.")
        return

    # Concatenate all chunks
    full_df = pd.concat(all_dataframes, ignore_index=True)
    logger.info(f"Total raw processed rows: {len(full_df)}")
    
    # Apply sample size filter (T016 logic)
    min_samples = config.get('min_samples_per_class', 1000)
    filtered_df = filter_by_class_sample_size(full_df, min_samples)
    
    if filtered_df.empty:
        logger.error("No data remaining after filtering by class sample size.")
        return

    # Ensure output directory exists
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    filtered_df.to_csv(FILTERED_OUTPUT_FILE, index=False)
    logger.info(f"Filtered dataset saved to {FILTERED_OUTPUT_FILE}")
    
    # Compute checksum
    checksum = compute_file_checksum(Path(FILTERED_OUTPUT_FILE))
    with open(CHECKSUM_FILE, 'w') as f:
        f.write(checksum)
    logger.info(f"Checksum computed and saved: {checksum}")
    
    # Save provenance
    stats = {
        "total_input_rows": total_rows,
        "final_rows": len(filtered_df),
        "class_counts": filtered_df['reaction_type'].value_counts().to_dict(),
        "min_samples_threshold": min_samples
    }
    save_provenance(Path(FILTERED_OUTPUT_FILE), checksum, config, stats)
    
    # Update state
    register_artifact("filtered_reactions", FILTERED_OUTPUT_FILE, checksum)
    update_stage_status("US1", "completed", artifacts=[FILTERED_OUTPUT_FILE])
    
    end_time = time.time()
    logger.info(f"Ingestion and filtering completed in {end_time - start_time:.2f} seconds.")

def main():
    """
    Entry point for the script.
    """
    ingest_and_filter()

if __name__ == "__main__":
    main()
