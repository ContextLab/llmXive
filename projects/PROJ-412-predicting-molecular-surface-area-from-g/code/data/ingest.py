"""
Robust dataset ingestion module for ZINC15.

Implements strict 'Fail Loudly' principles:
- No fallback to synthetic data on network failure.
- Immediate raising of ConnectionError or ValueError on real data fetch failure.
- Streaming processing to handle large datasets within memory constraints.
"""
import os
import sys
import gzip
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from datasets import load_dataset
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Project imports based on API surface
from code.utils.logging import get_logger, log_errors, log_excluded_molecules
from code.utils.validators import validate_smiles, count_atoms
from code.config import MAX_RAM_GB, SENSITIVITY_THRESHOLDS

# Configure logger
logger = get_logger(__name__)

# Constants
ZINC15_STREAM_URL = "zinc15/filtered"  # HuggingFace dataset ID for ZINC15 filtered
CHUNK_SIZE = 1000  # Number of molecules per processing chunk
MAX_ATOMS_THRESHOLD = 100  # Filter molecules with > 100 atoms

def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum of data."""
    return hashlib.sha256(data).hexdigest()

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def fetch_zinc15_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fetch ZINC15 dataset in streaming mode.
    
    Strictly adheres to 'Fail Loudly' principle:
    - If the dataset is unreachable or invalid, raises ConnectionError or ValueError immediately.
    - No synthetic fallback.
    
    Yields:
        Iterator of molecule records (dicts).
        
    Raises:
        ConnectionError: If network connection to HuggingFace fails.
        ValueError: If dataset configuration is invalid or empty.
    """
    try:
        # Check for environment override first
        data_source_override = os.getenv("DATA_SOURCE_OVERRIDE")
        if data_source_override:
            logger.warning(f"Using environment override for data source: {data_source_override}")
            dataset_id = data_source_override
        else:
            dataset_id = ZINC15_STREAM_URL

        logger.info(f"Attempting to stream dataset: {dataset_id}")
        
        # Attempt to load the dataset in streaming mode
        # This will raise an exception if the network is unreachable or the dataset ID is invalid
        dataset = load_dataset(dataset_id, split="train", streaming=True)
        
        # Verify the dataset is not empty by attempting to fetch one item
        try:
            first_item = next(iter(dataset))
            logger.info(f"Successfully connected to dataset. Sample keys: {first_item.keys()}")
        except StopIteration:
            raise ValueError("The dataset stream is empty.")
        
        # Yield items from the stream
        for item in dataset:
            yield item
            
    except ConnectionError as e:
        # Re-raise connection errors immediately
        logger.critical(f"Network connection failed while fetching dataset: {e}")
        raise
    except Exception as e:
        # Catch all other exceptions related to data fetching and re-raise as ValueError
        logger.critical(f"Failed to fetch dataset: {e}")
        raise ValueError(f"Dataset fetch failed: {e}") from e

def process_smiles_chunk(chunk: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Process a chunk of SMILES strings.
    
    Validates SMILES, filters by atom count, and extracts basic features.
    
    Args:
        chunk: List of raw molecule records from the stream.
        
    Returns:
        Tuple of (processed_records, excluded_smiles, invalid_smiles).
    """
    processed_records = []
    excluded_smiles = []
    invalid_smiles = []
    
    for record in chunk:
        smiles = record.get("smiles")
        if not smiles:
            continue
            
        # Validate SMILES syntax
        if not is_valid_smiles(smiles):
            invalid_smiles.append(smiles)
            continue
        
        # Parse molecule
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_smiles.append(smiles)
            continue
        
        # Check atom count
        atom_count = mol.GetNumAtoms()
        if atom_count > MAX_ATOMS_THRESHOLD:
            excluded_smiles.append(smiles)
            continue
        
        # Extract features (basic placeholder for now, detailed in T014)
        # Node features: [atom_type, hybridization, formal_charge]
        # Edge features: [bond_type, conjugated, aromatic]
        # For now, we just store the SMILES and atom count
        processed_records.append({
            "smiles": smiles,
            "atom_count": atom_count,
            "raw_record": record
        })
        
    return processed_records, excluded_smiles, invalid_smiles

def is_valid_smiles(smiles: str) -> bool:
    """Check if a SMILES string is valid."""
    return Chem.MolFromSmiles(smiles) is not None

def write_chunk_to_parquet(records: List[Dict[str, Any]], chunk_index: int, output_dir: Path) -> Path:
    """Write a chunk of records to a Parquet file."""
    if not records:
        return None
        
    output_path = output_dir / f"chunk_{chunk_index:04d}.parquet"
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Write to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote {len(records)} records to {output_path}")
    
    return output_path

def process_and_write_chunk(chunk: List[Dict[str, Any]], chunk_index: int, output_dir: Path, checksums: Dict[str, str]) -> Tuple[int, int, int]:
    """
    Process a chunk and write to Parquet.
    
    Returns:
        Tuple of (processed_count, excluded_count, invalid_count).
    """
    processed, excluded, invalid = process_smiles_chunk(chunk)
    
    # Log excluded molecules
    if excluded:
        log_excluded_molecules(len(excluded), excluded)
    
    # Log invalid molecules
    if invalid:
        logger.warning(f"Found {len(invalid)} invalid SMILES strings.")
        # Log errors for invalid SMILES
        log_errors([ValueError(f"Invalid SMILES: {s}") for s in invalid])
    
    # Write to Parquet
    if processed:
        write_chunk_to_parquet(processed, chunk_index, output_dir)
    
    return len(processed), len(excluded), len(invalid)

def main():
    """Main entry point for data ingestion."""
    logger.info("Starting ZINC15 ingestion pipeline...")
    
    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    total_processed = 0
    total_excluded = 0
    total_invalid = 0
    chunk_index = 0
    
    try:
        # Fetch and process stream
        stream = fetch_zinc15_streaming()
        chunk = []
        
        for record in stream:
            chunk.append(record)
            
            if len(chunk) >= CHUNK_SIZE:
                # Process chunk
                p_count, e_count, i_count = process_and_write_chunk(
                    chunk, chunk_index, output_dir, checksums
                )
                total_processed += p_count
                total_excluded += e_count
                total_invalid += i_count
                chunk_index += 1
                chunk = []
                
        # Process remaining items
        if chunk:
            p_count, e_count, i_count = process_and_write_chunk(
                chunk, chunk_index, output_dir, checksums
            )
            total_processed += p_count
            total_excluded += e_count
            total_invalid += i_count
            
    except (ConnectionError, ValueError) as e:
        logger.critical(f"Ingestion failed due to data source error: {e}")
        raise
    
    logger.info(f"Ingestion complete. Processed: {total_processed}, Excluded: {total_excluded}, Invalid: {total_invalid}")
    logger.info("Pipeline finished successfully.")

if __name__ == "__main__":
    main()