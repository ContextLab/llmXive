import os
import sys
import gzip
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
from datetime import datetime

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Import project utilities
from code.utils.logging import get_logger, log_excluded_molecules, log_errors
from code.utils.validators import validate_smiles, count_atoms
from code.utils.checksum import calculate_file_checksum, save_checksum_manifest
from code.config import MAX_RAM_GB, TIME_BUDGET

# Constants
CHUNK_SIZE = 1000  # Number of molecules per chunk
MAX_ATOMS = 100    # Max atoms filter threshold
OUTPUT_DIR = Path("data/raw")
LOG_DIR = Path("logs")
CHECKSUMS_FILE = OUTPUT_DIR / "checksums.json"
EXCLUDED_LOG = LOG_DIR / "excluded_molecules.log"
ERROR_LOG = LOG_DIR / "ingestion_errors.log"

def setup_logger(name: str, log_file: Path) -> logging.Logger:
    """Setup a dedicated logger for a specific file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Add handler if not already present
    if not logger.handlers:
        logger.addHandler(fh)
    
    return logger

def calculate_checksum(data: str) -> str:
    """Calculate SHA-256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def validate_schema_compatibility(dataset: Any) -> bool:
    """
    Validate that the dataset contains necessary fields for downstream processing.
    Checks for SMILES and metadata that supports 3D conformer generation.
    """
    try:
        # Check if dataset has 'smiles' column (or similar)
        if hasattr(dataset, 'column_names'):
            cols = dataset.column_names
            if 'smiles' not in cols and 'SMILES' not in cols:
                raise ValueError("Dataset missing 'smiles' column")
        
        # Verify we can access the first item to check structure
        for item in dataset.take(1):
            if 'smiles' not in item and 'SMILES' not in item:
                raise ValueError("Dataset item missing 'smiles' field")
            break
        
        return True
    except Exception as e:
        logging.error(f"Schema validation failed: {e}")
        return False

def fetch_zinc15_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fetch ZINC15 dataset using Hugging Face datasets streaming.
    Yields molecules one by one to avoid loading full dataset into RAM.
    """
    # Check for override environment variable
    override_source = os.getenv("DATA_SOURCE_OVERRIDE")
    
    if override_source:
        logging.info(f"Using overridden data source: {override_source}")
        dataset_name = override_source
    else:
        dataset_name = "Zinc15"  # Standard ZINC15 dataset on HF
    
    try:
        # Load dataset in streaming mode
        dataset = load_dataset(dataset_name, split="train", streaming=True)
        
        # Validate schema before processing
        if not validate_schema_compatibility(dataset):
            raise ValueError("Dataset schema validation failed")
        
        return dataset
    except Exception as e:
        logging.error(f"Failed to fetch ZINC15 stream: {e}")
        raise ConnectionError(f"Unable to access ZINC15 source: {e}")

def process_smiles_chunk(chunk: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Process a chunk of SMILES strings.
    Returns: (valid_molecules, excluded_smiles, error_smiles)
    """
    valid_molecules = []
    excluded_smiles = []
    error_smiles = []
    
    for item in chunk:
        # Get SMILES string (handle potential case variations)
        smiles = item.get('smiles') or item.get('SMILES') or item.get('smi')
        
        if not smiles:
            error_smiles.append(str(item))
            continue
        
        # Validate SMILES syntax using T017
        is_valid = validate_smiles([smiles])
        if not is_valid or smiles in is_valid:
            error_smiles.append(smiles)
            continue
        
        # Count atoms using RDKit
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            error_smiles.append(smiles)
            continue
        
        atom_count = mol.GetNumAtoms()
        
        # Apply Max Atoms Filter (T048 requirement)
        if atom_count > MAX_ATOMS:
            excluded_smiles.append(smiles)
            continue
        
        # Add to valid molecules
        valid_molecules.append({
            'smiles': smiles,
            'atom_count': atom_count,
            'metadata': {
                'source': 'ZINC15',
                'processed_at': datetime.utcnow().isoformat()
            }
        })
    
    return valid_molecules, excluded_smiles, error_smiles

def write_chunk_to_parquet(chunk_data: List[Dict[str, Any]], chunk_id: int) -> str:
    """Write a processed chunk to a Parquet file."""
    if not chunk_data:
        return ""
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = OUTPUT_DIR / f"chunk_{chunk_id:04d}.parquet"
    
    # Convert to DataFrame
    df = pd.DataFrame(chunk_data)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False)
    
    # Calculate and save checksum
    checksum = calculate_file_checksum(str(output_path))
    
    return str(output_path), checksum

def process_and_write_chunk(chunk: List[Dict[str, Any]], chunk_id: int, 
                            excluded_logger: logging.Logger, 
                            error_logger: logging.Logger) -> Tuple[int, int, int, Optional[str]]:
    """
    Process a chunk and write to Parquet.
    Returns: (valid_count, excluded_count, error_count, output_path)
    """
    # Process the chunk
    valid_molecules, excluded_smiles, error_smiles = process_smiles_chunk(chunk)
    
    # Log excluded molecules
    if excluded_smiles:
        log_excluded_molecules(len(excluded_smiles), excluded_smiles)
        for smiles in excluded_smiles:
            excluded_logger.info(f"Excluded (max atoms > {MAX_ATOMS}): {smiles}")
    
    # Log errors
    if error_smiles:
        for smiles in error_smiles:
            error_logger.info(f"Invalid SMILES: {smiles}")
    
    # Write valid molecules to Parquet
    output_path = None
    if valid_molecules:
        path, checksum = write_chunk_to_parquet(valid_molecules, chunk_id)
        output_path = path
        
        # Save checksum to manifest
        checksum_data = {
            'file': path,
            'checksum': checksum,
            'timestamp': datetime.utcnow().isoformat(),
            'valid_count': len(valid_molecules),
            'excluded_count': len(excluded_smiles),
            'error_count': len(error_smiles)
        }
        save_checksum_manifest(CHECKSUMS_FILE, checksum_data)
    
    return len(valid_molecules), len(excluded_smiles), len(error_smiles), output_path

def main():
    """Main ingestion pipeline entry point."""
    # Setup logging
    setup_logging = get_logger('ingest')
    excluded_logger = setup_logger('excluded_molecules', EXCLUDED_LOG)
    error_logger = setup_logger('ingestion_errors', ERROR_LOG)
    
    logging.info("Starting ZINC15 ingestion pipeline (T048)")
    logging.info(f"Max atoms filter: {MAX_ATOMS}")
    logging.info(f"Chunk size: {CHUNK_SIZE}")
    
    total_valid = 0
    total_excluded = 0
    total_errors = 0
    chunk_count = 0
    
    try:
        # Fetch streaming dataset
        dataset = fetch_zinc15_streaming()
        
        # Process in chunks
        chunk = []
        for idx, item in enumerate(dataset):
            chunk.append(item)
            
            if len(chunk) >= CHUNK_SIZE:
                chunk_count += 1
                valid, excluded, errors, _ = process_and_write_chunk(
                    chunk, chunk_count, excluded_logger, error_logger
                )
                
                total_valid += valid
                total_excluded += excluded
                total_errors += errors
                
                logging.info(f"Processed chunk {chunk_count}: {valid} valid, {excluded} excluded, {errors} errors")
                
                # Verify chunk integrity
                if valid + excluded + errors != len(chunk):
                    raise ValueError(f"Chunk integrity check failed: expected {len(chunk)}, got {valid + excluded + errors}")
                
                chunk = []
                
                # Optional: Stop after a certain number of chunks for testing
                # if chunk_count >= 10:
                #     break
        
        # Process remaining items
        if chunk:
            chunk_count += 1
            valid, excluded, errors, _ = process_and_write_chunk(
                chunk, chunk_count, excluded_logger, error_logger
            )
            
            total_valid += valid
            total_excluded += excluded
            total_errors += errors
            
            logging.info(f"Processed final chunk {chunk_count}: {valid} valid, {excluded} excluded, {errors} errors")
            
            # Verify final chunk integrity
            if valid + excluded + errors != len(chunk):
                raise ValueError(f"Final chunk integrity check failed")
        
        # Final summary
        logging.info(f"Ingestion complete: {total_valid} valid, {total_excluded} excluded, {total_errors} errors")
        logging.info(f"Total chunks written: {chunk_count}")
        
        # Log final statistics
        log_dataset_statistics({
            'total_processed': total_valid + total_excluded + total_errors,
            'valid_count': total_valid,
            'excluded_count': total_excluded,
            'error_count': total_errors,
            'chunk_count': chunk_count,
            'max_atoms_threshold': MAX_ATOMS
        })
        
    except ConnectionError as e:
        logging.error(f"Critical connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Ingestion pipeline failed: {e}")
        log_errors([e])
        raise

if __name__ == "__main__":
    main()