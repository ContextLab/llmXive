from __future__ import annotations

import csv
import gzip
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdChemReactions

from src.modeling.config import load_config
from src.utils.chemistry import classify_reaction, get_templates
from src.utils.logging import get_logger, log_operation, setup_logger
from src.utils.state_manager import register_artifact, update_stage_status

# ---------------------------------------------------------------------
# Logging Setup (Tolerant of all call shapes per contract)
# ---------------------------------------------------------------------
def setup_logger(name: Optional[str] = None) -> Any:
    """
    Setup logger tolerant of:
      - setup_logger("name")
      - setup_logger(__name__)
      - setup_logger()
    """
    try:
        if name is None:
            # Called as setup_logger() -> use default
            return get_logger()
        # Called with a string or module name
        return get_logger(name)
    except Exception:
        # Fallback to standard logging if custom logger fails
        return logging.getLogger(name if name else "ingestion")

# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------
def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_provenance(output_path: Path, source: str, checksum: str, config: Dict[str, Any]) -> None:
    """Save provenance metadata."""
    provenance = {
        "source": source,
        "checksum": checksum,
        "timestamp": datetime.utcnow().isoformat(),
        "config_snapshot": config,
    }
    with open(output_path, "w") as f:
        json.dump(provenance, f, indent=2)

# ---------------------------------------------------------------------
# Data Processing Logic
# ---------------------------------------------------------------------
def stream_jsonl_gz(file_path: Path) -> Any:
    """Stream a gzipped JSONL file line by line."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    # Check if it's a parquet file instead (common in USPTO datasets)
    if file_path.suffix == '.parquet':
        # Return a generator that yields rows from parquet
        df = pd.read_parquet(file_path)
        for _, row in df.iterrows():
            yield row.to_dict()
        return

    # Handle JSONL.gz
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield line

def parse_jsonl_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single JSONL line."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None

def process_chunk(chunk_data: List[Dict[str, Any]], templates: Dict[str, Any], logger: Any) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Process a chunk of reaction data:
    1. Classify reaction type using SMARTS
    2. Derive target variable (yield_pct or success_flag)
    3. Filter out non-matching reactions
    4. Log malformed SMILES
    """
    valid_rows = []
    errors = []
    
    for row in chunk_data:
        # Extract SMILES
        rxn_smiles = row.get('rxn_smiles') or row.get('reaction_smiles')
        if not rxn_smiles:
            errors.append({"row": row, "reason": "Missing rxn_smiles"})
            continue
        
        # Classify reaction
        reaction_type, match_info = classify_reaction(rxn_smiles, templates)
        
        if reaction_type is None:
            # No template matched, skip but don't error (unless we want strict mode)
            # For now, we filter these out as per T014 "exclude non-matching rows"
            continue
        
        # Derive target variable per FR-004
        target_source = None
        target_value = None
        
        if 'yield_pct' in row and row['yield_pct'] is not None:
            try:
                target_value = float(row['yield_pct'])
                target_source = 'yield_pct'
            except (ValueError, TypeError):
                pass
        
        if target_source is None and 'success_flag' in row:
            try:
                val = row['success_flag']
                if isinstance(val, bool):
                    target_value = 1.0 if val else 0.0
                elif isinstance(val, (int, float)):
                    target_value = float(val)
                else:
                    # Try to parse string
                    target_value = 1.0 if str(val).lower() in ['true', '1', 'yes'] else 0.0
                target_source = 'success_flag'
            except (ValueError, TypeError):
                pass
        
        if target_source is None:
            # Cannot derive target, log and skip
            errors.append({
                "row_id": row.get('id', 'unknown'),
                "reason": "Missing yield_pct and success_flag",
                "smiles": rxn_smiles
            })
            continue
        
        valid_rows.append({
            "reaction_smiles": rxn_smiles,
            "reaction_type": reaction_type,
            "target_source": target_source,
            "target_value": target_value,
            "original_row": row
        })
    
    return pd.DataFrame(valid_rows), errors

def filter_by_class_sample_size(df: pd.DataFrame, min_samples: int = 1000) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter dataset to exclude classes with < min_samples.
    Returns filtered DF and metadata about excluded classes.
    """
    if df.empty:
        return df, {"excluded_classes": []}
    
    class_counts = df['reaction_type'].value_counts().to_dict()
    excluded_classes = []
    
    for cls, count in class_counts.items():
        if count < min_samples:
            excluded_classes.append({"class": cls, "count": count})
    
    if excluded_classes:
        excluded_names = [c["class"] for c in excluded_classes]
        df_filtered = df[~df['reaction_type'].isin(excluded_names)]
    else:
        df_filtered = df
    
    metadata = {"excluded_classes": excluded_classes}
    return df_filtered, metadata

def ingest_and_filter(
    input_path: Path,
    output_full: Path,
    output_clean: Path,
    output_metadata: Path,
    output_target_log: Path,
    output_errors: Path,
    config: Dict[str, Any]
) -> None:
    """
    Main ingestion and filtering pipeline (T014, T014b, T016a, T017).
    """
    logger = setup_logger("ingestion")
    logger.log("ingest_and_filter_start", input=str(input_path))
    
    # Load templates from config
    templates = get_templates(config)
    
    # Check input file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Stream and process data
    all_rows = []
    all_errors = []
    
    logger.log("streaming_data", file=str(input_path))
    
    # Determine file type and stream accordingly
    if input_path.suffix == '.parquet':
        # Direct parquet read
        df_raw = pd.read_parquet(input_path)
        # Convert to list of dicts for processing
        data_iter = df_raw.to_dict('records')
    else:
        data_iter = stream_jsonl_gz(input_path)
    
    # Process in chunks if memory is a concern, but for now process all
    chunk_size = 10000
    chunk = []
    
    for i, row in enumerate(data_iter):
        if isinstance(row, dict):
            parsed = row
        elif isinstance(row, str):
            parsed = parse_jsonl_line(row)
            if parsed is None:
                all_errors.append({"line": i, "reason": "Parse error"})
                continue
        else:
            all_errors.append({"line": i, "reason": "Unknown row type"})
            continue
        
        chunk.append(parsed)
        
        if len(chunk) >= chunk_size:
            df_chunk, errors = process_chunk(chunk, templates, logger)
            all_rows.append(df_chunk)
            all_errors.extend(errors)
            chunk = []
    
    # Process remaining chunk
    if chunk:
        df_chunk, errors = process_chunk(chunk, templates, logger)
        all_rows.append(df_chunk)
        all_errors.extend(errors)
    
    if not all_rows:
        raise ValueError("No valid rows found in input data")
    
    # Combine all chunks
    df_full = pd.concat(all_rows, ignore_index=True)
    
    logger.log("combined_rows", count=len(df_full))
    
    # T014b: Target Validation
    target_validation_log = []
    valid_target_count = 0
    invalid_target_count = 0
    
    for idx, row in df_full.iterrows():
        target_source = row.get('target_source')
        target_value = row.get('target_value')
        
        if target_source and target_value is not None:
            valid_target_count += 1
            target_validation_log.append({
                "row_id": idx,
                "target_source": target_source,
                "value": target_value
            })
        else:
            invalid_target_count += 1
    
    total_rows = len(df_full)
    invalid_ratio = invalid_target_count / total_rows if total_rows > 0 else 0
    
    if invalid_ratio > 0.05:
        raise ValueError(f"Target derivation failed for {invalid_ratio*100:.1f}% of rows (>5% threshold)")
    
    # Write target validation log
    output_target_log.parent.mkdir(parents=True, exist_ok=True)
    with open(output_target_log, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["row_id", "target_source", "value"])
        writer.writeheader()
        writer.writerows(target_validation_log)
    
    logger.log("target_validation", valid=valid_target_count, invalid=invalid_target_count)
    
    # T016a: Sample Size Check and Metadata
    df_clean, metadata = filter_by_class_sample_size(df_full)
    
    # Write metadata
    output_metadata.parent.mkdir(parents=True, exist_ok=True)
    with open(output_metadata, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.log("class_exclusion", metadata=metadata)
    
    # T017: Save Full Dataset
    output_full.parent.mkdir(parents=True, exist_ok=True)
    df_full.to_parquet(output_full, index=False)
    
    # Save Clean Dataset
    df_clean.to_csv(output_clean, index=False)
    
    logger.log("saved_artifacts", full=str(output_full), clean=str(output_clean))
    
    # Log errors
    if all_errors:
        output_errors.parent.mkdir(parents=True, exist_ok=True)
        with open(output_errors, 'w') as f:
            json.dump(all_errors, f, indent=2)
        logger.log("errors_logged", count=len(all_errors))
    
    # Register artifacts
    register_artifact(output_full, "filtered_reactions_full.parquet")
    register_artifact(output_clean, "filtered_reactions_clean.csv")
    register_artifact(output_metadata, "class_exclusion_metadata.json")
    register_artifact(output_target_log, "target_validation.log")
    
    logger.log("ingest_and_filter_complete")

def main() -> None:
    """Entry point for ingestion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest and filter USPTO reaction data")
    parser.add_argument("--input", type=str, required=True, help="Input data file (parquet or jsonl.gz)")
    parser.add_argument("--output-full", type=str, default="data/processed/filtered_reactions_full.parquet", help="Output full dataset")
    parser.add_argument("--output-clean", type=str, default="data/processed/filtered_reactions_clean.csv", help="Output clean dataset")
    parser.add_argument("--output-metadata", type=str, default="data/processed/class_exclusion_metadata.json", help="Output exclusion metadata")
    parser.add_argument("--output-target-log", type=str, default="data/processed/target_validation.log", help="Output target validation log")
    parser.add_argument("--output-errors", type=str, default="data/processed/ingestion_errors.json", help="Output error log")
    
    args = parser.parse_args()
    
    config = load_config()
    
    ingest_and_filter(
        input_path=Path(args.input),
        output_full=Path(args.output_full),
        output_clean=Path(args.output_clean),
        output_metadata=Path(args.output_metadata),
        output_target_log=Path(args.output_target_log),
        output_errors=Path(args.output_errors),
        config=config
    )

if __name__ == "__main__":
    main()