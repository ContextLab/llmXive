import os
import sys
import gzip
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
import rdkit
from rdkit import Chem
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset
from tqdm import tqdm

from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir
from data.logging_stats import ExcludedMolecule, DatasetStatistics, log_excluded_molecule, log_dataset_statistics

logger = get_logger(__name__)

MAX_ATOMS = 100
CHUNK_SIZE = 1000
MAX_EXCLUDED_RATIO = 0.5  # Halt if >50% excluded to prevent silent data loss

def validate_smiles(smiles: str) -> Optional[Chem.Mol]:
    """Validate SMILES syntax and return RDKit Mol object or None."""
    if not smiles or not isinstance(smiles, str):
        return None
    mol = Chem.MolFromSmiles(smiles)
    return mol

def count_atoms(mol: Chem.Mol) -> int:
    """Count heavy atoms in a molecule."""
    if mol is None:
        return 0
    return mol.GetNumHeavyAtoms()

def fetch_zinc15_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fetch ZINC15 dataset using HuggingFace datasets streaming.
    Yields dictionaries with 'smiles' key.
    """
    try:
        # ZINC15 is available on HuggingFace datasets
        # Using 'zinc' dataset which is a common proxy for ZINC15
        # If the specific ZINC15 dataset ID changes, this might need adjustment
        dataset = load_dataset("zinc", "default", split="train", streaming=True)
        
        for item in dataset:
            # The dataset might have different field names, adapt accordingly
            if 'smiles' in item:
                yield item
            elif 'smiles_string' in item:
                item['smiles'] = item['smiles_string']
                yield item
            elif 'canonical_smiles' in item:
                item['smiles'] = item['canonical_smiles']
                yield item
            else:
                # Try to find any field that looks like SMILES
                for key, value in item.items():
                    if isinstance(value, str) and len(value) > 5 and value[0] in 'CNOSPFClBr':
                        item['smiles'] = value
                        yield item
                        break
    except Exception as e:
        logger.error(f"Failed to fetch ZINC15: {e}")
        raise

def fetch_open_data_pubchem_streaming() -> Iterator[Dict[str, Any]]:
    """
    Fallback: Fetch from OpenDataPubChem if ZINC15 fails.
    Yields dictionaries with 'smiles' key.
    """
    try:
        # OpenDataPubChem dataset on HuggingFace
        dataset = load_dataset("PubChem", "compound", split="train", streaming=True)
        
        for item in dataset:
            if 'smiles' in item:
                yield item
            elif 'canonical_smiles' in item:
                item['smiles'] = item['canonical_smiles']
                yield item
            else:
                # Try to find SMILES field
                for key, value in item.items():
                    if isinstance(value, str) and len(value) > 5:
                        item['smiles'] = value
                        yield item
                        break
    except Exception as e:
        logger.error(f"Failed to fetch OpenDataPubChem: {e}")
        raise

def process_smiles_chunk(chunk: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[ExcludedMolecule], int]:
    """
    Process a chunk of SMILES data:
    - Validate SMILES
    - Filter by max atoms
    - Return processed DataFrame and exclusion logs
    """
    valid_rows = []
    excluded_molecules = []
    excluded_count = 0
    
    for idx, item in enumerate(chunk):
        smiles = item.get('smiles')
        if not smiles:
            continue
            
        mol = validate_smiles(smiles)
        if mol is None:
            excluded_molecules.append(ExcludedMolecule(
                smiles=smiles,
                reason="Invalid SMILES syntax",
                chunk_id=0
            ))
            excluded_count += 1
            continue
            
        atom_count = count_atoms(mol)
        if atom_count > MAX_ATOMS:
            excluded_molecules.append(ExcludedMolecule(
                smiles=smiles,
                reason=f"Too many atoms ({atom_count} > {MAX_ATOMS})",
                chunk_id=0
            ))
            excluded_count += 1
            continue
            
        valid_rows.append({
            'smiles': smiles,
            'atom_count': atom_count,
            'source': item.get('source', 'unknown')
        })
    
    df = pd.DataFrame(valid_rows)
    return df, excluded_molecules, excluded_count

def write_chunk_to_parquet(df: pd.DataFrame, chunk_idx: int, output_dir: Path):
    """Write a DataFrame chunk to a parquet file."""
    if df.empty:
        logger.warning(f"Chunk {chunk_idx} is empty, skipping write.")
        return
        
    output_path = output_dir / f"chunk_{chunk_idx:04d}.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote {len(df)} molecules to {output_path}")

def calculate_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """Calculate SHA256 checksums for output files."""
    checksums = {}
    for path in file_paths:
        if path.exists():
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            checksums[str(path)] = sha256.hexdigest()
    return checksums

def main(args: Optional[List[str]] = None):
    """Main ingestion pipeline."""
    parser = argparse.ArgumentParser(description="Ingest SMILES from ZINC15 or OpenDataPubChem")
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE, help='Number of molecules per chunk')
    parser.add_argument('--max-excluded-ratio', type=float, default=MAX_EXCLUDED_RATIO, help='Max ratio of excluded molecules before halting')
    parser.add_argument('--source', type=str, default='zinc15', choices=['zinc15', 'pubchem'], help='Data source')
    args = parser.parse_args(args) if args else parser.parse_args()
    
    # Setup paths
    project_root = get_project_root()
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting SMILES ingestion from {args.source}")
    logger.info(f"Max atoms filter: {MAX_ATOMS}")
    logger.info(f"Chunk size: {args.chunk_size}")
    
    # Select data source
    if args.source == 'zinc15':
        data_fetcher = fetch_zinc15_streaming
    else:
        data_fetcher = fetch_open_data_pubchem_streaming
    
    # Process in chunks
    chunk_idx = 0
    current_chunk = []
    total_processed = 0
    total_excluded = 0
    all_excluded = []
    
    try:
        for item in data_fetcher():
            current_chunk.append(item)
            
            if len(current_chunk) >= args.chunk_size:
                # Process chunk
                df, excluded, excluded_count = process_smiles_chunk(current_chunk)
                
                if not df.empty:
                    write_chunk_to_parquet(df, chunk_idx, raw_dir)
                    chunk_idx += 1
                
                total_processed += len(df)
                total_excluded += excluded_count
                all_excluded.extend(excluded)
                
                # Check exclusion ratio
                chunk_total = len(current_chunk)
                if chunk_total > 0:
                    exclusion_ratio = excluded_count / chunk_total
                    if exclusion_ratio > args.max_excluded_ratio:
                        logger.error(f"Exclusion ratio {exclusion_ratio:.2%} exceeds threshold {args.max_excluded_ratio:.2%}. Halting.")
                        raise RuntimeError(f"Too many molecules excluded in chunk {chunk_idx}")
                
                current_chunk = []
                total_processed += 1  # Log progress
                if total_processed % 10000 == 0:
                    logger.info(f"Processed {total_processed} molecules, {total_excluded} excluded")
    
    except StopIteration:
        logger.info("Stream ended normally")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise
    
    # Process remaining items
    if current_chunk:
        df, excluded, excluded_count = process_smiles_chunk(current_chunk)
        if not df.empty:
            write_chunk_to_parquet(df, chunk_idx, raw_dir)
            chunk_idx += 1
        total_processed += len(df)
        total_excluded += excluded_count
        all_excluded.extend(excluded)
    
    # Log statistics
    dataset_stats = DatasetStatistics(
        total_processed=total_processed,
        total_excluded=total_excluded,
        chunks_written=chunk_idx,
        exclusion_ratio=total_excluded / (total_processed + total_excluded) if (total_processed + total_excluded) > 0 else 0
    )
    log_dataset_statistics(dataset_stats, raw_dir)
    
    # Log sample of excluded molecules
    if all_excluded:
        for excl in all_excluded[:10]:  # Log first 10
            log_excluded_molecule(excl, raw_dir)
    
    logger.info(f"Ingestion complete. Processed: {total_processed}, Excluded: {total_excluded}, Chunks: {chunk_idx}")
    
    # Calculate checksums
    output_files = list(raw_dir.glob("chunk_*.parquet"))
    if output_files:
        checksums = calculate_checksums(output_files)
        checksum_file = raw_dir / "checksums.json"
        with open(checksum_file, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Wrote checksums to {checksum_file}")

if __name__ == "__main__":
    main()