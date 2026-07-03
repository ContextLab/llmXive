import csv
import gzip
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Tuple

from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import update_stage_status, register_artifact
from src.data.schemas import validate_reaction_record
from src.utils.chemistry import classify_reaction, get_templates
from src.modeling.config import load_config

# Constants
USPTO_URL = "https://zenodo.org/record/3969375/files/uspto-mit.jsonl.gz"
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "filtered_reactions.csv"
ERROR_LOG_FILE = Path("data/processed/ingestion_errors.log")
CHECKSUM_FILE = Path("data/processed/filtered_reactions.csv.sha256")
STAGE_NAME = "ingestion"
MIN_CLASS_COUNT = 1000

def download_uspto_data(url: str, output_path: Path) -> Path:
    """Download the USPTO-MIT dataset from Zenodo."""
    import requests
    logger = get_logger("ingestion")
    logger.info(f"Downloading dataset from {url}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Downloaded to {output_path}")
    return output_path

def stream_jsonl_gz(file_path: Path) -> Iterator[Dict[str, Any]]:
    """Stream lines from a gzipped JSONL file."""
    logger = get_logger("ingestion")
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")

def parse_jsonl_line(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse and validate a single JSONL record."""
    logger = get_logger("ingestion")
    
    # Basic validation
    required_fields = ['reactants', 'products', 'reaction_smiles']
    for field in required_fields:
        if field not in record:
            logger.debug(f"Missing required field {field}")
            return None
    
    # Validate SMILES using schema helper
    if not validate_reaction_record(record):
        logger.debug(f"Record failed schema validation")
        return None
    
    return record

def process_chunk(chunk: List[Dict[str, Any]], templates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Process a chunk of records, classifying and filtering."""
    logger = get_logger("ingestion")
    filtered = []
    malformed_count = 0
    
    for record in chunk:
        try:
            # Classify reaction
            reaction_type = classify_reaction(record.get('reaction_smiles', ''), templates)
            
            if reaction_type is None:
                malformed_count += 1
                continue
            
            # Determine target variable
            target = None
            if 'yield_pct' in record:
                target = record['yield_pct']
            elif 'success_flag' in record:
                target = 1.0 if record['success_flag'] else 0.0
            
            if target is None:
                continue
            
            enriched_record = {
                **record,
                'reaction_type': reaction_type,
                'target': target
            }
            filtered.append(enriched_record)
            
        except Exception as e:
            logger.error(f"Error processing record: {e}")
            malformed_count += 1
            continue
    
    if malformed_count > 0:
        logger.warning(f"Skipped {malformed_count} records in this chunk due to errors/mismatches")
    
    return filtered

def ingest_and_filter(
    raw_data_path: Optional[Path] = None,
    force_download: bool = False
) -> Path:
    """
    Main ingestion pipeline: download, parse, classify, filter, and save.
    Returns the path to the output CSV.
    """
    logger = setup_logger("ingestion", level=logging.INFO)
    logger.info("Starting USPTO ingestion and filtering pipeline")
    
    # 1. Download data if needed
    downloaded_path = Path("data/raw/uspto-mit.jsonl.gz")
    if force_download or not downloaded_path.exists():
        download_uspto_data(USPTO_URL, downloaded_path)
    
    # 2. Load config for templates
    logger.info("Loading reaction templates from config")
    config = load_config()
    templates = config.get('reaction_templates', {})
    
    # 3. Stream and process
    logger.info("Streaming and processing JSONL data")
    all_filtered: List[Dict[str, Any]] = []
    class_counts: Dict[str, int] = {}
    
    # Process in memory-friendly chunks
    chunk_size = 1000
    current_chunk: List[Dict[str, Any]] = []
    
    for record in stream_jsonl_gz(downloaded_path):
        parsed = parse_jsonl_line(record)
        if parsed:
            current_chunk.append(parsed)
        
        if len(current_chunk) >= chunk_size:
            processed = process_chunk(current_chunk, templates)
            all_filtered.extend(processed)
            current_chunk = []
    
    # Process remaining
    if current_chunk:
        processed = process_chunk(current_chunk, templates)
        all_filtered.extend(processed)
    
    # 4. Filter by class size (FR-006)
    logger.info(f"Initial filtered count: {len(all_filtered)}")
    
    # Count classes
    for rec in all_filtered:
        rt = rec.get('reaction_type')
        class_counts[rt] = class_counts.get(rt, 0) + 1
    
    logger.info(f"Class counts before size filter: {class_counts}")
    
    # Filter out classes with < MIN_CLASS_COUNT
    valid_classes = {k for k, v in class_counts.items() if v >= MIN_CLASS_COUNT}
    if len(valid_classes) < len(class_counts):
        logger.warning(f"Removing classes with < {MIN_CLASS_COUNT} samples: {set(class_counts.keys()) - valid_classes}")
    
    final_data = [r for r in all_filtered if r.get('reaction_type') in valid_classes]
    logger.info(f"Final record count after size filter: {len(final_data)}")
    
    # 5. Write to CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = ['reaction_smiles', 'reactants', 'products', 'reaction_type', 'target', 'yield_pct', 'success_flag']
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(final_data)
    
    logger.info(f"Wrote {len(final_data)} records to {OUTPUT_FILE}")
    
    # 6. Compute checksum
    checksum = hashlib.sha256()
    with open(OUTPUT_FILE, 'rb') as f:
        for chunk_iter in iter(lambda: f.read(4096), b""):
            checksum.update(chunk_iter)
    checksum_hex = checksum.hexdigest()
    
    with open(CHECKSUM_FILE, 'w') as f:
        f.write(checksum_hex)
    
    logger.info(f"Checksum computed: {checksum_hex}")
    
    # 7. Update State
    logger.info("Updating project state")
    register_artifact(
        artifact_name="filtered_reactions",
        artifact_path=str(OUTPUT_FILE),
        checksum=checksum_hex,
        stage=STAGE_NAME
    )
    
    update_stage_status(
        stage=STAGE_NAME,
        status="completed",
        message=f"Ingestion complete. Output: {OUTPUT_FILE}",
        artifact_count=1
    )
    
    return OUTPUT_FILE

def main():
    """Entry point for the ingestion script."""
    logger = setup_logger("ingestion_main", level=logging.INFO)
    try:
        output_path = ingest_and_filter()
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()