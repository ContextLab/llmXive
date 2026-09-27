"""
Dataset Builder for Crystal Structure Prediction Pipeline.

This module handles the assembly of the final dataset from intermediate
processing steps, specifically managing polymorphism by treating unique
(SMILES, Space Group) pairs as distinct samples.
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Tuple
from dataclasses import dataclass, asdict

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_processed_data, get_path_data, ensure_directory
from ingestion.models import MoleculeRecord
from ingestion.fingerprint import generate_ecfp4, smiles_to_mol
from exceptions import MemoryErrorHandled, DownloadError
from logging_config import get_logger, log_event

logger = get_logger(__name__)

@dataclass
class PolymorphicRecord:
    """A record representing a unique polymorphic instance."""
    smiles: str
    space_group: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    alpha: float
    beta: float
    gamma: float
    fingerprint_bits: str  # Comma-separated string of bits
    molecule_id: str
    source_cif_id: str

def load_intermediate_data(batch_size: int = 1000) -> Iterator[Dict[str, Any]]:
    """
    Loads intermediate data from the parsed CIF output.
    Assumes T010 has produced a JSONL or CSV file in data/intermediate/
    containing parsed structures with SMILES and lattice parameters.

    Since T010 produces parsed structures, we look for the output file
    typically named 'parsed_structures.jsonl' or similar in the intermediate dir.
    """
    intermediate_dir = get_path_data("intermediate")
    # Fallback to checking common outputs if specific naming varies
    possible_files = [
        intermediate_dir / "parsed_structures.jsonl",
        intermediate_dir / "parsed_cifs.jsonl",
        intermediate_dir / "structures.jsonl"
    ]
    
    input_file = None
    for p in possible_files:
        if p.exists():
            input_file = p
            break
    
    if not input_file:
        # If T010 hasn't run or output is elsewhere, try to find any .jsonl
        # This is a safeguard for the pipeline flow
        for f in intermediate_dir.glob("*.jsonl"):
            input_file = f
            break

    if not input_file:
        raise FileNotFoundError(
            f"Could not find intermediate parsed structures in {intermediate_dir}. "
            "Ensure T010 (parse_cif.py) has been executed."
        )

    logger.info(f"Loading intermediate data from {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                yield data
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON line: {e}")
                continue

def handle_polymorphism(records: List[Dict[str, Any]]) -> List[PolymorphicRecord]:
    """
    Implements polymorphism handling logic.
    
    Treats each unique (SMILES, Space Group) pair as a distinct row.
    If the same SMILES appears with different Space Groups, they are kept as separate records.
    If the same (SMILES, Space Group) appears multiple times (e.g. multiple crystals),
    we keep the first occurrence or aggregate if necessary (here we keep first unique).
    
    Args:
        records: List of dicts containing 'smiles', 'space_group', and lattice params.
    
    Returns:
        List of PolymorphicRecord objects with unique (SMILES, Space Group) keys.
    """
    seen_keys = set()
    unique_records = []
    duplicates_count = 0

    for record in records:
        smiles = record.get('smiles')
        space_group = record.get('space_group')
        
        if not smiles or not space_group:
            logger.warning(f"Skipping record with missing SMILES or Space Group: {record.get('id', 'unknown')}")
            continue

        key = (smiles, space_group)
        
        if key in seen_keys:
            duplicates_count += 1
            continue
        
        seen_keys.add(key)
        
        # Generate fingerprint for this specific molecule
        try:
            mol = smiles_to_mol(smiles)
            if mol is None:
                logger.warning(f"Could not parse SMILES for fingerprint: {smiles}")
                continue
            
            fp = generate_ecfp4(mol, radius=2, n_bits=2048)
            # Convert RDKit ExplicitBitVector to a string representation
            # RDKit bit vector: getOnBits() returns indices of set bits
            on_bits = fp.GetOnBits()
            fp_str = ','.join(map(str, sorted(on_bits)))
            
        except Exception as e:
            logger.error(f"Error generating fingerprint for {smiles}: {e}")
            continue

        poly_record = PolymorphicRecord(
            smiles=smiles,
            space_group=str(space_group),
            lattice_a=float(record.get('lattice_a', 0.0)),
            lattice_b=float(record.get('lattice_b', 0.0)),
            lattice_c=float(record.get('lattice_c', 0.0)),
            alpha=float(record.get('alpha', 0.0)),
            beta=float(record.get('beta', 0.0)),
            gamma=float(record.get('gamma', 0.0)),
            fingerprint_bits=fp_str,
            molecule_id=record.get('id', hashlib.md5(f"{smiles}{space_group}".encode()).hexdigest()),
            source_cif_id=record.get('cif_id', 'unknown')
        )
        unique_records.append(poly_record)

    logger.info(f"Processed {len(records)} records, found {duplicates_count} duplicate (SMILES, Space Group) pairs.")
    logger.info(f"Total unique polymorphic records: {len(unique_records)}")
    
    return unique_records

def save_dataset(records: List[PolymorphicRecord], output_path: Optional[Path] = None) -> Path:
    """
    Saves the polymorphic dataset to a CSV file.
    
    Args:
        records: List of PolymorphicRecord objects.
        output_path: Optional path to save the file. Defaults to data/processed/polymorphic_dataset.csv.
    
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        processed_dir = get_path_processed_data()
        ensure_directory(processed_dir)
        output_path = processed_dir / "polymorphic_dataset.csv"
    else:
        ensure_directory(output_path.parent)

    logger.info(f"Saving polymorphic dataset to {output_path}")

    if not records:
        logger.warning("No records to save. Creating empty file with headers.")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("molecule_id,smiles,space_group,lattice_a,lattice_b,lattice_c,alpha,beta,gamma,fingerprint_bits,source_cif_id\n")
        return output_path

    # Write CSV header
    headers = [
        "molecule_id", "smiles", "space_group", 
        "lattice_a", "lattice_b", "lattice_c", 
        "alpha", "beta", "gamma", 
        "fingerprint_bits", "source_cif_id"
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(','.join(headers) + '\n')
        for rec in records:
            row = [
                rec.molecule_id,
                rec.smiles,
                rec.space_group,
                f"{rec.lattice_a:.4f}",
                f"{rec.lattice_b:.4f}",
                f"{rec.lattice_c:.4f}",
                f"{rec.alpha:.4f}",
                f"{rec.beta:.4f}",
                f"{rec.gamma:.4f}",
                rec.fingerprint_bits,
                rec.source_cif_id
            ]
            f.write(','.join(row) + '\n')

    logger.info(f"Successfully saved {len(records)} records to {output_path}")
    return output_path

def main():
    """
    Main entry point for the dataset builder task (T012).
    Orchestrates loading intermediate data, handling polymorphism, and saving the result.
    """
    try:
        # 1. Load intermediate data
        logger.info("Starting dataset builder pipeline (T012)...")
        raw_records = list(load_intermediate_data())
        
        if not raw_records:
            logger.error("No intermediate data found. Pipeline cannot proceed.")
            # Create empty output as per spec to avoid breaking downstream if possible,
            # but log critical failure
            save_dataset([])
            return

        # 2. Handle Polymorphism
        unique_records = handle_polymorphism(raw_records)
        
        if not unique_records:
            logger.error("No unique records generated after polymorphism handling.")
            save_dataset([])
            return

        # 3. Save Dataset
        output_path = save_dataset(unique_records)
        
        logger.info("T012 completed successfully.")
        log_event("T012_POLYMORPHISM_HANDLING", {
            "status": "success",
            "input_count": len(raw_records),
            "output_count": len(unique_records),
            "output_path": str(output_path)
        })

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()