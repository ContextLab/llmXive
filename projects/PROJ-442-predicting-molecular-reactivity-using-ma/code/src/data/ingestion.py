import csv
import gzip
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator

import pandas as pd
from tqdm import tqdm

from src.modeling.config import load_config
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import register_artifact, update_stage_status
from src.utils.chemistry import classify_batch, get_templates
from src.data.schemas import ReactionRecord, validate_reaction_record

# --- Configuration & Constants ---
DEFAULT_CHUNK_SIZE = 10000
OUTPUT_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")

# --- Helper Functions ---

def setup_logging() -> logging.Logger:
    """Initialize logging for the ingestion module."""
    logger = setup_logger("ingestion")
    return logger

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_provenance(
    output_path: Path,
    input_path: Optional[Path],
    checksum: str,
    config: Dict[str, Any],
    logger: logging.Logger
) -> Path:
    """Save provenance metadata for the output file."""
    provenance = {
        "output_file": str(output_path),
        "input_file": str(input_path) if input_path else None,
        "checksum": checksum,
        "timestamp": datetime.utcnow().isoformat(),
        "config_snapshot": {
            "source_url": config.get("data", {}).get("source_url"),
            "reaction_templates_version": config.get("modeling", {}).get("reaction_templates_version", "unknown")
        },
        "processing_stats": {
            "rows_written": 0  # To be updated after writing
        }
    }
    provenance_path = output_path.with_suffix(".provenance.json")
    with open(provenance_path, "w") as f:
        json.dump(provenance, f, indent=2)
    logger.info(f"Provenance saved to {provenance_path}")
    return provenance_path

def stream_jsonl_gz(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Stream lines from a gzipped JSONL file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logging.getLogger("ingestion").warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

def parse_jsonl_line(line_data: Dict[str, Any], logger: logging.Logger) -> Optional[ReactionRecord]:
    """Parse a raw JSONL record into a ReactionRecord."""
    try:
        # Map raw keys to standard schema keys if necessary
        # Assuming raw data has 'reactants', 'product', 'yield', 'success_flag', etc.
        # Adjust mapping based on actual USPTO subset schema
        reaction_smiles = line_data.get("reaction_smiles")
        if not reaction_smiles:
            logger.debug("Missing reaction_smiles")
            return None

        # Basic validation
        record = ReactionRecord(
            reaction_smiles=reaction_smiles,
            reactants=line_data.get("reactants", []),
            product=line_data.get("product"),
            yield_pct=line_data.get("yield_pct"),
            success_flag=line_data.get("success_flag"),
            metadata=line_data
        )
        return record
    except Exception as e:
        logger.debug(f"Failed to parse line: {e}")
        return None

def process_chunk(
    chunk: List[ReactionRecord],
    logger: logging.Logger
) -> Tuple[pd.DataFrame, int]:
    """Process a chunk of records: classify and filter."""
    valid_records = []
    malformed_count = 0

    # Extract SMILES for batch classification
    smiles_list = [r.reaction_smiles for r in chunk if r.reaction_smiles]

    if not smiles_list:
        return pd.DataFrame(), 0

    # Classify reactions
    classifications = classify_batch(smiles_list, logger)

    # Reconstruct valid records with classification
    for record, reaction_type in zip(chunk, classifications):
        if reaction_type is None:
            malformed_count += 1
            continue

        record.reaction_type = reaction_type
        # Derive target variable per FR-004
        if record.yield_pct is not None:
            record.target_value = record.yield_pct
        elif record.success_flag is not None:
            record.target_value = 1.0 if record.success_flag else 0.0
        else:
            # If no target, mark as invalid for modeling but keep for metadata?
            # Task T014 says "strictly derive... if present". If missing, we might drop or flag.
            # For T017, we keep valid reactions (valid SMILES + valid class).
            record.target_value = None

        valid_records.append(record)

    # Convert to DataFrame
    if not valid_records:
        return pd.DataFrame(), malformed_count

    data = [
        {
            "reaction_smiles": r.reaction_smiles,
            "reaction_type": r.reaction_type,
            "target_value": r.target_value,
            "yield_pct": r.yield_pct,
            "success_flag": r.success_flag
        }
        for r in valid_records
    ]
    df = pd.DataFrame(data)
    return df, malformed_count

def filter_by_class_sample_size(
    df: pd.DataFrame,
    min_samples: int,
    logger: logging.Logger
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter classes with < min_samples.
    Returns the filtered dataframe and metadata about excluded classes.
    Note: Per T016/T017, we do NOT drop rows from the main file if they are valid,
    but we log exclusion metadata. However, T017 says "Ensure the file contains ALL valid reactions".
    So we DO NOT filter the dataframe here. We only generate the metadata file.
    """
    class_counts = df['reaction_type'].value_counts()
    excluded_classes = {}

    for cls, count in class_counts.items():
        if count < min_samples:
            excluded_classes[cls] = {
                "count": int(count),
                "reason": f"Sample size ({count}) below threshold ({min_samples})"
            }
            logger.warning(f"Class '{cls}' has only {count} samples (< {min_samples}). Logged in exclusion metadata.")

    # Save exclusion metadata
    if excluded_classes:
        meta_path = Path("data/processed/class_exclusion_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(excluded_classes, f, indent=2)
        logger.info(f"Exclusion metadata saved to {meta_path}")

    # Return the FULL dataframe (do not drop rows as per T017 requirement)
    return df, excluded_classes

def ingest_and_filter(
    input_path: Path,
    output_path: Path,
    config: Dict[str, Any],
    logger: logging.Logger,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> None:
    """
    Main ingestion pipeline:
    1. Stream input
    2. Parse and classify
    3. Write to CSV
    4. Generate checksum and provenance
    5. Handle class balance metadata
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare CSV writer
    fieldnames = ["reaction_smiles", "reaction_type", "target_value", "yield_pct", "success_flag"]

    total_rows = 0
    malformed_rows = 0
    valid_rows = 0

    # Open output file
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Stream and process
        # We need to accumulate chunks to apply class filtering logic if needed,
        # but T017 says "ALL valid reactions". So we write valid ones immediately.
        # We track counts for the exclusion metadata generation.

        all_class_counts = {}

        with tqdm(stream_jsonl_gz(input_path), desc="Ingesting and Classifying") as pbar:
            for record_data in pbar:
                record = parse_jsonl_line(record_data, logger)
                if not record:
                    malformed_rows += 1
                    continue

                # Classify single record (or batch in larger chunks for efficiency)
                # For simplicity in this streaming context, we classify individually or small batches
                # Using classify_batch for efficiency if we buffer
                # Let's buffer to classify in batches
                # (Simplified: classify one by one for this snippet, or buffer logic)
                # Re-implementing batch logic for streaming:
                pass

    # Optimized Batch Processing
    buffer = []
    buffer_size = 1000

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for record_data in tqdm(stream_jsonl_gz(input_path), desc="Ingesting and Classifying"):
            record = parse_jsonl_line(record_data, logger)
            if not record:
                malformed_rows += 1
                continue

            buffer.append(record)

            if len(buffer) >= buffer_size:
                # Process buffer
                smiles_batch = [r.reaction_smiles for r in buffer]
                types_batch = classify_batch(smiles_batch, logger)

                for record, r_type in zip(buffer, types_batch):
                    if r_type is None:
                        malformed_rows += 1
                        continue

                    record.reaction_type = r_type
                    if record.yield_pct is not None:
                        record.target_value = record.yield_pct
                    elif record.success_flag is not None:
                        record.target_value = 1.0 if record.success_flag else 0.0
                    else:
                        record.target_value = None

                    # Write row
                    writer.writerow({
                        "reaction_smiles": record.reaction_smiles,
                        "reaction_type": record.reaction_type,
                        "target_value": record.target_value,
                        "yield_pct": record.yield_pct,
                        "success_flag": record.success_flag
                    })
                    valid_rows += 1
                    all_class_counts[record.reaction_type] = all_class_counts.get(record.reaction_type, 0) + 1

                buffer = []
                pbar.update(buffer_size)

        # Flush remaining
        if buffer:
            smiles_batch = [r.reaction_smiles for r in buffer]
            types_batch = classify_batch(smiles_batch, logger)
            for record, r_type in zip(buffer, types_batch):
                if r_type is None:
                    malformed_rows += 1
                    continue
                record.reaction_type = r_type
                if record.yield_pct is not None:
                    record.target_value = record.yield_pct
                elif record.success_flag is not None:
                    record.target_value = 1.0 if record.success_flag else 0.0
                else:
                    record.target_value = None

                writer.writerow({
                    "reaction_smiles": record.reaction_smiles,
                    "reaction_type": record.reaction_type,
                    "target_value": record.target_value,
                    "yield_pct": record.yield_pct,
                    "success_flag": record.success_flag
                })
                valid_rows += 1
                all_class_counts[record.reaction_type] = all_class_counts.get(record.reaction_type, 0) + 1

    total_rows = valid_rows + malformed_rows
    logger.info(f"Ingestion complete. Total: {total_rows}, Valid: {valid_rows}, Malformed: {malformed_rows}")

    # Checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")

    # Provenance
    save_provenance(output_path, input_path, checksum, config, logger)

    # Class Balance Check (T016 logic)
    min_samples = config.get("data", {}).get("min_class_samples", 1000)
    filter_by_class_sample_size(
        pd.read_csv(output_path), # Re-read to get DF for counting (or use all_class_counts)
        min_samples,
        logger
    )

    # Update State
    update_stage_status("data_ingestion", "completed")
    register_artifact(str(output_path), checksum)

def main():
    """Entry point for the ingestion script."""
    logger = setup_logging()
    logger.info("Starting molecular reactivity data ingestion.")

    config = load_config()
    source_url = config.get("data", {}).get("source_url")
    # Note: T012 handles download. Here we assume input is already in data/raw/
    # But the task description implies T017 saves the filtered dataset.
    # We need an input file. Let's assume the input is the raw parquet or jsonl from T012.
    # The command line arg --output is provided in the failure log, but we need --input.
    # Let's check config for default input if not provided.

    import argparse
    parser = argparse.ArgumentParser(description="Ingest and filter reaction data.")
    parser.add_argument("--input", type=str, required=False, help="Path to raw input file (jsonl.gz or parquet)")
    parser.add_argument("--output", type=str, default="data/processed/filtered_reactions.csv", help="Path to output CSV")
    args = parser.parse_args()

    # Determine input
    input_path = Path(args.input) if args.input else RAW_DIR / "uspto_subset.parquet"

    # If parquet, convert to stream or read directly
    # For simplicity, if parquet, read to DF and write to CSV directly after classification
    # But the code above expects stream_jsonl_gz. Let's handle both.
    
    if input_path.suffix == ".parquet":
        logger.info(f"Reading parquet from {input_path}")
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return

        df_raw = pd.read_parquet(input_path)
        
        # Process in chunks
        chunk_size = 10000
        total_rows = len(df_raw)
        valid_rows = 0
        malformed_rows = 0
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["reaction_smiles", "reaction_type", "target_value", "yield_pct", "success_flag"]
        
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for i in tqdm(range(0, total_rows, chunk_size), desc="Processing Parquet Chunks"):
                chunk = df_raw.iloc[i:i+chunk_size]
                smiles_list = chunk["reaction_smiles"].dropna().tolist()
                
                if not smiles_list:
                    continue

                classifications = classify_batch(smiles_list, logger)
                
                # Map back to rows
                # We need to handle missing smiles in the original chunk
                # Let's iterate the chunk
                for _, row in chunk.iterrows():
                    smiles = row.get("reaction_smiles")
                    if not smiles:
                        malformed_rows += 1
                        continue
                    
                    # Find classification
                    # This is inefficient if we don't map indices, but classify_batch returns list
                    # We need to align.
                    # Better: classify the whole list and map by index
                    pass
                
                # Re-doing the loop for efficiency
                # Extract valid smiles and their original indices
                valid_indices = []
                valid_smiles = []
                for idx, val in enumerate(chunk["reaction_smiles"]):
                    if pd.notna(val):
                        valid_indices.append(idx)
                        valid_smiles.append(val)
                    else:
                        malformed_rows += 1
                
                if not valid_smiles:
                    continue

                types = classify_batch(valid_smiles, logger)
                
                type_map = {idx: t for idx, t in zip(valid_indices, types)}
                
                for idx, val in chunk["reaction_smiles"].items():
                    if pd.isna(val):
                        continue
                    
                    r_type = type_map.get(idx)
                    if r_type is None:
                        malformed_rows += 1
                        continue
                    
                    yield_pct = row.get("yield_pct")
                    success_flag = row.get("success_flag")
                    
                    target = None
                    if pd.notna(yield_pct):
                        target = yield_pct
                    elif pd.notna(success_flag):
                        target = 1.0 if success_flag else 0.0
                    
                    writer.writerow({
                        "reaction_smiles": val,
                        "reaction_type": r_type,
                        "target_value": target,
                        "yield_pct": yield_pct,
                        "success_flag": success_flag
                    })
                    valid_rows += 1

        logger.info(f"Parquet processing complete. Valid: {valid_rows}, Malformed: {malformed_rows}")
        input_path_for_provenance = input_path
    else:
        # Assume JSONL/GZ
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return
        input_path_for_provenance = input_path
        ingest_and_filter(input_path, Path(args.output), config, logger)
        valid_rows = 0 # Handled inside ingest_and_filter for logging
        # Re-read for checksum
        output_path = Path(args.output)
        checksum = compute_file_checksum(output_path)
        save_provenance(output_path, input_path_for_provenance, checksum, config, logger)
        # Class balance
        df_check = pd.read_csv(output_path)
        filter_by_class_sample_size(df_check, config.get("data", {}).get("min_class_samples", 1000), logger)
        return

    # Finalize Parquet path
    output_path = Path(args.output)
    checksum = compute_file_checksum(output_path)
    save_provenance(output_path, input_path_for_provenance, checksum, config, logger)
    
    # Class balance check for parquet path too
    df_check = pd.read_csv(output_path)
    filter_by_class_sample_size(df_check, config.get("data", {}).get("min_class_samples", 1000), logger)

    logger.info("Ingestion pipeline finished successfully.")

if __name__ == "__main__":
    main()
