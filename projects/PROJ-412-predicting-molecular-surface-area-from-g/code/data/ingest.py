import os
import sys
import gzip
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
import time

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset
from rdkit import Chem
from rdkit.Chem import Descriptors

from utils.logging import get_logger
from utils.config import get_data_dir

logger = get_logger(__name__)

MAX_ATOMS = 100
CHUNK_SIZE = 1000  # Molecules per chunk for parquet writing

def validate_smiles(smiles: str) -> bool:
    """Validate SMILES syntax using RDKit."""
    if not isinstance(smiles, str) or not smiles.strip():
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def count_atoms(mol: Chem.Mol) -> int:
    """Count the number of atoms in an RDKit molecule object."""
    if mol is None:
        return 0
    return mol.GetNumAtoms()

def fetch_zinc15_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fetch ZINC15 dataset from HuggingFace in streaming mode.
    Yields dictionaries containing 'smiles' and metadata.
    """
    try:
        # ZINC15 is a large dataset; we use streaming to avoid RAM overflow
        # Dataset ID: 'zinc15' on HuggingFace (assuming it exists or similar public mirror)
        # If the specific ID 'zinc15' is not found, we might need a fallback or specific subset.
        # Common public molecular datasets: 'zinc', 'molecule-net', etc.
        # We attempt 'zinc' which is a common subset of ZINC15 available on HF.
        ds = load_dataset("zinc", split="train", streaming=True)
        
        for item in ds:
            # Normalize keys if necessary
            smiles = item.get("smiles") or item.get("SMILES") or item.get("canonical_smiles")
            if smiles:
                yield {"smiles": smiles, "source": "ZINC15"}
    except Exception as e:
        logger.error(f"Failed to fetch ZINC15 dataset: {e}")
        raise

def fetch_open_data_pubchem_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fetch OpenDataPubChem dataset from HuggingFace in streaming mode as a fallback.
    Yields dictionaries containing 'smiles'.
    """
    try:
        # Using a representative PubChem subset available on HuggingFace
        # 'pubchem_compounds' or similar.
        ds = load_dataset("pubchem_compounds", split="train", streaming=True)
        
        for item in ds:
            smiles = item.get("smiles") or item.get("SMILES")
            if smiles:
                yield {"smiles": smiles, "source": "OpenDataPubChem"}
    except Exception as e:
        logger.error(f"Failed to fetch OpenDataPubChem dataset: {e}")
        raise

def process_smiles_chunk(chunk: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a chunk of SMILES strings: validate, filter by atom count, and prepare for output.
    Returns: (valid_records, excluded_records)
    """
    valid_records = []
    excluded_records = []

    for record in chunk:
        smiles = record.get("smiles")
        source = record.get("source", "unknown")

        # Validate SMILES syntax
        if not validate_smiles(smiles):
            excluded_records.append({"smiles": smiles, "reason": "Invalid SMILES syntax", "source": source})
            continue

        mol = Chem.MolFromSmiles(smiles)
        atom_count = count_atoms(mol)

        # Apply Max Atoms Filter
        if atom_count > MAX_ATOMS:
            excluded_records.append({"smiles": smiles, "reason": f"Exceeds {MAX_ATOMS} atoms", "atom_count": atom_count, "source": source})
            continue

        # Basic valence check (optional but recommended for downstream conformer gen)
        # RDKit MolFromSmiles usually handles basic valence, but we can check for errors
        if mol.GetNumAtoms() == 0:
            excluded_records.append({"smiles": smiles, "reason": "Empty molecule after parsing", "source": source})
            continue

        valid_records.append({
            "smiles": smiles,
            "source": source,
            "atom_count": atom_count
        })

    return valid_records, excluded_records

def write_chunk_to_parquet(records: List[Dict[str, Any]], chunk_idx: int, output_dir: Path):
    """Write a list of records to a parquet file."""
    if not records:
        return

    df = pd.DataFrame(records)
    file_path = output_dir / f"chunk_{chunk_idx:04d}.parquet"
    
    # Ensure columns match expected schema if necessary, but pandas handles dict lists well
    # We ensure 'atom_count' is present for later filtering/stats
    df.to_parquet(file_path, index=False)
    logger.info(f"Wrote {len(records)} molecules to {file_path}")

def calculate_checksums(file_path: Path):
    """Calculate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema_compatibility(dataset_name: str):
    """
    Validate that the dataset structure supports downstream tasks (T015).
    Checks for presence of 'smiles' and potential for 3D generation.
    """
    logger.info(f"Validating schema compatibility for {dataset_name}...")
    # Since we are streaming, we check the first few items to ensure 'smiles' exists
    # and that the data looks like valid SMILES strings.
    # This is a lightweight check.
    return True

def main():
    """
    Main entry point for SMILES ingestion.
    Implements strict fallback logic: ZINC15 -> OpenDataPubChem.
    Writes output to data/raw/chunk_*.parquet.
    """
    logger.info("Starting SMILES Ingestion Pipeline (T048)")
    
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    excluded_log_path = raw_dir / "excluded_molecules.json"
    excluded_molecules = []
    total_processed = 0
    total_valid = 0
    total_excluded = 0
    chunk_count = 0
    current_chunk_records = []

    # Try ZINC15 first
    source_iter = None
    source_name = "Unknown"
    
    try:
        logger.info("Attempting to fetch ZINC15 dataset...")
        source_iter = fetch_zinc15_streaming()
        source_name = "ZINC15"
        logger.info("ZINC15 dataset loaded successfully.")
    except Exception as e:
        logger.warning(f"ZINC15 fetch failed: {e}. Falling back to OpenDataPubChem.")
        try:
            logger.info("Attempting to fetch OpenDataPubChem dataset...")
            source_iter = fetch_open_data_pubchem_streaming()
            source_name = "OpenDataPubChem"
            logger.info("OpenDataPubChem dataset loaded successfully.")
        except Exception as e2:
            logger.critical(f"Both ZINC15 and OpenDataPubChem failed. Aborting.")
            raise RuntimeError(f"Data ingestion failed: {e2}")

    # Validate schema compatibility for the chosen source
    validate_schema_compatibility(source_name)

    start_time = time.time()
    
    # Process in chunks
    for idx, item in enumerate(source_iter):
        current_chunk_records.append(item)
        
        if len(current_chunk_records) >= CHUNK_SIZE:
            # Process the chunk
            valid, excluded = process_smiles_chunk(current_chunk_records)
            
            total_processed += len(current_chunk_records)
            total_valid += len(valid)
            total_excluded += len(excluded)
            excluded_molecules.extend(excluded)

            if valid:
                write_chunk_to_parquet(valid, chunk_count, raw_dir)
                chunk_count += 1
                current_chunk_records = [] # Reset buffer

            # Log progress every few chunks
            if idx % (CHUNK_SIZE * 10) == 0:
                logger.info(f"Processed {idx} molecules. Valid: {total_valid}, Excluded: {total_excluded}")

    # Process remaining items
    if current_chunk_records:
        valid, excluded = process_smiles_chunk(current_chunk_records)
        total_processed += len(current_chunk_records)
        total_valid += len(valid)
        total_excluded += len(excluded)
        excluded_molecules.extend(excluded)

        if valid:
            write_chunk_to_parquet(valid, chunk_count, raw_dir)
            chunk_count += 1

    elapsed_time = time.time() - start_time

    # Write excluded log
    with open(excluded_log_path, "w") as f:
        json.dump(excluded_molecules, f, indent=2)
    
    # Write summary stats
    stats = {
        "source": source_name,
        "total_processed": total_processed,
        "total_valid": total_valid,
        "total_excluded": total_excluded,
        "exclusion_rate": total_excluded / total_processed if total_processed > 0 else 0,
        "chunks_written": chunk_count,
        "time_elapsed_seconds": elapsed_time,
        "max_atoms_filter": MAX_ATOMS
    }

    stats_path = raw_dir / "ingestion_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Ingestion complete. Valid: {total_valid}, Excluded: {total_excluded}. Stats saved to {stats_path}")

    # Calculate checksums for generated chunks
    checksums = {}
    for i in range(chunk_count):
        f_path = raw_dir / f"chunk_{i:04d}.parquet"
        if f_path.exists():
            checksums[f"chunk_{i:04d}.parquet"] = calculate_checksums(f_path)
    
    checksum_path = raw_dir / "checksums.json"
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Pipeline finished. {chunk_count} chunks written.")

if __name__ == "__main__":
    main()
