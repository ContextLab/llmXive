import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, Tuple
from datetime import datetime
import pandas as pd
from src.utils.logging import setup_logger, get_logger
from src.utils.chemistry import classify_batch, get_templates
from src.utils.state_manager import register_artifact, update_stage_status
from src.data.schemas import ReactionRecord, validate_reaction_record

logger = get_logger(__name__)

def download_uspto_data(url: str, output_path: Path) -> Path:
    """
    Downloads the USPTO dataset from the provided URL.
    For this implementation, we assume the file is already downloaded or
    we simulate the download logic by checking for existence.
    In a real execution, this would use `requests` to fetch the file.
    """
    import requests
    
    logger.info(f"Downloading data from {url}")
    if output_path.exists():
        logger.info(f"File {output_path} already exists, skipping download.")
        return output_path
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Downloaded data to {output_path}")
    return output_path

def parse_jsonl_line(line: str) -> Optional[Dict[str, Any]]:
    """Parses a single JSONL line into a dictionary."""
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON line: {e}")
        return None

def validate_reaction_record(record: Dict[str, Any]) -> Optional[ReactionRecord]:
    """Validates a raw record against the ReactionRecord schema."""
    try:
        # Basic validation: ensure required fields exist
        required_fields = ['reaction_smiles', 'reaction_type'] # reaction_type might be inferred later
        for field in required_fields:
            if field not in record and field != 'reaction_type':
                # reaction_type is derived, so we don't strictly require it in raw input
                pass
        
        # Try to instantiate the dataclass
        # We map raw keys to schema keys if necessary, assuming standard USPTO format
        # USPTO-MIT usually has 'rxn_smiles' or 'reaction_smiles'
        smiles = record.get('reaction_smiles') or record.get('rxn_smiles')
        if not smiles:
            logger.warning("Missing reaction smiles")
            return None
        
        # Determine target variable (yield or success)
        target = None
        if 'yield_pct' in record:
            target = record['yield_pct']
        elif 'success_flag' in record:
            target = record['success_flag']
        
        return ReactionRecord(
            raw_data=record,
            smiles=smiles,
            target=target,
            reaction_type=None # To be filled by classification
        )
    except Exception as e:
        logger.warning(f"Validation failed for record: {e}")
        return None

def process_chunk(chunk: List[Dict[str, Any]], templates: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Processes a chunk of raw records: validates, classifies, and filters.
    Returns a list of valid, classified records.
    """
    valid_records = []
    for raw in chunk:
        parsed = parse_jsonl_line(json.dumps(raw)) if not isinstance(raw, str) else parse_jsonl_line(raw)
        if not parsed:
            continue
        
        validated = validate_reaction_record(parsed)
        if not validated:
            continue
        
        # Classify reaction
        # Assuming classify_batch takes a list of SMILES and returns list of types
        # We pass a list of one to get the type for this record
        reaction_types = classify_batch([validated.smiles], templates)
        if not reaction_types or reaction_types[0] is None:
            # Not matching any template, skip
            continue
        
        validated.reaction_type = reaction_types[0]
        valid_records.append(validated)
    
    return valid_records

def stream_jsonl_gz(file_path: Path, chunk_size: int = 1000) -> Generator[List[Dict[str, Any]], None, None]:
    """Streams a JSONL file in chunks."""
    import gzip
    
    chunk = []
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunk.append(line)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk

def ingest_and_filter(input_path: Path, output_path: Path, templates_config: Dict[str, Any]) -> None:
    """
    Main ingestion pipeline:
    1. Stream input
    2. Validate and classify
    3. Filter by reaction type
    4. Check sample sizes per class
    5. Remove classes with < 1000 samples
    6. Save to CSV
    """
    logger.info(f"Starting ingestion from {input_path}")
    
    # Load templates
    templates = get_templates(templates_config)
    
    all_valid_records = []
    chunk_count = 0
    
    # Process in chunks to handle memory
    for chunk in stream_jsonl_gz(input_path):
        chunk_count += 1
        processed = process_chunk(chunk, templates)
        all_valid_records.extend(processed)
        if chunk_count % 10 == 0:
            logger.info(f"Processed {chunk_count} chunks, total records so far: {len(all_valid_records)}")
    
    logger.info(f"Total valid classified records: {len(all_valid_records)}")
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'reaction_smiles': r.smiles,
            'reaction_type': r.reaction_type,
            'target': r.target,
            'timestamp': datetime.now().isoformat()
        }
        for r in all_valid_records
    ])
    
    if df.empty:
        logger.error("No valid records found after classification.")
        return
    
    # T016: Check sample size per class and remove under-represented classes
    class_counts = df['reaction_type'].value_counts()
    logger.info(f"Class distribution before filtering: \n{class_counts}")
    
    classes_to_keep = []
    for cls, count in class_counts.items():
        if count < 1000:
            logger.warning(f"Class '{cls}' has {count} samples (< 1000). Removing from dataset.")
        else:
            classes_to_keep.append(cls)
    
    if not classes_to_keep:
        logger.error("No classes met the minimum sample size requirement of 1000.")
        # Create empty file or exit? We'll create empty to satisfy path requirement
        df.to_csv(output_path, index=False)
        return

    logger.info(f"Keeping classes: {classes_to_keep}")
    df_filtered = df[df['reaction_type'].isin(classes_to_keep)]
    
    logger.info(f"Final dataset size after filtering: {len(df_filtered)}")
    logger.info(f"Final class distribution: \n{df_filtered['reaction_type'].value_counts()}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df_filtered.to_csv(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")
    
    # Register artifact
    checksum = hashlib.md5(open(output_path, 'rb').read()).hexdigest()
    register_artifact(
        artifact_name="filtered_reactions.csv",
        path=str(output_path),
        checksum=checksum,
        stage="ingestion"
    )

def main():
    """Entry point for the ingestion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest and filter USPTO data")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSONL.gz")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    parser.add_argument("--config", type=str, default="src/modeling/config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    
    setup_logger()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load config for templates
    from src.modeling.config import load_config
    config = load_config(args.config)
    templates_config = config.get('reaction_templates', {})
    
    ingest_and_filter(input_path, output_path, templates_config)

if __name__ == "__main__":
    main()