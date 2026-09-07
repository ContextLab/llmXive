import csv
import gzip
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple

import pandas as pd

# Import from project utilities
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.modeling.config import load_config
from src.utils.chemistry import classify_batch, get_templates

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOG_FILE = PROJECT_ROOT / "logs" / "ingestion.log"

def setup_logging():
    """Configure logging for the ingestion script."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logger("ingestion", LOG_FILE)
    return logger

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_provenance(output_path: Path, input_path: Path, checksum: str, logger: logging.Logger):
    """Save provenance metadata for the output file."""
    provenance = {
        "output_file": str(output_path),
        "input_file": str(input_path),
        "checksum": checksum,
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_stage": "T017_save_filtered_dataset",
        "source": "USPTO-MIT Subset",
        "filters_applied": [
            "SMILES validation",
            "Reaction template matching (SN1, SN2, Diels-Alder)",
            "Class sample size filtering (>= 1000 rows)"
        ]
    }
    provenance_path = output_path.parent / f"{output_path.stem}_provenance.json"
    with open(provenance_path, "w") as f:
        json.dump(provenance, f, indent=2)
    logger.info(f"Saved provenance metadata to {provenance_path}")
    return provenance_path

def stream_jsonl_gz(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Stream JSONL records from a gzipped file."""
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logging.getLogger(__name__).warning(f"Skipping malformed JSON line: {e}")
                    continue

def parse_jsonl_line(record: Dict[str, Any], logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """Parse and validate a single JSONL record."""
    # Basic validation: ensure required fields exist
    required_fields = ["reactants_smiles", "products_smiles"]
    for field in required_fields:
        if field not in record or not record[field]:
            logger.debug(f"Skipping record missing {field}")
            return None
    return record

def process_chunk(chunk: List[Dict[str, Any]], logger: logging.Logger) -> pd.DataFrame:
    """Process a chunk of records, classify reactions, and build a DataFrame."""
    if not chunk:
        return pd.DataFrame()

    # Extract SMILES
    reactants = [r.get("reactants_smiles", "") for r in chunk]
    products = [r.get("products_smiles", "") for r in chunk]
    yields = [r.get("yield_pct") for r in chunk]
    success_flags = [r.get("success_flag") for r in chunk]

    # Classify reactions using templates
    templates = get_templates()
    classifications = classify_batch(reactants, products, templates, logger)

    # Determine target variable
    targets = []
    for i, (y, s) in enumerate(zip(yields, success_flags)):
        if y is not None:
            targets.append(y)
        elif s is not None:
            targets.append(s)
        else:
            targets.append(None)

    # Build DataFrame
    df = pd.DataFrame({
        "reactants_smiles": reactants,
        "products_smiles": products,
        "reaction_type": classifications,
        "target": targets
    })

    # Filter out rows where classification failed or target is missing
    df = df[df["reaction_type"].notna() & df["target"].notna()]
    df = df.reset_index(drop=True)

    return df

def filter_by_class_sample_size(df: pd.DataFrame, min_samples: int = 1000, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """Filter the DataFrame to keep only classes with >= min_samples rows."""
    if logger is None:
        logger = logging.getLogger(__name__)

    counts = df["reaction_type"].value_counts()
    valid_classes = counts[counts >= min_samples].index.tolist()

    if len(valid_classes) < len(counts):
        removed_classes = set(counts.index) - set(valid_classes)
        logger.warning(f"Removing classes with < {min_samples} samples: {removed_classes}")
        for cls in removed_classes:
            logger.warning(f"  - {cls}: {counts[cls]} rows")

    filtered_df = df[df["reaction_type"].isin(valid_classes)].reset_index(drop=True)
    logger.info(f"Filtered dataset: {len(filtered_df)} rows (from {len(df)} original)")
    return filtered_df

def ingest_and_filter(input_file: Path, output_file: Path, chunk_size: int = 10000, logger: Optional[logging.Logger] = None) -> Path:
    """
    Main ingestion pipeline: stream, parse, classify, filter by class size, and save.
    """
    if logger is None:
        logger = setup_logging()

    logger.info(f"Starting ingestion from {input_file}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_rows = []
    total_processed = 0

    # Stream and process in chunks
    for record in stream_jsonl_gz(input_file):
        parsed = parse_jsonl_line(record, logger)
        if parsed:
            all_rows.append(parsed)
            total_processed += 1

        # Process in chunks to manage memory and allow intermediate logging
        if len(all_rows) >= chunk_size:
            chunk_df = process_chunk(all_rows, logger)
            all_rows.clear()  # Clear memory
            # Note: We defer class-size filtering until the end to ensure accurate counts
            # However, for extremely large datasets, one might accumulate stats online.
            # Here we just store the processed chunk in memory (pandas is efficient enough for moderate sizes)
            # To be safe for T017, we will accumulate all processed chunks in a list of DataFrames
            # and concatenate at the end.
            # Actually, to avoid memory explosion, we'll write chunks to a temp file or accumulate if small.
            # Given the constraint, let's accumulate in a list and concat.
            pass

    # Re-structure: accumulate DataFrames directly to avoid holding raw dicts
    df_chunks = []
    current_chunk = []

    for record in stream_jsonl_gz(input_file):
        parsed = parse_jsonl_line(record, logger)
        if parsed:
            current_chunk.append(parsed)

        if len(current_chunk) >= chunk_size:
            chunk_df = process_chunk(current_chunk, logger)
            if not chunk_df.empty:
                df_chunks.append(chunk_df)
            current_chunk = []
            logger.info(f"Processed {total_processed} records so far...")

    # Process remaining
    if current_chunk:
        chunk_df = process_chunk(current_chunk, logger)
        if not chunk_df.empty:
            df_chunks.append(chunk_df)

    if not df_chunks:
        logger.error("No valid data found in input file.")
        raise ValueError("No valid data found in input file.")

    # Concatenate all chunks
    full_df = pd.concat(df_chunks, ignore_index=True)
    logger.info(f"Total raw records after parsing/classification: {len(full_df)}")

    # Apply class sample size filtering (T016 logic)
    filtered_df = filter_by_class_sample_size(full_df, min_samples=1000, logger=logger)

    # Save to CSV
    filtered_df.to_csv(output_file, index=False)
    logger.info(f"Saved filtered dataset to {output_file}")

    # Compute checksum
    checksum = compute_file_checksum(output_file)
    logger.info(f"Checksum: {checksum}")

    # Save provenance
    save_provenance(output_file, input_file, checksum, logger)

    # Update state
    register_artifact(
        artifact_path=str(output_file),
        checksum=checksum,
        stage_id="T017",
        description="Filtered reaction dataset with class balance"
    )

    return output_file

def main():
    """Entry point for the ingestion script."""
    # Load config for paths if needed, or use defaults
    config = load_config()
    
    # Determine input file (T012 should have downloaded this)
    # Default to the standard location if not specified in args
    input_file = DATA_RAW_DIR / "uspto_mit_subset.jsonl.gz"
    output_file = DATA_PROCESSED_DIR / "filtered_reactions.csv"

    # Allow override via environment or args (simplified for this task)
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger = setup_logging()
    try:
        ingest_and_filter(input_file, output_file, logger=logger)
        logger.info("Ingestion and filtering completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
