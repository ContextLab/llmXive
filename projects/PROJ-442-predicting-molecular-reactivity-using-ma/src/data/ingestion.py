import os
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional
from datetime import datetime

# Import from project modules (matching API surface)
from src.utils.logging import setup_logging
from src.utils.state_manager import update_artifact_state
from src.data.schemas import ReactionRecord

# Configuration constants
CHUNK_SIZE = 1000  # Number of records to process at a time
USPTO_URL = "https://zenodo.org/record/3969375/files/uspto_mit_subset.jsonl"
# Note: Actual URL structure may vary; this is a placeholder for the real endpoint
# In a real implementation, we would use the specific file download URL from Zenodo
# For now, we assume the file is downloaded manually or via a separate step
# and placed in data/raw/uspto_mit_subset.jsonl
RAW_DATA_PATH = Path("data/raw/uspto_mit_subset.jsonl")
PROCESSED_DATA_PATH = Path("data/processed/filtered_reactions.csv")
ERROR_LOG_PATH = Path("data/raw/error_log.json")

logger = setup_logging()

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "src/data",
        "src/modeling",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "scripts",
        "state/projects"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {dirs}")

def download_data():
    """Download USPTO-MIT subset from Zenodo."""
    ensure_dirs()
    if RAW_DATA_PATH.exists():
        logger.info(f"Data already exists at {RAW_DATA_PATH}")
        return RAW_DATA_PATH

    logger.info(f"Downloading data from {USPTO_URL}")
    try:
        response = requests.get(USPTO_URL, stream=True)
        response.raise_for_status()
        with open(RAW_DATA_PATH, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Data downloaded to {RAW_DATA_PATH}")
        return RAW_DATA_PATH
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        # Fallback: assume data is manually placed (for CI/CD or local dev)
        if RAW_DATA_PATH.exists():
            logger.warning("Using existing local file as fallback")
            return RAW_DATA_PATH
        raise FileNotFoundError(f"Data file not found at {RAW_DATA_PATH} and download failed")

def parse_jsonl(file_path: Path) -> Generator[Dict[str, Any], None, None]:
    """Parse JSONL file line by line to handle large files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                yield record
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

def normalize_smiles(smiles: str) -> Optional[str]:
    """Normalize SMILES string using RDKit."""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception as e:
        logger.warning(f"Failed to normalize SMILES '{smiles}': {e}")
        return None

def process_record(record: Dict[str, Any]) -> Optional[ReactionRecord]:
    """Process a single record and validate against schema."""
    try:
        # Extract relevant fields
        reactants = record.get('reactants', '')
        products = record.get('products', '')
        reaction_type = record.get('reaction_type', None)
        yield_pct = record.get('yield_pct', None)
        success_flag = record.get('success_flag', None)

        # Normalize SMILES
        norm_reactants = normalize_smiles(reactants)
        norm_products = normalize_smiles(products)

        if norm_reactants is None or norm_products is None:
            return None

        # Determine target variable (per T014)
        target = yield_pct if yield_pct is not None else (1 if success_flag else 0) if success_flag is not None else None

        if target is None:
            return None

        # Create ReactionRecord
        return ReactionRecord(
            reactants=norm_reactants,
            products=norm_products,
            reaction_type=reaction_type,
            target=target,
            raw_record=record
        )
    except Exception as e:
        logger.warning(f"Failed to process record: {e}")
        return None

def save_to_csv(records: List[ReactionRecord], output_path: Path):
    """Save records to CSV file."""
    if not records:
        logger.warning("No records to save")
        return

    headers = ['reactants', 'products', 'reaction_type', 'target']
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(','.join(headers) + '\n')
        for rec in records:
            row = [
                rec.reactants,
                rec.products,
                rec.reaction_type if rec.reaction_type else '',
                str(rec.target)
            ]
            f.write(','.join(f'"{x}"' for x in row) + '\n')
    logger.info(f"Saved {len(records)} records to {output_path}")

def process_batch(records: List[Dict[str, Any]]) -> List[ReactionRecord]:
    """Process a batch of records and return valid ReactionRecords."""
    valid_records = []
    for record in records:
        processed = process_record(record)
        if processed:
            valid_records.append(processed)
    return valid_records

def main():
    """Main function to run ingestion with batch processing."""
    logger.info("Starting data ingestion with batch processing")
    ensure_dirs()

    # Download data if needed
    data_path = download_data()

    # Process in chunks to handle memory limits
    all_records = []
    error_records = []
    batch = []
    total_processed = 0

    for record in parse_jsonl(data_path):
        batch.append(record)
        total_processed += 1

        if len(batch) >= CHUNK_SIZE:
            # Process batch
            valid_batch = process_batch(batch)
            all_records.extend(valid_batch)

            # Log progress
            logger.info(f"Processed batch of {len(batch)} records, {len(valid_batch)} valid")

            # Clear batch
            batch = []

    # Process remaining records
    if batch:
        valid_batch = process_batch(batch)
        all_records.extend(valid_batch)
        logger.info(f"Processed final batch of {len(batch)} records, {len(valid_batch)} valid")

    logger.info(f"Total records processed: {total_processed}, valid: {len(all_records)}")

    # Save to CSV
    save_to_csv(all_records, PROCESSED_DATA_PATH)

    # Update state
    checksum = hashlib.md5(PROCESSED_DATA_PATH.read_bytes()).hexdigest()
    update_artifact_state(
        artifact_name="filtered_reactions.csv",
        path=str(PROCESSED_DATA_PATH),
        checksum=checksum,
        metadata={
            "total_processed": total_processed,
            "valid_records": len(all_records),
            "chunk_size": CHUNK_SIZE,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    logger.info("Ingestion completed successfully")

if __name__ == "__main__":
    main()
